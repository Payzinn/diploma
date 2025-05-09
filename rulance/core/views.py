from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count, Q
from .models import Sphere, SphereType, Portfolio, User, OrderFile, Order, Response, Notification, Chat, Message
from .forms import  UserRegisterForm, UserProfileForm, AvatarForm, PortfolioForm, OrderForm, ResponseForm, MessageForm
from django.core.exceptions import PermissionDenied    
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync
from django.core.paginator import Paginator
from channels.layers import get_channel_layer
from .utils import update_profile_tab

def index(request):
    spheres = Sphere.objects.prefetch_related('spheretype_set').all()
    return render(request, 'index.html', {'spheres': spheres})

def freelancers(request):
    spheres      = Sphere.objects.all()
    sphere_types = SphereType.objects.all()
    qs = User.objects.filter(
        role='Freelancer',
        portfolio__isnull=False
    ).select_related('portfolio')

    paginator   = Paginator(qs, 10)
    page_number = request.GET.get('page') or 1
    page_obj    = paginator.get_page(page_number)

    elided_range = paginator.get_elided_page_range(
        number=page_obj.number,
        on_each_side=2,
        on_ends=1,
    )

    params = request.GET.copy()
    params.pop('page', None)
    get_params = params.urlencode()

    return render(request, 'freelancers.html', {
        'freelancers': page_obj,
        'spheres': spheres,
        'sphere_types': sphere_types,
        'page_range': elided_range,
        'get_params': get_params,
    })

def orders(request):
    spheres      = Sphere.objects.all()
    sphere_types = SphereType.objects.all()

    qs = (
        Order.objects
             .filter(status='Open')
             .annotate(responses_count=Count('responses',
                                filter=Q(responses__status='Pending')))
             .select_related('sphere', 'sphere_type', 'client')
    )

    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(title__icontains=search)

    price_min = request.GET.get('price_min')
    if price_min:
        qs = qs.filter(price__gte=price_min)

    price_max = request.GET.get('price_max')
    if price_max:
        qs = qs.filter(price__lte=price_max)

    sphere_id = request.GET.get('sphere')
    if sphere_id:
        qs = qs.filter(sphere_type__sphere_id=sphere_id)

    sphere_types_ids = request.GET.getlist('sphere_types')
    if sphere_types_ids:
        qs = qs.filter(sphere_type_id__in=sphere_types_ids)

    sort = request.GET.get('sort', '')
    if sort == 'no_responses':
        qs = qs.filter(responses_count=0)
    elif sort == 'resp_asc':
        qs = qs.order_by('responses_count')
    elif sort == 'resp_desc':
        qs = qs.order_by('-responses_count')
    elif sort == 'date_asc':
        qs = qs.order_by('created_at')
    elif sort == 'date_desc':
        qs = qs.order_by('-created_at')
    else:
        qs = qs.order_by('-created_at')

    paginator   = Paginator(qs, 10)
    page_number = request.GET.get('page') or 1
    page_obj    = paginator.get_page(page_number)

    elided_range = paginator.get_elided_page_range(
        number=page_obj.number,
        on_each_side=2,
        on_ends=1,
    )

    params = request.GET.copy()
    params.pop('page', None)
    get_params = params.urlencode()

    return render(request, 'orders.html', {
        'orders': page_obj,
        'spheres': spheres,
        'sphere_types': sphere_types,
        'filter': {
            'search': search,
            'price_min': price_min or '',
            'price_max': price_max or '',
            'sphere_id': sphere_id or '',
            'sphere_types_ids': list(map(int, sphere_types_ids)) if sphere_types_ids else [],
            'sort': sort,
        },
        'page_range': elided_range,
        'get_params': get_params,
    })

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def switch_role(request):
    u = request.user
    u.role = 'Client' if u.role == 'Freelancer' else 'Freelancer'
    u.save()
    return redirect('index')


