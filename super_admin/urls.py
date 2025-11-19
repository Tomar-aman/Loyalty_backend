from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.CustomAdminLoginView.as_view(), name='login'),
    path('dashboard/', views.CustomAdminDashboardView.as_view(), name='dashboard'),
    path('logout/', views.CustomAdminLogoutView.as_view(), name='logout'),
    path('profile/', views.AdminProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('users/', views.UserListView.as_view(), name='manage_users'),
    path('users/<int:user_id>/toggle/', views.UserToggleStatusView.as_view(), name='user_toggle'),
    path('users/<int:user_id>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/edit/', views.UserEditView.as_view(), name='user_edit'),
]