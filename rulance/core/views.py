from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .models import Sphere, SphereType, Portfolio, User, OrderFile, Order
from .forms import (
    UserRegisterForm,
    UserProfileForm,
    AvatarForm,
    PortfolioForm,
    OrderForm,
    
)

def index(request):
    spheres = Sphere.objects.prefetch_related('spheretype_set').all()
    return render(request, 'index.html', {'spheres': spheres})

def orders(request):
    spheres       = Sphere.objects.all()
    sphere_types  = SphereType.objects.all()
    qs            = Order.objects.filter(status='Открыт')
    
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
    
    qs = qs.select_related('sphere', 'sphere_type', 'client') \
           .order_by('-created_at')
    
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
def profile(request):
    """
    Аватар: меняем через AJAX (AvatarForm) — возвращает простой HttpResponse.
    has_portfolio: флаг, чтобы отрисовать кнопку создания/редактирования.
    """
    if request.method == 'POST':
        form = AvatarForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponse("OK")
        return HttpResponse(status=400)

    form = AvatarForm(instance=request.user)
    has_portfolio = hasattr(request.user, 'portfolio')
    return render(request, 'profile.html', {
        'form': form,
        'has_portfolio': has_portfolio,
    })

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
             .prefetch_related('files'),  
        pk=pk
    )
    return render(request, 'order_detail.html', {
        'order': order,
    })