def profile(request, pk=None):
    if pk:
        profile_user = get_object_or_404(User, pk=pk)
    else:
        profile_user = request.user

    is_own = request.user.is_authenticated and (profile_user == request.user)

    has_portfolio = hasattr(profile_user, 'portfolio')

    if request.method == 'POST' and is_own:
        avatar_form = AvatarForm(request.POST, request.FILES, instance=request.user)
        if avatar_form.is_valid():
            avatar_form.save()
            return JsonResponse({'success': True, 'avatar_url': request.user.avatar.url})
        else:
            return JsonResponse({'success': False, 'errors': avatar_form.errors}, status=400)
        
    context = {
        'profile_user': profile_user,
        'is_own': is_own,
        'has_portfolio': has_portfolio,
    }

    client_orders = []
    if profile_user.role == 'Client':
        qs = (
            Order.objects
                 .filter(client=profile_user)
                 .annotate(
                     responses_count=Count(
                         'responses',
                         filter=Q(responses__status='Pending')
                     )
                 )
                 .select_related('sphere', 'sphere_type')
        )
        if request.user.is_authenticated and not is_own and request.user.role == 'Freelancer':
            my_resps = Response.objects.filter(
                order__client=profile_user,
                user=request.user
            )
            resp_map = {r.order_id: r for r in my_resps}
            for o in qs:
                o.user_response = resp_map.get(o.pk)
                client_orders.append(o)
        else:
            client_orders = list(qs)

    context['client_orders'] = client_orders

    if is_own:
        if profile_user.role == 'Client':
            tab_label = 'Отклики исполнителей'
            pending = Response.objects.filter(
                order__client=profile_user,
                status='Pending'
            ).select_related('order', 'user').prefetch_related('order__sphere', 'order__sphere_type')
            in_work = Response.objects.filter(
                order__client=profile_user,
                status='Accepted',
                order__status='InWork'
            ).select_related('order', 'user').prefetch_related('order__sphere', 'order__sphere_type')
            completed = Order.objects.filter(
                client=profile_user,
                status='Completed'
            ).select_related('sphere', 'sphere_type').prefetch_related('responses')
            cancelled = Order.objects.filter(
                client=profile_user,
                status='Cancelled'
            ).select_related('sphere', 'sphere_type').prefetch_related('responses')
        else:
            tab_label = 'Мои отклики'
            pending = Response.objects.filter(
                user=profile_user,
                status='Pending'
            ).select_related('order', 'order__client').prefetch_related('order__sphere', 'order__sphere_type')
            in_work = Response.objects.filter(
                user=profile_user,
                status='Accepted',
                order__status='InWork'
            ).select_related('order', 'order__client').prefetch_related('order__sphere', 'order__sphere_type')
            completed = Response.objects.filter(
                user=profile_user,
                status='Accepted',
                order__status='Completed'
            ).select_related('order', 'order__client').prefetch_related('order__sphere', 'order__sphere_type')
            cancelled = Order.objects.filter(
                responses__user=profile_user,
                responses__status='Accepted',
                status='Cancelled'
            ).select_related('sphere', 'sphere_type').prefetch_related('responses')

        resp_list = list(in_work) + list(completed)
        order_ids = [r.order_id if isinstance(r, Response) else r.pk for r in resp_list]

        if profile_user.role == 'Client':
            chats = Chat.objects.filter(
                order__client=profile_user,
                freelancer__in=[r.user for r in in_work]
            )
            chat_map = {(c.order_id, c.freelancer_id): c for c in chats}
            for r in resp_list:
                if isinstance(r, Response):
                    r.chat = chat_map.get((r.order_id, r.user_id))
                else:
                    r.chat = None
        else:
            chats = Chat.objects.filter(
                freelancer=profile_user,
                order_id__in=order_ids
            )
            chat_map = {c.order_id: c for c in chats}
            for r in resp_list:
                r.chat = chat_map.get(r.order_id if isinstance(r, Response) else r.pk)

        default_tab = 'orders' if profile_user.role == 'Client' else 'pending'
        current_tab = request.GET.get('tab', default_tab)
        if current_tab not in ('orders', 'pending', 'in_work', 'completed', 'cancelled'):
            current_tab = default_tab

        context.update({
            'tab_label': tab_label,
            'pending': pending,
            'in_work': in_work,
            'completed': completed,
            'cancelled': cancelled,
            'current_tab': current_tab,
        })

    return render(request, 'profile.html', context)

@login_required
def response_reject(request, pk):
    resp = get_object_or_404(Response, pk=pk, order__client=request.user)
    resp.status = 'Rejected'
    resp.save()
    return redirect(reverse('profile'))

