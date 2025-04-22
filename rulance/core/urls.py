from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('orders/', views.orders, name='orders'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='login.html', success_url='/profile/'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('switch-role/', views.switch_role, name='switch_role'),
    path('profile/', views.profile, name='profile'),
    
]