from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.contrib.auth import get_user_model
from django.contrib import messages
from config.utils import send_mail
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.core.mail import get_connection, EmailMessage
from django.db.models import Q
from settings.models import SMTPSettings, StipeKeySettings, GoogleMapsSettings, FirebaseSettings
from django.core.paginator import Paginator
from django.db import models
from notification.models import Notification
from notification.utils import send_push_to_user
from card.models import Card, CardBenefit , UserCard, UserCardHistory
from django.http import JsonResponse
import json
import datetime
from django.utils import timezone
from news.models import NewsArticle
from django.core.files.storage import default_storage
from business.models import Business, BusinessCategory, BusinessImage, BusinessOffer
from users.models import User, City, Country
from contact_us.models import Support, FAQ, ContactUsMessage, SubsciberEmail, Address, APPDownloadLink, SocialMediaLink, LandingPageContent
from django.views.generic import TemplateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models

def is_superadmin(user):
    """Check if user is a superadmin"""
    return user.is_superuser or user.is_superadmin

def is_admin(user):
    return user.is_authenticated and (user.is_superadmin or user.is_admin)

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
        from django.db.models import F
        import calendar
        from collections import defaultdict
        from datetime import datetime

        context = super().get_context_data(**kwargs)
        context['title'] = 'Dashboard'

        # User stats
        try:
            total_users = User.objects.filter(is_superadmin=False).count()
            active_users = User.objects.filter(is_superadmin=False, is_active=True).count()

            # Subscription and paid/free breakdown via UserCard
            total_subscriptions = UserCard.objects.count()
            paid_users = UserCard.objects.filter(is_active=True).values('user_id').distinct().count()
            free_users = max(total_users - paid_users, 0)

            context.update({
                'total_users': total_users,
                'active_users': active_users,
                'total_subscriptions': total_subscriptions,
                'paid_users': paid_users,
                'free_users': free_users,
            })
        except Exception:
            # Fail-safe defaults
            context.update({
                'total_users': 0,
                'active_users': 0,
                'total_subscriptions': 0,
                'paid_users': 0,
                'free_users': 0,
            })

        # Monthly revenue (current month) from UserCardHistory purchase/renew
        try:
            now = timezone.now()
            year = now.year
            month = now.month
            days_in_month = calendar.monthrange(year, month)[1]

            # Filter histories for current month
            histories = (
                UserCardHistory.objects
                .filter(action__in=['purchase', 'renew'], start_at__year=year, start_at__month=month)
                .select_related('card')
                .annotate(amount=F('card__price'))
            )

            # Aggregate per day
            daily_totals = defaultdict(float)
            monthly_total = 0.0
            for h in histories:
                day_key = h.start_at.date()
                amt = float(h.amount) if h.amount is not None else 0.0
                daily_totals[day_key] += amt
                monthly_total += amt

            labels = []
            data = []
            for day in range(1, days_in_month + 1):
                date_obj = datetime(year, month, day)
                labels.append(date_obj.strftime('%d %b'))
                data.append(round(daily_totals.get(date_obj.date(), 0.0), 2))

            context.update({
                'labels': labels,
                'data': data,
                'monthly_total': round(monthly_total, 2),
                'total_revenue': f"${round(monthly_total, 2):.2f}",
            })
        except Exception:
            context.update({
                'labels': [],
                'data': [],
                'monthly_total': 0.0,
                'total_revenue': "$0.00",
            })

        return context

class CustomAdminLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('admin_panel:login')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class ManageNotificationsView(TemplateView):
    template_name = 'custom-admin/services/manage-notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Send Notifications'

        # Filters
        search_query = self.request.GET.get('search', '').strip()
        city_id = self.request.GET.get('city_id')
        page = self.request.GET.get('page', 1)

        users_qs = User.objects.filter(is_superadmin=False).order_by('-date_joined')
        if city_id:
            users_qs = users_qs.filter(city_id=city_id)
        if search_query:
            users_qs = users_qs.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )

        paginator = Paginator(users_qs, 25)
        users_page = paginator.get_page(page)

        context['cities'] = City.objects.all().order_by('name')
        context['users_page'] = users_page
        context['search_query'] = search_query
        context['selected_city_id'] = city_id
        return context

    def post(self, request):
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        mode = request.POST.get('mode', 'selected_users')  # 'selected_users' | 'cities' | 'all'
        city_ids = request.POST.getlist('city_ids')
        user_ids = request.POST.getlist('user_ids')

        if not title or not message:
            messages.error(request, 'Title and message are required.')
            return redirect('admin_panel:manage_notifications')

        try:
            # Build recipient queryset based on mode
            if mode == 'all':
                recipients = User.objects.filter(is_superadmin=False)
            elif mode == 'cities':
                if not city_ids:
                    messages.error(request, 'Please select at least one city.')
                    return redirect('admin_panel:manage_notifications')
                recipients = User.objects.filter(is_superadmin=False, city_id__in=city_ids)
            else:  # selected_users
                if not user_ids:
                    messages.error(request, 'Please select at least one user.')
                    return redirect('admin_panel:manage_notifications')
                recipients = User.objects.filter(pk__in=user_ids, is_superadmin=False)

            created_count = 0
            pushed_count = 0
            for u in recipients.only('id', 'device_token'):
                Notification.objects.create(user=u, title=title, message=message)
                unread_count = Notification.objects.filter(user=u, is_read=False).count()
                created_count += 1
                if u.device_token:
                    try:
                        send_push_to_user(u.id, title, message, data={'type': 'admin_broadcast', 'unread_count': str(unread_count)})
                        pushed_count += 1
                        print("Push sent to user:", u.id)
                    except Exception:
                        print("Failed to send push to user:", u.id)
                        # Fail silently for push but keep record
                        pass

            messages.success(request, f'Notification created for {created_count} users. Push sent to {pushed_count}.')
        except Exception as e:
            messages.error(request, f'Failed to send notifications: {str(e)}')

        return redirect('admin_panel:manage_notifications')
  
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
class UpdateSMTPSettingsView(View):
    def post(self, request):
        host = request.POST.get('smtp_host')
        port = request.POST.get('smtp_port')
        username = request.POST.get('smtp_username')
        password = request.POST.get('smtp_password')
        from_email = request.POST.get('from_email')
        use_tls = request.POST.get('use_tls') == 'on'
        
        try:
            smtp_settings, created = SMTPSettings.objects.get_or_create(id=1)
            smtp_settings.host = host
            smtp_settings.port = port
            smtp_settings.username = username
            smtp_settings.password = password
            smtp_settings.from_email = from_email
            smtp_settings.use_tls = use_tls
            smtp_settings.save()
            messages.success(request, 'SMTP settings updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating SMTP settings: {str(e)}')
        
        return redirect('admin_panel:manage_api_settings')

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