@login_required
def portfolio_create(request):
    """
    Создание портфолио. Если уже есть — редиректим в профиль.
    """
    if hasattr(request.user, 'portfolio'):
        return redirect('profile')

    if request.method == 'POST':
        form = PortfolioForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.user = request.user
            p.sphere = p.sphere_type.sphere
            p.save()
            return redirect('profile')
    else:
        form = PortfolioForm()

    spheres = Sphere.objects.prefetch_related('spheretype_set').all()
    return render(request, 'portfolio_create.html', {
        'form': form,
        'spheres': spheres,
        'is_update': False,
    })

def portfolio_detail(request, pk):
    profile_user = get_object_or_404(User, pk=pk, role='Freelancer')
    if request.user.is_authenticated and request.user.pk == profile_user.pk:
        is_own = True
    else:
        is_own = False

    portfolio = profile_user.portfolio

    return render(request, 'portfolio_detail.html', {
        'portfolio': portfolio,
        'profile_user': profile_user,
        'is_own': is_own,
    })

@login_required
def portfolio_update(request):
    """
    Редактирование портфолио. Если нет — 403 Forbidden.
    """
    if not hasattr(request.user, 'portfolio'):
        raise PermissionDenied

    p = request.user.portfolio
    if request.method == 'POST':
        form = PortfolioForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            return redirect('portfolio_detail')
    else:
        form = PortfolioForm(instance=p)

    spheres = Sphere.objects.prefetch_related('spheretype_set').all()
    return render(request, 'portfolio_create.html', {
        'form': form,
        'spheres': spheres,
        'is_update': True,
    })

@login_required
def make_order(request):
    spheres = Sphere.objects.prefetch_related('spheretype_set').all()

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.client = request.user
            order.sphere = order.sphere_type.sphere
            order.save()
            for f in request.FILES.getlist('files'):
                OrderFile.objects.create(order=order, file=f)
            # Обновляем вкладку "orders" для клиента
            count = Order.objects.filter(client=request.user).count()
            update_profile_tab(request.user, 'orders', count)
            return redirect(reverse('make_order') + '?status=success')
    else:
        form = OrderForm()

    return render(request, "make_order.html", {
        'form': form,
        'spheres': spheres,
    })

def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects
             .select_related('sphere','sphere_type','client')
             .prefetch_related('files','responses__user'),
        pk=pk
    )

    if request.user.is_authenticated:
        has_portfolio = hasattr(request.user, 'portfolio')
        has_responded = order.responses.filter(user=request.user).exists()
        response_form = ResponseForm()
    else:
        has_portfolio = False
        has_responded = False
        response_form = None

    return render(request, 'order_detail.html', {
        'order': order,
        'has_portfolio': has_portfolio,
        'has_responded': has_responded,
        'response_form': response_form,
    })

