from django.urls import path
from . import views
urlpatterns = [
    path('cadastro/', views.register_view, name='register'),
    path('activate/<uidb64>/<token>/', views.activate_view, name='activate'),
    path('login/', views.login_view, name='login'),
    path('activation-success/', views.activation_success, name='activation_success'),
    path('', views.home_view, name='home'),
    path('resend-activation-email/', views.resend_activation_email, name='resend_activation_email'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.request_password_reset, name='password_reset'),
    path('reset/<uuid:token>/', views.reset_password, name='reset_password'),
    path('meu-perfil/', views.my_profile, name='my_profile'),
    path('perfil/<str:username>/', views.profile_view, name='profile_view'),
    path('perfil/editar/', views.profile_edit, name='profile_edit'),
]