class ResetPasswordView(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model().objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token):
                return render(request, 'custom-admin/services/reset-password.html', {
                    'uidb64': uidb64,
                    'token': token
                })
            else:
                messages.error(request, 'Password reset link is invalid or has expired.')
                return redirect('admin_panel:login')
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            messages.error(request, 'Password reset link is invalid.')
            return redirect('admin_panel:login')

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model().objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token):
                password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')
                
                if password != confirm_password:
                    messages.error(request, 'Passwords do not match.')
                    return render(request, 'custom-admin/services/reset-password.html', {
                        'uidb64': uidb64,
                        'token': token
                    })
                
                if len(password) < 8:
                    messages.error(request, 'Password must be at least 8 characters long.')
                    return render(request, 'custom-admin/services/reset-password.html', {
                        'uidb64': uidb64,
                        'token': token
                    })
                
                user.set_password(password)
                user.save()
                messages.success(request, 'Password has been reset successfully.')
                return redirect('admin_panel:login')
            else:
                messages.error(request, 'Password reset link is invalid or has expired.')
                return redirect('admin_panel:login')
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            messages.error(request, 'Password reset link is invalid.')
            return redirect('admin_panel:login')

class ForgotPasswordView(View):
    def post(self, request):
        email = request.POST.get('email')
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            if not is_admin(user):
                messages.error(request, "This email is not registered as an admin user.", extra_tags='forgot_password_message')
                return redirect('admin_panel:login')

            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            reset_url = request.build_absolute_uri(
                reverse('admin_panel:reset_password', kwargs={'uidb64': uid, 'token': token})
            )
            # Send email
            subject = 'Password Reset Request'
            template_name = 'email/password_reset_email.html'
            context = {
                'reset_url': reset_url,
            }
            send_mail(subject, template_name, context, email)
            
            messages.success(request, "Password reset link has been sent to your email.", extra_tags='forgot_password_message')
            return redirect('admin_panel:login')
            
        except User.DoesNotExist:
            messages.error(request, "Email not found.", extra_tags='forgot_password_message')
            return redirect('admin_panel:login')
        except Exception as e:
            messages.error(request, "An error occurred while sending the reset link.", extra_tags='forgot_password_message')
            return redirect('admin_panel:login')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class AdminListView(TemplateView):
    template_name = 'custom-admin/services/manage-admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        # Show only admins, not superadmins (superadmin cannot edit other superadmins)
        admins = User.objects.filter(is_admin=True, is_superadmin=False)
        
        if search_query:
            admins = admins.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        admins = admins.order_by('-date_joined')
        paginator = Paginator(admins, 25)
        admins_page = paginator.get_page(page)

        context['admins'] = admins_page
        context['search_query'] = search_query
        context['title'] = 'Admin Management'
        context['current_user'] = self.request.user
        return context


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class AdminAddView(View):
    def post(self, request):
        User = get_user_model()
        email = request.POST.get('email').lower()
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone_number = request.POST.get('phone_number')
        country_code = request.POST.get('country_code')
        
        try:
            # Validation
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return redirect('admin_panel:manage_admins')
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match')
                return redirect('admin_panel:manage_admins')
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long')
                return redirect('admin_panel:manage_admins')
            
            # Create admin user (only regular admin, not superadmin)
            admin_user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                phone_number=phone_number,
                country_code=country_code,
                is_admin=True,  # Only create regular admins
                is_superadmin=False,
                is_temp=False,
                is_active=True
            )
            
            messages.success(request, 'Admin created successfully')
            
            # Send welcome email
            subject = 'Welcome to Admin Panel'
            template_name = 'email/admin_welcome_email.html'
            context = {
                'first_name': first_name,
                'email': email,
                'login_url': request.build_absolute_uri(reverse('admin_panel:login'))
            }
            try:
                send_mail(subject, template_name, context, email)
            except:
                pass
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_admins')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class AdminEditView(View):
    def post(self, request, admin_id):
        User = get_user_model()
        try:
            admin_user = User.objects.get(pk=admin_id, is_admin=True, is_superadmin=False)
            
            admin_user.first_name = request.POST.get('first_name')
            admin_user.last_name = request.POST.get('last_name')
            admin_user.email = request.POST.get('email')
            admin_user.phone_number = request.POST.get('phone_number')
            admin_user.country_code = request.POST.get('country_code')
            # Don't allow changing admin type through edit
            admin_user.is_active = request.POST.get('status') == 'true'
            admin_user.save()
            messages.success(request, 'Admin updated successfully')
        except User.DoesNotExist:
            messages.error(request, 'Admin not found or you cannot edit this user')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:manage_admins')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class AdminDeleteView(View):
    def post(self, request, admin_id):
        User = get_user_model()
        try:
            if int(admin_id) == request.user.id:
                messages.error(request, 'You cannot delete your own account')
                return redirect('admin_panel:manage_admins')
            
            admin_user = User.objects.get(pk=admin_id, is_admin=True, is_superadmin=False)
            admin_user.delete()
            messages.success(request, 'Admin deleted successfully')
        except User.DoesNotExist:
            messages.error(request, 'Admin not found or you cannot delete this user')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:manage_admins')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class AdminToggleStatusView(View):
    def post(self, request, admin_id):
        User = get_user_model()
        try:
            if int(admin_id) == request.user.id:
                messages.error(request, 'You cannot toggle your own status')
                return redirect('admin_panel:manage_admins')
            
            admin_user = User.objects.get(pk=admin_id, is_admin=True, is_superadmin=False)
            admin_user.is_active = not admin_user.is_active
            admin_user.save()
            status = 'activated' if admin_user.is_active else 'deactivated'
            messages.success(request, f'Admin {status} successfully')
        except User.DoesNotExist:
            messages.error(request, 'Admin not found or you cannot toggle this user')
        return redirect('admin_panel:manage_admins')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class AdminPasswordReset(View):
    def post(self, request, admin_id):
        User = get_user_model()

        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation
        if not password or not confirm_password:
            messages.error(request, "Both password fields are required.")
            return redirect('admin_panel:manage_admins')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('admin_panel:manage_admins')
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('admin_panel:manage_admins')

        # Get admin user
        admin_user = get_object_or_404(User, id=admin_id)

        # Set new password securely
        admin_user.set_password(password)
        admin_user.save(update_fields=["password"])

        messages.success(request, "Password reset successfully.")
        return redirect("admin_panel:manage_admins")  # adjust redirect if needed

            

# Keep UserListView accessible to regular admins
@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UserListView(TemplateView):
    template_name = 'custom-admin/services/manage-user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        users = User.objects.filter(is_superadmin=False, is_admin=False)
        
        if search_query:
            users = users.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        users = users.order_by('-date_joined')
        paginator = Paginator(users, 25)  
        users_page = paginator.get_page(page)

        context['users'] = users_page
        context['search_query'] = search_query
        context['title'] = 'User Management'
        return context
  
@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UserToggleStatusView(View):
    def post(self, request, user_id):
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id, is_admin=False, is_superadmin=False)
            user.is_active = not user.is_active
            user.save()
            status = 'activated' if user.is_active else 'deactivated'
            messages.success(request, f'User {status} successfully')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        return redirect('admin_panel:manage_users')

@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class UserDeleteView(View):
    def post(self, request, user_id):
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id, is_admin=False, is_superadmin=False)
            user.delete()
            messages.success(request, 'User deleted successfully')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        return redirect('admin_panel:manage_users')