@login_required
def order_respond(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if request.user.role != 'Freelancer':
        return redirect(reverse('order_detail', args=[order.pk]) + '?error=not_freelancer')
    
    if not hasattr(request.user, 'portfolio'):
        return redirect(reverse('order_detail', args=[order.pk]) + '?no_portfolio=1')
    
    if Response.objects.filter(order=order, user=request.user).exists():
        return redirect(reverse('order_detail', args=[order.pk]) + '?already=1')
    
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.order = order
            response.user = request.user
            response.status = 'Pending'
            response.save()
            freelancer_count = Response.objects.filter(user=request.user, status='Pending').count()
            update_profile_tab(request.user, 'pending', freelancer_count)
            client_count = Response.objects.filter(order__client=order.client, status='Pending').count()
            update_profile_tab(order.client, 'pending', client_count)
            return redirect(reverse('order_detail', args=[order.pk]) + '?responded=1')
    else:
        form = ResponseForm()
    
    return render(request, 'order_detail.html', {
        'order': order,
        'response_form': form,
    })

@login_required
def response_detail(request, pk):
    resp = get_object_or_404(
        Response.objects
            .select_related('order__client', 'user'),
        pk=pk
    )
    if not (
        request.user == resp.order.client 
        or request.user == resp.user
    ):
        raise PermissionDenied

    return render(request, 'response_detail.html', {
        'resp': resp
    })

@login_required
def response_accept(request, response_id):
    response = get_object_or_404(Response, pk=response_id)
    if request.user != response.order.client:
        return redirect('order_detail', response.order.pk)
    
    response.status = 'Accepted'
    response.order.status = 'InWork'
    response.save()
    response.order.save()
    
    # Создаем чат
    chat, created = Chat.objects.get_or_create(
        order=response.order,
        client=response.order.client,
        freelancer=response.user,
        defaults={'is_active': True}
    )
    
    # Обновляем вкладки
    client_pending_count = Response.objects.filter(order__client=response.order.client, status='Pending').count()
    client_in_work_count = Response.objects.filter(order__client=response.order.client, status='Accepted', order__status='InWork').count()
    update_profile_tab(response.order.client, 'pending', client_pending_count)
    update_profile_tab(response.order.client, 'in_work', client_in_work_count)
    
    freelancer_pending_count = Response.objects.filter(user=response.user, status='Pending').count()
    freelancer_in_work_count = Response.objects.filter(user=response.user, status='Accepted', order__status='InWork').count()
    update_profile_tab(response.user, 'pending', freelancer_pending_count)
    update_profile_tab(response.user, 'in_work', freelancer_in_work_count)
    
    return redirect('order_detail', response.order.pk)

@login_required
def response_reject(request, pk):
    resp = get_object_or_404(Response, pk=pk, order__client=request.user)
    resp.status = 'Rejected'
    resp.save()

    verb = f'Ваш отклик на «{resp.order.title}» отклонён.'
    link = reverse('response_detail', args=[resp.pk])
    note = Notification.objects.create(user=resp.user, verb=verb, link=link)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{resp.user.id}',
        {
            'type': 'notif_message',
            'data': {
                'id': note.id,
                'verb': note.verb,
                'link': note.get_absolute_url(),
                'created_at': note.created_at.strftime('%d.%m.%Y %H:%M'),
            }
        }
    )

    return redirect('profile')

@login_required
def notifications_list(request):
    qs = request.user.notifications.all()
    qs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications_list.html', {'notifications': qs})


@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, pk=chat_id)
    if request.user not in (chat.client, chat.freelancer):
        raise PermissionDenied

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.chat = chat
            msg.sender = request.user
            msg.save()
            other = chat.freelancer if request.user == chat.client else chat.client
            verb = f'Новое сообщение в чате по заказу «{chat.order.title}»'
            link = reverse('chat_detail', args=[chat.pk])
            note = Notification.objects.create(user=other, verb=verb, link=link)

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{other.id}',
                {
                    'type': 'notif_message',
                    'data': {
                        'id': note.id,
                        'verb': note.verb,
                        'link': note.get_absolute_url(),
                        'created_at': note.created_at.strftime('%d.%m.%Y %H:%M'),
                    }
                }
            )

            return redirect('chat_detail', chat_id=chat.pk)
    else:
        form = MessageForm()

    return render(request, 'chat_detail.html', {
        'chat': chat,
        'messages': chat.messages.select_related('sender').all(),
        'form': form,
    })

@login_required
def order_complete(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.user != order.client:
        return redirect('order_detail', order.pk)
    
    return redirect('chat_detail', chat_id=Chat.objects.get(order=order, client=order.client).pk)

@login_required
def order_cancel(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.user != order.client:
        return redirect('order_detail', order.pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        order.status = 'Cancelled'
        order.reason_of_cancel = reason
        order.save()
        
        chat = Chat.objects.filter(order=order, client=order.client).first()
        if chat:
            chat.is_active = False
            chat.save()
        
        client_count = Order.objects.filter(client=order.client, status='Cancelled').count()
        update_profile_tab(order.client, 'cancelled', client_count)
        
        response = Response.objects.filter(order=order, status='Accepted').first()
        if response:
            freelancer_count = Order.objects.filter(
                responses__user=response.user, responses__status='Accepted', status='Cancelled'
            ).count()
            update_profile_tab(response.user, 'cancelled', freelancer_count)
        
        return redirect('order_detail', order.pk)
    
    return render(request, 'order_cancel.html', {'order': order})

@require_POST
@login_required
def mark_notification_read(request, id):
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'ok'})

@require_POST
def delete_notification(request, id):
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.delete()
    return JsonResponse({'status': 'ok'})