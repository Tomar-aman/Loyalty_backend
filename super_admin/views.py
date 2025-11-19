from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.contrib.auth import get_user_model
from django.contrib import messages
from config.utils import send_mail
from django.contrib.auth import update_session_auth_hash
from django.core.mail import get_connection, EmailMessage

from settings.models import SMTPSettings
from django.core.paginator import Paginator
from django.db import models


def is_admin(user):
    return user.is_superuser or user.is_superadmin

class CustomAdminLoginView(View):

    def get(self, request):
        if request.user.is_authenticated and is_admin(request.user):
            return redirect('admin_panel:dashboard')
        next_url = request.GET.get('next','')
        return render(request, 'custom-admin/services/login.html',{'next_url':next_url})

    def post(self, request):
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None and is_admin(user):
            login(request, user)
            next_url = request.POST.get('next','')
            if next_url:
                return redirect(next_url)
            return redirect('admin_panel:dashboard')
        messages.error(request, 'Invalid credentials')
        return render(request, 'custom-admin/services/login.html')
  
@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class CustomAdminDashboardView(TemplateView):
    template_name = 'custom-admin/services/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dashboard'
        return context

class CustomAdminLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('admin_panel:login')
  
@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class AdminProfileView(View):
    def get(self, request):
        smtp_settings = SMTPSettings.objects.first()
        context = {
            'title': 'Update Profile',
            'user': request.user,
            'smtp_settings': smtp_settings,
        }
        return render(request, 'custom-admin/services/profile.html', context)

    def post(self, request):
        user = request.user
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            try:
                user.profile_picture = request.FILES['profile_picture']
                user.save()
                messages.success(request, 'Profile picture updated successfully')
            except Exception as e:
                messages.error(request, f'Error updating profile picture: {str(e)}')
            return redirect('admin_panel:profile')
        
        # Handle other profile updates
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
    
        try:
            user.first_name = first_name
            user.last_name = last_name
            user.phone_number = phone_number
            user.save()
            messages.success(request, 'Profile updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
        return redirect('admin_panel:profile')


@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class ChangePasswordView(View):
    def get(self, request):
        return render(request, 'custom-admin/services/change-password.html', {'title': 'Change Password'})

    def post(self, request):
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect')
            return redirect('admin_panel:change_password')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('admin_panel:change_password')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return redirect('admin_panel:change_password')

        try:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            messages.success(request, 'Password changed successfully')
            return redirect('admin_panel:profile')
        except Exception as e:
            messages.error(request, 'Error changing password')
            return redirect('admin_panel:change_password')


@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class UserListView(TemplateView):
    template_name = 'custom-admin/services/manage-user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        
        # Get search query from request
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        users = User.objects.filter(is_temp=False, is_superadmin=False, is_admin=False)
        if search_query:
            users = users.filter(
                models.Q(email__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query) |
                models.Q(phone_number__icontains=search_query)
            )
        users = users.order_by('-date_joined')
        paginator = Paginator(users, 25)  
        users_page = paginator.get_page(page)


        context['users'] = users_page
        context['search_query'] = search_query
        context['title'] = 'User Management'
        return context
  
@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class UserToggleStatusView(View):
    def post(self, request, user_id):
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()
            status = 'activated' if user.is_active else 'deactivated'
            messages.success(request, f'User {user.email} has been {status}')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        return redirect('admin_panel:manage_users')

@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class UserDeleteView(View):
    def post(self, request, user_id):
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            messages.success(request, f'User {user.email} has been deleted')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        return redirect('admin_panel:manage_users')


@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class UserEditView(View):
    def post(self, request):
        User = get_user_model()
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email').lower()
            user.phone_number = request.POST.get('phone_number')

            
            user.is_active = request.POST.get('is_active') == 'true'
            user.save()
            messages.success(request, f'User {user.email} has been updated successfully')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
        return redirect('admin_panel:manage_users')