@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class UserEditView(View):
    def post(self, request):
        User = get_user_model()
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(pk=user_id, is_admin=False, is_superadmin=False)
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.phone_number = request.POST.get('phone_number')
            user.country_code = request.POST.get('country_code')
            user.is_active = request.POST.get('status') == 'true'
            user.save()
            messages.success(request, 'User updated successfully')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:manage_users')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CityListView(TemplateView):
    template_name = 'custom-admin/services/manage-city.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)

        cities = City.objects.select_related('country').all()
        if search_query:
            cities = cities.filter(
                Q(name__icontains=search_query) |
                Q(country__name__icontains=search_query)
            )
        cities = cities.order_by('-id')
        paginator = Paginator(cities, 25)
        cities_page = paginator.get_page(page)

        context['cities'] = cities_page
        context['countries'] = Country.objects.order_by('name')  # for add/edit forms
        context['search_query'] = search_query
        context['title'] = 'City Management'
        return context


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CityAddView(View):
    def post(self, request):
        try:
            country_id = request.POST.get('country')
            name = request.POST.get('name', '').strip()
            is_popular = request.POST.get('is_popular', 'false') == 'true'
            icon = request.FILES.get('icon')

            if not country_id or not name:
                messages.error(request, 'Country and city name are required')
                return redirect('admin_panel:manage_cities')

            country = get_object_or_404(Country, pk=country_id)

            # Optional: prevent duplicate city name for same country
            if City.objects.filter(country=country, name__iexact=name).exists():
                messages.error(request, f'City "{name}" already exists for {country.name}')
                return redirect('admin_panel:manage_cities')

            City.objects.create(country=country, name=name, is_popular=is_popular, icon=icon)
            messages.success(request, f'City "{name}" added successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('admin_panel:manage_cities')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CityEditView(View):
    def post(self, request, city_id):
        try:
            city = City.objects.get(pk=city_id)
            country_id = request.POST.get('country')
            name = request.POST.get('name', '').strip()
            is_popular = request.POST.get('is_popular', 'false') == 'true'
            icon = request.FILES.get('icon')
            print(icon,"url")

            if not country_id or not name:
                messages.error(request, 'Country and city name are required')
                return redirect('admin_panel:manage_cities')

            country = get_object_or_404(Country, pk=country_id)

            # prevent duplicate name in same country (except itself)
            if City.objects.filter(country=country, name__iexact=name).exclude(pk=city_id).exists():
                messages.error(request, f'City "{name}" already exists for {country.name}')
                return redirect('admin_panel:manage_cities')

            city.country = country
            city.name = name
            city.is_popular = is_popular
            if icon:
                # delete old icon file if exists
                try:
                    if city.icon and default_storage.exists(city.icon.name):
                        default_storage.delete(city.icon.name)
                except Exception:
                    pass
                city.icon = icon
            city.save()
            messages.success(request, 'City updated successfully')
        except City.DoesNotExist:
            messages.error(request, 'City not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('admin_panel:manage_cities')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CityDeleteView(View):
    def post(self, request, city_id):
        try:
            city = City.objects.get(pk=city_id)
            name = city.name
            city.delete()
            messages.success(request, f'City "{name}" deleted successfully')
        except City.DoesNotExist:
            messages.error(request, 'City not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('admin_panel:manage_cities')

# CARD MANAGEMENT VIEWS
@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CardListView(TemplateView):
    template_name = 'custom-admin/services/manage-card.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        cards = Card.objects.prefetch_related('benefits').all()
        if search_query:
            cards = cards.filter(
                Q(name__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        cards = cards.order_by('-created_at')
        paginator = Paginator(cards, 25)
        cards_page = paginator.get_page(page)
        # Add benefits data for each card
        cards_with_benefits = []
        for card in cards_page:
            cards_with_benefits.append({
                'id': card.id,
                'name': card.name,
                'duration': card.duration,
                'price': str(card.price),
                'short_description': card.short_description,
                'is_active': card.is_active,
                'benefits': list(card.benefits.values('id', 'title', 'description', 'icon'))
            })
        context['cards'] = cards_page
        context['cards_json'] = json.dumps(cards_with_benefits)
        context['search_query'] = search_query
        context['title'] = 'Card Management'
        return context


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CardAddView(View):
    def post(self, request):
        try:
            name = request.POST.get('name')
            duration = request.POST.get('duration')
            price = request.POST.get('price')
            short_description = request.POST.get('short_description')
            
            # Validation
            if Card.objects.filter(name=name).exists():
                messages.error(request, 'Card with this name already exists')
                return redirect('admin_panel:manage_cards')
            
            if not name or not duration or not price:
                messages.error(request, 'Please fill all required fields')
                return redirect('admin_panel:manage_cards')
            
            try:
                price = float(price)
                if price < 0:
                    messages.error(request, 'Price cannot be negative')
                    return redirect('admin_panel:manage_cards')
            except ValueError:
                messages.error(request, 'Invalid price format')
                return redirect('admin_panel:manage_cards')
            
            # Create card
            card = Card.objects.create(
                name=name,
                duration=duration,
                price=price,
                short_description=short_description,
                is_active=True
            )
            
            # Handle benefits
            benefits_json = request.POST.get('benefits_json', '[]')
            try:
                benefits = json.loads(benefits_json)
                benefit_count = 0
                for benefit in benefits:
                    if benefit.get('title'):
                        CardBenefit.objects.create(
                            card=card,
                            title=benefit.get('title'),
                            description=benefit.get('description', ''),
                            icon=benefit.get('icon', '')
                        )
                        benefit_count += 1
                
                messages.success(request, f'Card "{name}" created successfully with {benefit_count} benefits')
            except (json.JSONDecodeError, Exception) as e:
                messages.success(request, f'Card "{name}" created successfully (benefits error: {str(e)})')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_cards')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CardEditView(View):
    def post(self, request, card_id):
        try:
            card = Card.objects.get(pk=card_id)
            
            card.name = request.POST.get('name', card.name)
            card.duration = request.POST.get('duration', card.duration)
            card.short_description = request.POST.get('short_description', card.short_description)
            
            price = request.POST.get('price')
            if price:
                try:
                    price = float(price)
                    if price < 0:
                        messages.error(request, 'Price cannot be negative')
                        return redirect('admin_panel:manage_cards')
                    card.price = price
                except ValueError:
                    messages.error(request, 'Invalid price format')
                    return redirect('admin_panel:manage_cards')
            
            status = request.POST.get('status')
            if status:
                card.is_active = status == 'true'
            
            card.save()
            
            # Handle benefits update
            benefits_json = request.POST.get('benefits_json', '[]')
            try:
                benefits = json.loads(benefits_json)
                
                # Delete old benefits
                card.benefits.all().delete()
                
                # Create new benefits
                benefit_count = 0
                for benefit in benefits:
                    if benefit.get('title'):
                        CardBenefit.objects.create(
                            card=card,
                            title=benefit.get('title'),
                            description=benefit.get('description', ''),
                            icon=benefit.get('icon', '')
                        )
                        benefit_count += 1
                
                messages.success(request, f'Card updated successfully with {benefit_count} benefits')
            except (json.JSONDecodeError, Exception) as e:
                messages.success(request, f'Card updated successfully (benefits: {str(e)})')
                
        except Card.DoesNotExist:
            messages.error(request, 'Card not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_cards')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CardDeleteView(View):
    def post(self, request, card_id):
        try:
            card = Card.objects.get(pk=card_id)
            card_name = card.name
            card.delete()
            messages.success(request, f'Card "{card_name}" and all its benefits deleted successfully')
        except Card.DoesNotExist:
            messages.error(request, 'Card not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_cards')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CardToggleStatusView(View):
    def post(self, request, card_id):
        try:
            card = Card.objects.get(pk=card_id)
            card.is_active = not card.is_active
            card.save()
            status = 'activated' if card.is_active else 'deactivated'
            messages.success(request, f'Card {status} successfully')
        except Card.DoesNotExist:
            messages.error(request, 'Card not found')
        
        return redirect('admin_panel:manage_cards')


# API endpoint to get card details with benefits
@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CardDetailAPIView(View):
    def get(self, request, card_id):
        try:
            card = Card.objects.prefetch_related('benefits').get(pk=card_id)
            benefits = list(card.benefits.values('id', 'title', 'description', 'icon'))
            
            return JsonResponse({
                'success': True,
                'card': {
                    'id': card.id,
                    'name': card.name,
                    'duration': card.duration,
                    'price': str(card.price),
                    'short_description': card.short_description,
                    'is_active': card.is_active
                },
                'benefits': benefits
            })
        except Card.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Card not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


# NEWS MANAGEMENT VIEWS
@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class NewsListView(TemplateView):
    template_name = 'custom-admin/services/manage-news.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        category_filter = self.request.GET.get('category', '')
        city_filter = self.request.GET.get('city', '')
        page = self.request.GET.get('page', 1)
        
        news = NewsArticle.objects.select_related('category', 'city').all()
        
        if search_query:
            news = news.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        if category_filter:
            news = news.filter(category_id=category_filter)
            
        if city_filter:
            news = news.filter(city_id=city_filter)
        
        news = news.order_by('-published_at')
        paginator = Paginator(news, 25)
        news_page = paginator.get_page(page)

        # Get all categories and cities for filter dropdowns
        categories = BusinessCategory.objects.filter(is_active=True).order_by('name')
        cities = City.objects.all().order_by('name')

        context.update({
            'news': news_page,
            'search_query': search_query,
            'category_filter': category_filter,
            'city_filter': city_filter,
            'categories': categories,
            'cities': cities,
            'title': 'News Management'
        })
        return context


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class NewsAddView(View):
    def post(self, request):
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            category_id = request.POST.get('category')
            city_id = request.POST.get('city')
            icon = request.FILES.get('icon')
            
            # Validation
            if not title or not content:
                messages.error(request, 'Title and content are required')
                return redirect('admin_panel:manage_news')
            
            if len(title) < 5:
                messages.error(request, 'Title must be at least 5 characters')
                return redirect('admin_panel:manage_news')
            
            if len(content) < 20:
                messages.error(request, 'Content must be at least 20 characters')
                return redirect('admin_panel:manage_news')
            
            # Get category and city objects if provided
            category = None
            if category_id:
                try:
                    category = BusinessCategory.objects.get(id=category_id)
                except BusinessCategory.DoesNotExist:
                    pass
            
            city = None
            if city_id:
                try:
                    city = City.objects.get(id=city_id)
                except City.DoesNotExist:
                    pass
            
            # Create news article
            news_article = NewsArticle.objects.create(
                title=title,
                content=content,
                category=category,
                city=city,
                icon=icon
            )
            
            messages.success(request, f'News article "{title}" created successfully')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_news')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class NewsEditView(View):
    def post(self, request, news_id):
        try:
            news_article = NewsArticle.objects.get(pk=news_id)
            
            news_article.title = request.POST.get('title', news_article.title)
            news_article.content = request.POST.get('content', news_article.content)
            
            # Handle category update
            category_id = request.POST.get('category')
            if category_id:
                try:
                    news_article.category = BusinessCategory.objects.get(id=category_id)
                except BusinessCategory.DoesNotExist:
                    pass
            else:
                news_article.category = None
            
            # Handle city update
            city_id = request.POST.get('city')
            if city_id:
                try:
                    news_article.city = City.objects.get(id=city_id)
                except City.DoesNotExist:
                    pass
            else:
                news_article.city = None
            
            # Handle icon upload
            if 'icon' in request.FILES:
                # Delete old icon if exists
                if news_article.icon:
                    if default_storage.exists(news_article.icon.name):
                        default_storage.delete(news_article.icon.name)
                
                news_article.icon = request.FILES['icon']
            
            news_article.save()
            messages.success(request, 'News article updated successfully')
            
        except NewsArticle.DoesNotExist:
            messages.error(request, 'News article not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_news')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class NewsDeleteView(View):
    def post(self, request, news_id):
        try:
            news_article = NewsArticle.objects.get(pk=news_id)
            article_title = news_article.title
            
            # Delete icon if exists
            if news_article.icon:
                if default_storage.exists(news_article.icon.name):
                    default_storage.delete(news_article.icon.name)
            
            news_article.delete()
            messages.success(request, f'News article "{article_title}" deleted successfully')
        except NewsArticle.DoesNotExist:
            messages.error(request, 'News article not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_news')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class NewsDetailAPIView(View):
    def get(self, request, news_id):
        try:
            news_article = NewsArticle.objects.select_related('category', 'city').get(pk=news_id)
            
            icon_url = ''
            if news_article.icon:
                icon_url = news_article.icon.url
            
            return JsonResponse({
                'success': True,
                'news': {
                    'id': news_article.id,
                    'title': news_article.title,
                    'content': news_article.content,
                    'icon_url': icon_url,
                    'category_id': news_article.category.id if news_article.category else None,
                    'category_name': news_article.category.name if news_article.category else '',
                    'city_id': news_article.city.id if news_article.city else None,
                    'city_name': news_article.city.name if news_article.city else '',
                    'published_at': news_article.published_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'News article not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


# BUSINESS CATEGORY MANAGEMENT VIEWS
@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CategoryListView(TemplateView):
    template_name = 'custom-admin/services/manage-category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        categories = BusinessCategory.objects.all()
        
        if search_query:
            categories = categories.filter(name__icontains=search_query)
        
        categories = categories.order_by('-created_at')
        paginator = Paginator(categories, 25)
        categories_page = paginator.get_page(page)

        context['categories'] = categories_page
        context['search_query'] = search_query
        context['title'] = 'Business Category Management'
        return context


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CategoryAddView(View):
    def post(self, request):
        try:
            name = request.POST.get('name', '').strip()
            icon = request.FILES.get('icon')
            print(icon,"url")
            
            # Validation
            if not name:
                messages.error(request, 'Category name is required')
                return redirect('admin_panel:manage_categories')
            
            if len(name) < 3:
                messages.error(request, 'Category name must be at least 3 characters')
                return redirect('admin_panel:manage_categories')
            
            if len(name) > 255:
                messages.error(request, 'Category name must not exceed 255 characters')
                return redirect('admin_panel:manage_categories')
            
            # Check if category already exists
            if BusinessCategory.objects.filter(name__iexact=name).exists():
                messages.error(request, f'Category "{name}" already exists')
                return redirect('admin_panel:manage_categories')
            
            # Create category
            category = BusinessCategory.objects.create(
                name=name,
                icon=icon,
                is_active=True
            )
            
            messages.success(request, f'Category "{name}" created successfully')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_categories')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CategoryEditView(View):
    def post(self, request, category_id):
        try:
            category = BusinessCategory.objects.get(pk=category_id)
            name = request.POST.get('name', '').strip()
            icon = request.FILES.get('icon')
            print(icon,"url")
            
            # Validation
            if not name:
                messages.error(request, 'Category name is required')
                return redirect('admin_panel:manage_categories')
            
            if len(name) < 3:
                messages.error(request, 'Category name must be at least 3 characters')
                return redirect('admin_panel:manage_categories')
            
            if len(name) > 255:
                messages.error(request, 'Category name must not exceed 255 characters')
                return redirect('admin_panel:manage_categories')
            
            # Check if new name already exists (but allow same name for current category)
            if BusinessCategory.objects.filter(name__iexact=name).exclude(pk=category_id).exists():
                messages.error(request, f'Category "{name}" already exists')
                return redirect('admin_panel:manage_categories')
            
            old_name = category.name
            category.name = name
            if icon:
                # delete old icon file if exists
                try:
                    if category.icon and default_storage.exists(category.icon.name):
                        default_storage.delete(category.icon.name)
                except Exception:
                    pass
                category.icon = icon
            
            # Handle status update
            status = request.POST.get('status')
            if status:
                category.is_active = status == 'true'
            
            category.save()
            messages.success(request, f'Category updated from "{old_name}" to "{name}" successfully')
            
        except BusinessCategory.DoesNotExist:
            messages.error(request, 'Category not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_categories')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CategoryDeleteView(View):
    def post(self, request, category_id):
        try:
            category = BusinessCategory.objects.get(pk=category_id)
            category_name = category.name
            
            # Check if category has businesses
            business_count = Business.objects.filter(category=category).count()
            if business_count > 0:
                messages.error(request, f'Cannot delete category "{category_name}" as it has {business_count} business(es) associated with it')
                return redirect('admin_panel:manage_categories')
            
            # delete icon file if exists
            try:
                if category.icon and default_storage.exists(category.icon.name):
                    default_storage.delete(category.icon.name)
            except Exception:
                pass
            
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully')
        except BusinessCategory.DoesNotExist:
            messages.error(request, 'Category not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_categories')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CategoryToggleStatusView(View):
    def post(self, request, category_id):
        try:
            category = BusinessCategory.objects.get(pk=category_id)
            category.is_active = not category.is_active
            category.save()
            status = 'activated' if category.is_active else 'deactivated'
            messages.success(request, f'Category {status} successfully')
        except BusinessCategory.DoesNotExist:
            messages.error(request, 'Category not found')
        
        return redirect('admin_panel:manage_categories')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class CategoryDetailAPIView(View):
    def get(self, request, category_id):
        try:
            category = BusinessCategory.objects.get(pk=category_id)
            business_count = Business.objects.filter(category=category).count()
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'is_active': category.is_active,
                    'business_count': business_count,
                    'created_at': category.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': category.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        except BusinessCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


# BUSINESS MANAGEMENT VIEWS
@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class BusinessListView(TemplateView):
    template_name = 'custom-admin/services/manage-business.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        user = self.request.user
        businesses = Business.objects.select_related('category', 'owner').all()
        if user.is_admin and not user.is_superadmin:
            businesses = businesses.filter(owner=user)

        if search_query:
            businesses = businesses.filter(
                models.Q(name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        
        api_key = GoogleMapsSettings.objects.first().api_key
        businesses = businesses.order_by('-created_at')
        paginator = Paginator(businesses, 25)
        context['businesses'] = paginator.get_page(page)
        context['categories'] = BusinessCategory.objects.filter(is_active=True)
        context['GOOGLE_MAPS_API_KEY'] = api_key if api_key else settings.GOOGLE_MAPS_API_KEY
        context['admins'] = User.objects.filter(is_admin=True, is_active=True)
        context['search_query'] = search_query
        return context

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class BusinessAddView(View):
    def post(self, request):
        name = request.POST.get('name', '').strip()
        owner_id = request.POST.get('owner')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '').strip()
        address = request.POST.get('address', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        website = request.POST.get('website', '').strip()
        is_active = request.POST.get('is_active') == 'true'
        is_featured = request.POST.get('is_featured') == 'true'
        logo = request.FILES.get('logo')
        gallery_images = request.FILES.getlist('gallery_images')

        # Basic validation
        if not name or not owner_id or not category_id:
            messages.error(request, "Name, Owner, and Category are required.")
            return redirect('admin_panel:manage_businesses')

        owner = get_object_or_404(User, pk=owner_id, is_admin=True)
        category = get_object_or_404(BusinessCategory, pk=category_id)

        business = Business(
            name=name,
            owner=owner,
            category=category,
            description=description,
            address=address,
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None,
            phone_number=phone_number,
            email=email,
            website=website,
            is_active=is_active,
            is_featured=is_featured,
            logo=logo
        )
        if logo:
            business.logo = logo
        business.save()
        for image in gallery_images:
            if image:
                BusinessImage.objects.create(business=business, image=image)
        messages.success(request, "Business added successfully.")
        return redirect('admin_panel:manage_businesses')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class BusinessEditView(View):
    def post(self, request, business_id):
        business = get_object_or_404(Business, pk=business_id)
        name = request.POST.get('name', '').strip()
        owner_id = request.POST.get('owner')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '').strip()
        address = request.POST.get('address', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        website = request.POST.get('website', '').strip()
        is_active = request.POST.get('is_active') == 'true'
        is_featured = request.POST.get('is_featured') == 'true'
        logo = request.FILES.get('logo')

        if not name or not owner_id or not category_id:
            messages.error(request, "Name, Owner, and Category are required.")
            return redirect('admin_panel:manage_businesses')

        owner = get_object_or_404(User, pk=owner_id, is_admin=True)
        category = get_object_or_404(BusinessCategory, pk=category_id)

        business.name = name
        business.owner = owner
        business.category = category
        business.description = description
        business.address = address
        business.phone_number = phone_number
        business.email = email
        business.latitude = latitude if latitude else None
        business.longitude = longitude if longitude else None
        business.website = website
        business.is_active = is_active
        business.is_featured = is_featured
        if logo:
            business.logo = logo
        business.save()
        # Handle deleted images
        deleted_image_ids = request.POST.get('deleted_image_ids', '')
        if deleted_image_ids:
            deleted_ids = [int(id) for id in deleted_image_ids.split(',') if id.strip()]
            BusinessImage.objects.filter(id__in=deleted_ids, business=business).delete()
        
        # Handle new gallery images
        gallery_images = request.FILES.getlist('gallery_images')
        for image in gallery_images:
            if image:
                BusinessImage.objects.create(business=business, image=image)
        messages.success(request, "Business updated successfully.")
        return redirect('admin_panel:manage_businesses')

class BusinessDeleteView(View):
    def post(self, request, business_id):
        business = get_object_or_404(Business, pk=business_id)
        business.delete()
        messages.success(request, "Business deleted successfully.")
        return redirect('admin_panel:manage_businesses')

class BusinessToggleStatusView(View):
    def post(self, request, business_id):
        business = get_object_or_404(Business, pk=business_id)
        business.is_active = not business.is_active
        business.save()
        messages.success(request, "Business status updated.")
        return redirect('admin_panel:manage_businesses')


# BUSINESS OFFER MANAGEMENT VIEWS
@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class OfferListView(TemplateView):
    template_name = 'custom-admin/services/manage-offers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        user = self.request.user
        offers = BusinessOffer.objects.select_related('business').all()
        if user.is_admin and not user.is_superadmin:
            offers = offers.filter(business__owner = user)
        if search_query:
            offers = offers.filter(
                models.Q(title__icontains=search_query) |
                models.Q(business__name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        offers = offers.order_by('-created_at')
        paginator = Paginator(offers, 25)
        context['offers'] = paginator.get_page(page)
        if user.is_admin and not user.is_superadmin:
            context['businesses'] = Business.objects.filter(is_active=True, owner=user)
        else:
            context['businesses'] = Business.objects.filter(is_active=True)
        context['search_query'] = search_query
        context['title'] = 'Business Offers Management'
        return context

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class OfferAddView(View):
    def post(self, request):
        try:
            business_id = request.POST.get('business')
            title = request.POST.get('title', '').strip()
            coupon_code = request.POST.get('coupon_code', '').strip().upper()
            description = request.POST.get('description', '').strip()
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            is_active = request.POST.get('is_active') == 'true'

            # Basic validation
            if not business_id or not title or not description or not start_date or not end_date:
                messages.error(request, "All fields are required.")
                return redirect('admin_panel:manage_offers')

            business = get_object_or_404(Business, pk=business_id)

            # Create offer
            offer = BusinessOffer.objects.create(
                business=business,
                title=title,
                coupon_code=coupon_code,
                description=description,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active
            )
            
            messages.success(request, f'Offer "{title}" created successfully.')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_offers')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class OfferEditView(View):
    def post(self, request, offer_id):
        try:
            offer = get_object_or_404(BusinessOffer, pk=offer_id)
            business_id = request.POST.get('business')
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            coupon_code = request.POST.get('coupon_code', '').strip().upper()
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            is_active = request.POST.get('is_active') == 'true'
            is_popular = request.POST.get('is_popular') == 'true'

            # Basic validation
            if not business_id or not title or not description or not start_date or not end_date:
                messages.error(request, "All fields are required.")
                return redirect('admin_panel:manage_offers')

            business = get_object_or_404(Business, pk=business_id)

            # Update offer
            offer.business = business
            offer.title = title
            offer.description = description
            offer.coupon_code = coupon_code
            offer.start_date = start_date
            offer.end_date = end_date
            offer.is_active = is_active
            offer.is_popular = is_popular
            offer.save()
            
            messages.success(request, f'Offer "{title}" updated successfully.')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_offers')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class OfferDeleteView(View):
    def post(self, request, offer_id):
        try:
            offer = get_object_or_404(BusinessOffer, pk=offer_id)
            offer_title = offer.title
            offer.delete()
            messages.success(request, f'Offer "{offer_title}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_offers')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class OfferToggleStatusView(View):
    def post(self, request, offer_id):
        try:
            offer = get_object_or_404(BusinessOffer, pk=offer_id)
            offer.is_active = not offer.is_active
            offer.save()
            status = 'activated' if offer.is_active else 'deactivated'
            messages.success(request, f'Offer {status} successfully.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_panel:manage_offers')
    


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class ManageAPISettingsView(TemplateView):
    template_name = 'custom-admin/services/manage-api.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create settings instances
        # chatgpt_settings = ChatGPTSettings.objects.first()
        # if not chatgpt_settings:
        #     chatgpt_settings = ChatGPTSettings.objects.create()

        stripe_settings = StipeKeySettings.objects.first()
        if not stripe_settings:
            stripe_settings = StipeKeySettings.objects.create()

        google_maps_settings = GoogleMapsSettings.objects.first()
        if not google_maps_settings:
            google_maps_settings = GoogleMapsSettings.objects.create()

        firebase_settings = FirebaseSettings.objects.first()
        if not firebase_settings:
            firebase_settings = FirebaseSettings.objects.create()
        
        smtp_settings = SMTPSettings.objects.first()
        if not smtp_settings:  
            smtp_settings = SMTPSettings.objects.create()

        context.update({
            'title': 'Manage API Settings',
            # 'chatgpt_settings': chatgpt_settings,
            'smtp_settings': smtp_settings,
            'stripe_settings': stripe_settings,
            'google_maps_settings': google_maps_settings,
            'firebase_settings': firebase_settings,
        })
        return context

# @method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
# class UpdateChatGPTSettingsView(View):
#     def post(self, request, api_id):
#         try:
#             chatgpt_settings = get_object_or_404(ChatGPTSettings, pk=api_id)
            
#             chatgpt_settings.model = request.POST.get('model', chatgpt_settings.model)
#             chatgpt_settings.api_key = request.POST.get('api_key', chatgpt_settings.api_key)
#             chatgpt_settings.status = request.POST.get('is_active', 'false') == 'true'
            
#             chatgpt_settings.save()
#             messages.success(request, 'ChatGPT settings updated successfully')
            
#         except Exception as e:
#             messages.error(request, f'Error updating ChatGPT settings: {str(e)}')
        
#         return redirect('admin_panel:manage_api_settings')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UpdateStripeSettingsView(View):
    def post(self, request, stripe_id):
        try:
            stripe_settings = get_object_or_404(StipeKeySettings, pk=stripe_id)
            
            stripe_settings.public_key = request.POST.get('publishable_key', stripe_settings.public_key)
            stripe_settings.secret_key = request.POST.get('secret_key', stripe_settings.secret_key)
            stripe_settings.currency = request.POST.get('currency', stripe_settings.currency)
            stripe_settings.version = request.POST.get('api_version', stripe_settings.version)
            
            stripe_settings.save()
            messages.success(request, 'Stripe settings updated successfully')
            
        except Exception as e:
            messages.error(request, f'Error updating Stripe settings: {str(e)}')
        
        return redirect('admin_panel:manage_api_settings')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UpdateGoogleMapsSettingsView(View):
    def post(self, request, maps_id):
        try:
            maps_settings = get_object_or_404(GoogleMapsSettings, pk=maps_id)
            
            maps_settings.api_key = request.POST.get('api_key', maps_settings.api_key)
            
            maps_settings.save()
            messages.success(request, 'Google Maps settings updated successfully')
            
        except Exception as e:
            messages.error(request, f'Error updating Google Maps settings: {str(e)}')
        
        return redirect('admin_panel:manage_api_settings')

@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class UpdateFirebaseSettingsView(View):
    def post(self, request, notification_id):
        try:
            firebase_settings = get_object_or_404(FirebaseSettings, pk=notification_id)
            
            if 'config_file' in request.FILES:
                # Delete old file if exists
                if firebase_settings.config_file:
                    if default_storage.exists(firebase_settings.config_file.name):
                        default_storage.delete(firebase_settings.config_file.name)
                
                firebase_settings.config_file = request.FILES['config_file']
                firebase_settings.save()
                
                messages.success(request, 'Firebase notification settings updated successfully')
            else:
                messages.error(request, 'Please select a file to upload')
                
        except Exception as e:
            messages.error(request, f'Error updating Firebase settings: {str(e)}')
        
        return redirect('admin_panel:manage_api_settings')

# @method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
# class ToggleChatGPTStatusView(View):
#     def post(self, request, api_id):
#         try:
#             chatgpt_settings = get_object_or_404(ChatGPTSettings, pk=api_id)
#             chatgpt_settings.status = not chatgpt_settings.status
#             chatgpt_settings.save()
            
#             status = 'activated' if chatgpt_settings.status else 'deactivated'
#             messages.success(request, f'ChatGPT API {status} successfully')
            
#         except Exception as e:
#             messages.error(request, f'Error toggling ChatGPT status: {str(e)}')
        
#         return redirect('admin_panel:manage_api_settings')

def _parse_dt(value):
    if not value:
        return None
    dt = datetime.datetime.fromisoformat(value)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UserCardAdminListView(TemplateView):
    template_name = 'custom-admin/services/manage-user-card.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('search', '').strip()

        user_cards = UserCard.objects.select_related('user', 'card').order_by('-start_at')
        if search:
            user_cards = user_cards.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(card__name__icontains=search)
            )

        paginator = Paginator(user_cards, 25)
        page_obj = paginator.get_page(self.request.GET.get('page', 1))

        context.update({
            'title': 'Manage User Cards',
            'user_cards': page_obj,
            'search_query': search,
            'users': User.objects.filter(is_admin=False, is_superadmin=False, is_active=True, is_temp=False).order_by('email'),
            'cards': Card.objects.filter(is_active=True).order_by('name'),
        })
        return context


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UserCardAdminAddView(View):
    def post(self, request):
        try:
            user = get_object_or_404(User, pk=request.POST.get('user'), is_admin=False, is_superadmin=False)
            card = get_object_or_404(Card, pk=request.POST.get('card'))
            start_at = _parse_dt(request.POST.get('start_at')) or timezone.now()
            end_at = _parse_dt(request.POST.get('end_at'))
            if not end_at:
                messages.error(request, 'End date/time is required.')
                return redirect('admin_panel:manage_user_cards')

            user_card = UserCard.objects.create(
                user=user,
                card=card,
                start_at=start_at,
                end_at=end_at,
                is_active=request.POST.get('is_active', 'true') == 'true',
            )
            messages.success(request, f'User card created for {user.email} -> {card.name}.')
        except Exception as e:
            messages.error(request, f'Error creating user card: {str(e)}')
        return redirect('admin_panel:manage_user_cards')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UserCardAdminEditView(View):
    def post(self, request, user_card_id):
        try:
            user_card = get_object_or_404(UserCard, pk=user_card_id)
            user_card.user = get_object_or_404(User, pk=request.POST.get('user'), is_admin=False, is_superadmin=False)
            user_card.card = get_object_or_404(Card, pk=request.POST.get('card'))

            start_at = _parse_dt(request.POST.get('start_at'))
            end_at = _parse_dt(request.POST.get('end_at'))
            if start_at:
                user_card.start_at = start_at
            if end_at:
                user_card.end_at = end_at

            user_card.is_active = request.POST.get('is_active', 'true') == 'true'
            user_card.save()
            messages.success(request, 'User card updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating user card: {str(e)}')
        return redirect('admin_panel:manage_user_cards')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UserCardAdminDeleteView(View):
    def post(self, request, user_card_id):
        try:
            user_card = get_object_or_404(UserCard, pk=user_card_id)
            user_card.delete()
            messages.success(request, 'User card deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting user card: {str(e)}')
        return redirect('admin_panel:manage_user_cards')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UserCardAdminToggleStatusView(View):
    def post(self, request, user_card_id):
        try:
            user_card = get_object_or_404(UserCard, pk=user_card_id)
            user_card.is_active = not user_card.is_active
            user_card.save()
            status = 'activated' if user_card.is_active else 'deactivated'
            messages.success(request, f'User card {status}.')
        except Exception as e:
            messages.error(request, f'Error toggling status: {str(e)}')
        return redirect('admin_panel:manage_user_cards')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class ManageContactView(TemplateView):
    template_name = 'custom-admin/services/manage-contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['support'] = Support.objects.first()
        context['address'] = Address.objects.first()
        context['social_link'] = SocialMediaLink.objects.first()
        context['app_download'] = APPDownloadLink.objects.first()
        context['title'] = 'Manage Contact'

        return context

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class ManageLandingPageView(TemplateView):
    template_name = 'custom-admin/services/manage-landing-page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        landing = LandingPageContent.objects.first()
        if not landing:
            landing = LandingPageContent.objects.create()
        context.update({
            'title': 'Manage Landing Page',
            'landing': landing,
        })
        return context

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class UpdateLandingPageView(View):
    def post(self, request):
        landing, _ = LandingPageContent.objects.get_or_create(pk=1)

        # Text fields
        landing.banner_title = request.POST.get('banner_title') or None
        landing.banner_description = request.POST.get('banner_description') or None
        landing.business_section_title = request.POST.get('business_section_title') or None
        landing.business_section_description = request.POST.get('business_section_description') or None
        landing.card_section_title = request.POST.get('card_section_title') or None
        landing.card_section_description = request.POST.get('card_section_description') or None
        landing.news_section_title = request.POST.get('news_section_title') or None
        landing.news_section_description = request.POST.get('news_section_description') or None
        landing.touch_section_title = request.POST.get('touch_section_title') or None
        landing.touch_section_description = request.POST.get('touch_section_description') or None
        landing.faq_section_title = request.POST.get('faq_section_title') or None
        landing.faq_section_description = request.POST.get('faq_section_description') or None
        landing.footer_section_title = request.POST.get('footer_section_title') or None
        landing.footer_section_description = request.POST.get('footer_section_description') or None

        # Images
        banner_image = request.FILES.get('banner_image')
        card_section_image = request.FILES.get('card_section_image')
        try:
            if banner_image:
                # delete old file if exists
                try:
                    if landing.banner_image and default_storage.exists(landing.banner_image.name):
                        default_storage.delete(landing.banner_image.name)
                except Exception:
                    pass
                landing.banner_image = banner_image

            if card_section_image:
                try:
                    if landing.card_section_image and default_storage.exists(landing.card_section_image.name):
                        default_storage.delete(landing.card_section_image.name)
                except Exception:
                    pass
                landing.card_section_image = card_section_image

            landing.save()
            messages.success(request, 'Landing page content updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating landing content: {str(e)}')

        return redirect('admin_panel:manage_landing_page')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class SupportUpdateView(View):
    def post(self, request):
        support, _ = Support.objects.get_or_create(pk=1)

        support.country_code = request.POST.get('country_code', '').strip()
        support.phone_number = request.POST.get('phone_number', '').strip()
        support.email = request.POST.get('email', '').strip()
        support.save()

        messages.success(request, 'Contact information updated successfully')
        return redirect('admin_panel:manage_contact')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class AddressUpdateView(View):
    def post(self, request):
        address, _ = Address.objects.get_or_create(pk=1)

        address.address_line_1 = request.POST.get('address_line_1', '').strip()
        address.address_line_2 = request.POST.get('address_line_2', '').strip() or None
        address.city = request.POST.get('city', '').strip()
        address.state = request.POST.get('state', '').strip()
        address.postal_code = request.POST.get('postal_code', '').strip()
        address.country = request.POST.get('country', '').strip()
        address.save()

        messages.success(request, 'Address updated successfully')
        return redirect('admin_panel:manage_contact')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class SocialLinkUpdateView(View):
    def post(self, request):
        social, _ = SocialMediaLink.objects.get_or_create(pk=1)

        social.instagram = request.POST.get('instagram') or None
        social.facebook = request.POST.get('facebook') or None
        social.twitter = request.POST.get('twitter') or None
        social.linkedin = request.POST.get('linkedin') or None
        social.save()

        messages.success(request, 'Social links updated successfully')
        return redirect('admin_panel:manage_contact')

@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class AppDownloadUpdateView(View):
    def post(self, request):
        app, _ = APPDownloadLink.objects.get_or_create(pk=1)

        app.android_link = request.POST.get('android_link') or None
        app.ios_link = request.POST.get('ios_link') or None
        app.save()

        messages.success(request, 'App download links updated successfully')
        return redirect('admin_panel:manage_contact')



@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class FAQListView(TemplateView):
    template_name = 'custom-admin/services/manage-faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        faqs = FAQ.objects.all()
        if search_query:
            faqs = faqs.filter(Q(question__icontains=search_query) | Q(answer__icontains=search_query))
        faqs = faqs.order_by('-created_at') if hasattr(FAQ, 'created_at') else faqs.order_by('-id')
        paginator = Paginator(faqs, 25)
        faqs_page = paginator.get_page(page)

        context['faqs'] = faqs_page
        context['search_query'] = search_query
        context['title'] = 'Manage FAQ'
        return context


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class FAQAddView(View):
    def post(self, request):
        try:
            FAQ.objects.create(
                question=request.POST.get('question') or '',
                answer=request.POST.get('answer') or '',
                is_active=True
            )
            messages.success(request, 'FAQ added successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:manage_faq')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class FAQEditView(View):
    def post(self, request, faq_id):
        try:
            faq = FAQ.objects.get(pk=faq_id)
            faq.question = request.POST.get('question') or ''
            faq.answer = request.POST.get('answer') or ''
            faq.is_active = (request.POST.get('is_active') == 'true') if request.POST.get('is_active') is not None else faq.is_active
            faq.save()
            messages.success(request, 'FAQ updated successfully')
        except FAQ.DoesNotExist:
            messages.error(request, 'FAQ not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:manage_faq')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class FAQToggleStatusView(View):
    def post(self, request, faq_id):
        try:
            faq = FAQ.objects.get(pk=faq_id)
            faq.is_active = not faq.is_active
            faq.save()
            messages.success(request, 'FAQ status updated')
        except FAQ.DoesNotExist:
            messages.error(request, 'FAQ not found')
        return redirect('admin_panel:manage_faq')


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class FAQDeleteView(View):
    def post(self, request, faq_id):
        try:
            FAQ.objects.get(pk=faq_id).delete()
            messages.success(request, 'FAQ deleted successfully')
        except FAQ.DoesNotExist:
            messages.error(request, 'FAQ not found')
        return redirect('admin_panel:manage_faq')


@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class ContactMessageListView(TemplateView):
    template_name = 'custom-admin/services/manage-contact-messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        msgs = ContactUsMessage.objects.all()
        if search_query:
            msgs = msgs.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(subject__icontains=search_query) |
                Q(message__icontains=search_query)
            )
        msgs = msgs.order_by('-created_at') if hasattr(ContactUsMessage, 'created_at') else msgs.order_by('-id')
        paginator = Paginator(msgs, 25)
        msgs_page = paginator.get_page(page)

        context['messages_page'] = msgs_page
        context['search_query'] = search_query
        context['title'] = 'Manage Contact Messages'
        return context


@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class ContactMessageToggleResolveView(View):
    def post(self, request, message_id):
        try:
            msg = ContactUsMessage.objects.get(pk=message_id)
            msg.is_resolved = not msg.is_resolved
            msg.save()
            messages.success(request, 'Message status updated')
        except ContactUsMessage.DoesNotExist:
            messages.error(request, 'Message not found')
        return redirect('admin_panel:manage_contact_messages')


@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class ContactMessageDeleteView(View):
    def post(self, request, message_id):
        try:
            ContactUsMessage.objects.get(pk=message_id).delete()
            messages.success(request, 'Message deleted successfully')
        except ContactUsMessage.DoesNotExist:
            messages.error(request, 'Message not found')
        return redirect('admin_panel:manage_contact_messages')


@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class ManageSubscriberEmailsView(TemplateView):
    template_name = 'custom-admin/services/manage-subscriber.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search query
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        
        # Filter subscribers
        subscribers = SubsciberEmail.objects.all()
        if search_query:
            subscribers = subscribers.filter(
                email__icontains=search_query
            )
        
        # Order by creation date (newest first) - avoid caching
        subscribers = subscribers.order_by('-created_at')
        
        # Paginate results
        paginator = Paginator(subscribers, 25)  # Show 25 subscribers per page
        subscribers_page = paginator.get_page(page)
        
        context['subscribers'] = subscribers_page
        context['search_query'] = search_query
        context['title'] = 'Manage Subscriber Emails'
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        
        if action == 'add_edit':
            return self._handle_add_edit(request)
        elif action == 'delete':
            return self._handle_delete(request)
        elif action == 'bulk_delete':
            return self._handle_bulk_delete(request)
        
        # If no action or invalid action, show the form again
        return self.get(request, *args, **kwargs)
    
    def _handle_add_edit(self, request):
        subscriber_id = request.POST.get('subscriber_id')
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Email address is required.')
            return redirect('admin_panel:manage_subscribers')
        
        try:
            if subscriber_id:  # Edit existing
                subscriber = SubsciberEmail.objects.get(pk=subscriber_id)
                old_email = subscriber.email
                subscriber.email = email
                subscriber.save()
                messages.success(request, f'Subscriber email updated from {old_email} to {email}.')
            else:  # Add new
                SubsciberEmail.objects.create(email=email)
                messages.success(request, f'Subscriber email {email} added successfully.')
        
        except SubsciberEmail.DoesNotExist:
            messages.error(request, 'Subscriber not found.')
        except Exception as e:
            if 'unique constraint' in str(e).lower():
                messages.error(request, 'This email address is already subscribed.')
            else:
                messages.error(request, f'Error saving subscriber: {str(e)}')
        
        return redirect('admin_panel:manage_subscribers')
    
    def _handle_delete(self, request):
        subscriber_id = request.POST.get('subscriber_id')
        
        try:
            subscriber = SubsciberEmail.objects.get(pk=subscriber_id)
            email = subscriber.email
            subscriber.delete()
            messages.success(request, f'Subscriber email {email} deleted successfully.')
        except SubsciberEmail.DoesNotExist:
            messages.error(request, 'Subscriber not found.')
        except Exception as e:
            messages.error(request, f'Error deleting subscriber: {str(e)}')
        
        return redirect('admin_panel:manage_subscribers')
    
    def _handle_bulk_delete(self, request):
        selected_ids = request.POST.getlist('selected_ids')
        
        if not selected_ids:
            messages.error(request, 'No subscribers selected for deletion.')
            return redirect('admin_panel:manage_subscribers')
        
        try:
            deleted_count = SubsciberEmail.objects.filter(id__in=selected_ids).delete()[0]
            messages.success(request, f'{deleted_count} subscriber email(s) deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting subscribers: {str(e)}')
        
        return redirect('admin_panel:manage_subscribers')