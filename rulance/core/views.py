from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count, Q
from .models import Sphere, SphereType, Portfolio, User, OrderFile, Order, Response
from .forms import  UserRegisterForm, UserProfileForm, AvatarForm, PortfolioForm, OrderForm, ResponseForm
from django.core.exceptions import PermissionDenied    


def index(request):
    spheres = Sphere.objects.prefetch_related('spheretype_set').all()
    return render(request, 'index.html', {'spheres': spheres})

def orders(request):
    spheres       = Sphere.objects.all()
    sphere_types  = SphereType.objects.all()

    qs = Order.objects.filter(status='Открыт') \
                      .annotate(responses_count=Count('responses'))

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

    qs = qs.select_related('sphere','sphere_type','client')

    return render(request, 'orders.html', {
        'orders': qs,
        'spheres': spheres,
        'sphere_types': sphere_types,
        'filter': {
            'search': search,
            'price_min': price_min or '',
            'price_max': price_max or '',
            'sphere_id': sphere_id or '',
            'sphere_types_ids': list(map(int, sphere_types_ids)) if sphere_types_ids else [],
            'sort': sort,
        }
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

@login_required
def profile(request, pk=None):
    # 1) Определяем, чей профиль
    if pk:
        profile_user = get_object_or_404(User, pk=pk)
    else:
        profile_user = request.user

    is_own = (profile_user == request.user)
    has_portfolio = hasattr(profile_user, 'portfolio')

    context = {
        'profile_user': profile_user,
        'is_own':       is_own,
        'has_portfolio': has_portfolio,
    }

    # 2) Если у профиля — Клиент, готовим список его заказов
    if profile_user.role == 'Client':
        qs = (
            Order.objects
                 .filter(client=profile_user)
                 .annotate(responses_count=Count('responses'))
                 .select_related('sphere', 'sphere_type')
        )
        # Если мы зашли НЕ в свой профиль и мы — Фрилансер, 
        # нужно отметить, где у нас уже есть отклик:
        if not is_own and request.user.role == 'Freelancer':
            my_resps = Response.objects.filter(
                order__client=profile_user,
                user=request.user
            )
            resp_map = {r.order_id: r for r in my_resps}
            client_orders = []
            for o in qs:
                o.user_response = resp_map.get(o.pk)
                client_orders.append(o)
        else:
            client_orders = list(qs)

        context['client_orders'] = client_orders

    # 3) Если это мой профиль, собираем отклики и табы
    if is_own:
        if profile_user.role == 'Client':
            all_resps = Response.objects.filter(order__client=profile_user)
            tab_label = 'Отклики исполнителей'
        else:
            all_resps = Response.objects.filter(user=profile_user)
            tab_label = 'Мои отклики'

        pending   = all_resps.filter(status='Pending')
        in_work   = all_resps.filter(status='Accepted')
        completed = all_resps.filter(status='Rejected')

        # по умолчанию для Клиента открывать «orders», для Фрилансера — «pending»
        default_tab = 'orders' if profile_user.role == 'Client' else 'pending'
        current_tab = request.GET.get('tab', default_tab)
        valid_tabs = ['orders', 'pending', 'in_work', 'completed']
        if current_tab not in valid_tabs:
            current_tab = default_tab

        context.update({
            'pending':     pending,
            'in_work':     in_work,
            'completed':   completed,
            'current_tab': current_tab,
            'tab_label':   tab_label,
        })

    return render(request, 'profile.html', context)

@login_required
def response_accept(request, pk):
    resp = get_object_or_404(Response, pk=pk, order__client=request.user)
    resp.status = 'Accepted'
    resp.save()
    order = resp.order
    order.status = 'В работе'
    order.save()
    return redirect(reverse('profile'))

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

@login_required
def portfolio_detail(request):
    """
    Просмотр своего портфолио.
    """
    p = get_object_or_404(Portfolio, user=request.user)
    return render(request, 'portfolio_detail.html', {'portfolio': p})

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
            return redirect(reverse('make_order') + '?status=success')
    else:
        form = OrderForm()

    return render(request, "make_order.html", {
        'form': form,
        'spheres': spheres,
    })


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects
             .select_related('sphere','sphere_type','client')
             .prefetch_related('files','responses__user'),
        pk=pk
    )

    has_portfolio = hasattr(request.user, 'portfolio')
    has_responded = order.responses.filter(user=request.user).exists()

    return render(request, 'order_detail.html', {
        'order': order,
        'has_portfolio': has_portfolio,
        'has_responded': has_responded,
        'response_form': ResponseForm(),
    })

@login_required
def order_respond(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.user.role != 'Freelancer':
        return redirect('order_detail', pk=pk)
    if not hasattr(request.user, 'portfolio'):
        return redirect(reverse('order_detail', args=[pk]) + '?no_portfolio=1')
    if order.responses.filter(user=request.user).exists():
        return redirect(reverse('order_detail', args=[pk]) + '?already=1')

    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            resp = form.save(commit=False)
            resp.order = order
            resp.user = request.user
            resp.save()
            return redirect(reverse('order_detail', args=[pk]) + '?responded=1')
    return redirect('order_detail', pk=pk)

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