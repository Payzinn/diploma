from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserProfileForm, AvatarForm
from .models import *

def index(request):
    spheres = Sphere.objects.prefetch_related('spheretype_set').all()
    return render(request, 'index.html', {'spheres': spheres})

def orders(request):
    return render(request, 'orders.html', {})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def switch_role(request):
    user = request.user
    user.role = 'Client' if user.role == 'Freelancer' else 'Freelancer'
    user.save()
    return redirect('/')

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = AvatarForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponse("OK")  
    else:
        form = AvatarForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})