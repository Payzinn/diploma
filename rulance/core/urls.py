from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.index, name='index'),
    path('orders/', views.orders, name='orders'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='login.html', success_url='/profile/'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('switch-role/', views.switch_role, name='switch_role'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:pk>/', views.profile, name='profile_detail'),
    path('portfolio/create/', views.portfolio_create, name='portfolio_create'),
    path('portfolio/', views.portfolio_detail, name='portfolio_detail'),
    path('portfolio/edit/', views.portfolio_update, name='portfolio_update'),
    path('make_order/', views.make_order, name='make_order'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/respond/', views.order_respond, name='order_respond'),
    path('response/<int:pk>/accept/', views.response_accept, name='response_accept'),
    path('response/<int:pk>/reject/',  views.response_reject,  name='response_reject'),
    path('responses/<int:pk>/', views.response_detail, name='response_detail'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('order/<int:pk>/complete/', views.order_complete, name='order_complete'),
    path('order/<int:pk>/cancel/',   views.order_cancel,   name='order_cancel'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)