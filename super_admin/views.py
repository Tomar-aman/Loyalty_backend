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
from settings.models import SMTPSettings
from django.core.paginator import Paginator
from django.db import models
from card.models import Card, CardBenefit
from django.http import JsonResponse
import json
from news.models import NewsArticle
from django.core.files.storage import default_storage
from business.models import Business, BusinessCategory, BusinessImage, BusinessOffer
from users.models import User, City, Country
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


# Keep UserListView accessible to regular admins
@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
class UserListView(TemplateView):
    template_name = 'custom-admin/services/manage-user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        users = User.objects.filter(is_temp=False, is_superadmin=False, is_admin=False)
        
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
  
@method_decorator(user_passes_test(is_admin, login_url='admin_panel:login'), name='dispatch')
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
        page = self.request.GET.get('page', 1)
        news = NewsArticle.objects.all()
        
        if search_query:
            news = news.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        news = news.order_by('-published_at')
        paginator = Paginator(news, 25)
        news_page = paginator.get_page(page)

        context['news'] = news_page
        context['search_query'] = search_query
        context['title'] = 'News Management'
        return context


@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class NewsAddView(View):
    def post(self, request):
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
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
            
            # Create news article
            news_article = NewsArticle.objects.create(
                title=title,
                content=content,
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
            news_article = NewsArticle.objects.get(pk=news_id)
            
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
@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class BusinessListView(TemplateView):
    template_name = 'custom-admin/services/manage-business.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        businesses = Business.objects.select_related('category', 'owner').all()
        if search_query:
            businesses = businesses.filter(
                models.Q(name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        businesses = businesses.order_by('-created_at')
        paginator = Paginator(businesses, 25)
        context['businesses'] = paginator.get_page(page)
        context['categories'] = BusinessCategory.objects.filter(is_active=True)
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
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        website = request.POST.get('website', '').strip()
        is_active = request.POST.get('is_active') == 'true'
        is_featured = request.POST.get('is_featured') == 'true'
        logo = request.FILES.get('logo')

        # Basic validation
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
@method_decorator(user_passes_test(is_superadmin, login_url='admin_panel:login'), name='dispatch')
class OfferListView(TemplateView):
    template_name = 'custom-admin/services/manage-offers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        offers = BusinessOffer.objects.select_related('business').all()
        if search_query:
            offers = offers.filter(
                models.Q(title__icontains=search_query) |
                models.Q(business__name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        offers = offers.order_by('-created_at')
        paginator = Paginator(offers, 25)
        context['offers'] = paginator.get_page(page)
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