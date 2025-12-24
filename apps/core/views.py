from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, F, Q
from django.http import JsonResponse
from .models import RestaurantCompany, Branch
from .forms import CompanyForm, BranchForm
from apps.inventory.models import StockItem
from apps.analytics.models import WasteReport
from apps.operations.models import OperationalRequest
from apps.inventory.models import Product, BranchStockSetting
from django.contrib import messages
import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'core/landing_page.html', {})

# --- DASHBOARD ROUTER ---
def dashboard_router(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_superuser:
        return _admin_dashboard(request)
    elif request.user.role == 'manager':
        return _company_dashboard(request)
    elif request.user.role == 'branch_manager':
        return _branch_dashboard(request)
    else:
        return render(request, 'core/dashboard_empty.html', {})

# --- SAAS ADMIN DASHBOARD ---
def _admin_dashboard(request):
    companies = RestaurantCompany.objects.select_related('manager').all().order_by('-created_at')
    total_companies = companies.count()
    active_subscriptions = companies.filter(subscription_status=True).count()
    
    # Mock Revenue
    total_revenue = active_subscriptions * 299 

    context = {
        'user_role': 'SaaS Administrator',
        'companies': companies,
        'total_companies': total_companies,
        'active_subscriptions': active_subscriptions,
        'total_revenue': total_revenue,
        'company_form': CompanyForm(),
        'system_logs': get_system_logs(), # 📜 سجلات النظام
    }
    return render(request, 'core/dashboard_saas_admin.html', context)

# --- COMPANY DASHBOARD (Generic Manager) ---
def _company_dashboard(request):
    if not hasattr(request.user, 'managed_company'):
        return render(request, 'core/dashboard_empty.html', {'error': 'No company assigned'})
        
    company = request.user.managed_company
    branches = company.branches.all()
    
    # Simple Stats
    total_waste_cost = WasteReport.objects.filter(branch__in=branches).aggregate(Sum('total_waste_value'))['total_waste_value__sum'] or 0
    total_requests = OperationalRequest.objects.filter(branch__in=branches, status='PENDING').count()
    
    # Low Stock Alerts (Global for Company)
    low_stock_items = StockItem.objects.filter(branch__in=branches, quantity__lte=F('product__minimum_quantity'))[:5]
    
    # Notifications
    from apps.notifications.models import UserNotification
    notifications = UserNotification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    
    # Count low stock for badge
    low_stock_count = StockItem.objects.filter(branch__in=branches, quantity__lte=F('product__minimum_quantity')).count()
    unread_count = UserNotification.objects.filter(user=request.user, is_read=False).count() + low_stock_count

    # Latest Reports (Added for AI Dashboard consistency)
    latest_reports = WasteReport.objects.filter(branch__company=company).order_by('-generated_date')[:5]

    context = {
        'user_role': 'General Manager',
        'company': company,
        'branches': branches,
        'total_branches': branches.count(),
        'total_waste': total_waste_cost,
        'pending_requests': total_requests,
        'low_stock_items': low_stock_items,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
        'latest_reports': latest_reports, # Restored for Template
        'total_potential_loss': total_waste_cost, # Alias for Template compatibility
    }
    return render(request, 'core/dashboard_company.html', context)

# --- BRANCH DASHBOARD ---
def _branch_dashboard(request):
    # Check if user has a branch
    # Check if user has a branch
    if not hasattr(request.user, 'managed_branch') or not request.user.managed_branch:
        return render(request, 'core/dashboard_empty.html', {'error': 'No branch assigned'})
    
    branch = request.user.managed_branch

    # Stats
    total_waste = WasteReport.objects.filter(branch=branch).aggregate(Sum('total_waste_value'))['total_waste_value__sum'] or 0
    current_stock_count = StockItem.objects.filter(branch=branch).count()
    
    # Alerts
    low_stock = StockItem.objects.filter(branch=branch, quantity__lte=F('product__minimum_quantity'))[:5]
    expiring_soon = StockItem.objects.filter(branch=branch).order_by('expiry_date')[:5] # Mock logic for expiry
    
    # Notifications
    from apps.notifications.models import UserNotification
    notifications = UserNotification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    
    # Count low stock for badge
    low_stock_count = StockItem.objects.filter(branch=branch, quantity__lte=F('product__minimum_quantity')).count()
    unread_count = UserNotification.objects.filter(user=request.user, is_read=False).count() + low_stock_count

    # Requests
    my_requests = OperationalRequest.objects.filter(branch=branch).order_by('-created_at')[:5]

    context = {
        'user_role': 'Branch Manager',
        'branch': branch,
        'total_waste': total_waste,
        'current_stock_count': current_stock_count,
        'low_stock_items': low_stock,
        'expiring_items': expiring_soon,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
        'my_requests': my_requests,
    }
    return render(request, 'core/dashboard_branch.html', context)

# --- BRANCH MANAGEMENT ---
@login_required
def branch_list(request):
    try:
        if request.user.is_superuser:
            branches = Branch.objects.all()
        elif request.user.role == 'manager' and hasattr(request.user, 'managed_company'):
            branches = request.user.managed_company.branches.all()
        else:
             # Branch Managers shouldn't see full list, usually redirected
             raise PermissionDenied("ليس لديك صلاحية لعرض قائمة الفروع.")
    except Exception:
         branches = Branch.objects.none()

    # Search Filter
    search_query = request.GET.get('search', '')
    if search_query:
        branches = branches.filter(
            Q(name__icontains=search_query) | 
            Q(location__icontains=search_query)
        )

    context = {
        'branches': branches,
        'branch_form': BranchForm(user=request.user)
    }
    return render(request, 'core/branch_list.html', context)

@login_required
def add_branch_view(request):
    User = get_user_model()
    # Only Superuser or Manager
    if not (request.user.is_superuser or request.user.role == 'manager'):
        messages.error(request, "ليس لديك صلاحية.")
        return redirect('core:branch_list')

    if request.method == 'POST':
        form = BranchForm(request.POST, user=request.user)
        if form.is_valid():
            branch = form.save(commit=False)
            
            # Create Manager User Logic (Simplified for restoration)
            new_username = form.cleaned_data.get('new_manager_username')
            new_email = form.cleaned_data.get('new_manager_email')
            new_password = form.cleaned_data.get('new_manager_password')
            
            if new_username and new_password:
                try:
                    new_manager = User.objects.create_user(username=new_username, email=new_email, password=new_password, role='branch_manager')
                    branch.manager = new_manager
                except Exception as e:
                    messages.error(request, f"Error creating user: {e}")
                    return redirect('core:branch_list')

            if hasattr(request.user, 'managed_company'):
                branch.company = request.user.managed_company
            elif form.cleaned_data.get('company'):
                branch.company = form.cleaned_data['company']
            
            branch.save()
            messages.success(request, f"تم إضافة الفرع '{branch.name}' بنجاح.")
        else:
            for err in form.errors.values():
                messages.error(request, err)
                
    return redirect('core:branch_list')

# --- CLIENT MANAGEMENT (SAAS ADMIN) ---
@user_passes_test(lambda u: u.is_superuser)
def add_company_view(request):
    User = get_user_model()
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            # Create General Manager
            new_username = form.cleaned_data.get('new_manager_username')
            new_email = form.cleaned_data.get('new_manager_email')
            new_password = form.cleaned_data.get('new_manager_password')
            
            manager = None # Initialize manager
            if new_username and new_password:
                try:
                    manager = User.objects.create_user(username=new_username, email=new_email, password=new_password, role='manager')
                except Exception as e:
                     messages.error(request, f"Error creating manager: {e}")
                     return redirect('core:admin_dashboard')

            # 2. Create Company
            company = form.save(commit=False)
            if manager:
                company.manager = manager
            company.save()
            
            messages.success(request, f"تم إضافة مطعم {company.name} بنجاح.")
        else:
            messages.error(request, "بيانات غير صحيحة.")
    
    return redirect('core:dashboard')

@user_passes_test(lambda u: u.is_superuser)
def toggle_company_status(request, company_id):
    company = get_object_or_404(RestaurantCompany, pk=company_id)
    company.subscription_status = not company.subscription_status
    company.save()
    status_msg = "تفعيل" if company.subscription_status else "إيقاف"
    messages.success(request, f"تم {status_msg} اشتراك {company.name} بنجاح.")
    return redirect('core:dashboard')

@user_passes_test(lambda u: u.is_superuser)
def client_management_view(request):
     # basic stub to resolve conflict
     return render(request, 'core/dashboard_saas_admin.html')

# --- APIS ---
@login_required # Added from stashed changes
def chart_data_api(request):
    # Retrieve data for charts (Mock or Real)
    labels = ["Yan", "Feb", "Mar", "Apr", "May", "Jun"] # From stashed changes
    data = [10, 20, 15, 25, 20, 30] # Mock data or query DB # From stashed changes
    
    return JsonResponse({ # Combined from both
        'labels': labels,
        'data': data
    })

# --- NEW FEATURES (SMART LAYER) ---

# 1. Integrations Page
def integrations_view(request):
    sync_logs = [
        {'system': 'Foodics', 'action': 'Import Sales', 'status': 'Success', 'time': '2 mins ago', 'details': 'Imported 142 orders'},
        {'system': 'Foodics', 'action': 'Sync Inventory', 'status': 'Success', 'time': '15 mins ago', 'details': 'Updated 23 items'},
        {'system': 'Foodics', 'action': 'Update Menu', 'status': 'Success', 'time': '1 hour ago', 'details': 'No changes found'},
        {'system': 'Moyasar', 'action': 'Subscription Check', 'status': 'Success', 'time': '5 hours ago', 'details': 'Active'},
    ]
    context = {
        'sync_logs': sync_logs,
        'title': 'Integrations'
    }
    return render(request, 'core/integrations.html', context)

# 2. Impersonation (Login As)
@user_passes_test(lambda u: u.is_superuser)
def impersonate_user(request, user_id):
    User = get_user_model()
    original_user_id = request.user.id
    
    try:
        target_user = User.objects.get(id=user_id)
        # Login as target
        from django.contrib.auth import login
        login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')
        
        # Save original ID in session
        request.session['impersonator_id'] = original_user_id
        request.session.save()
        
        messages.warning(request, f"⚠️ تم الدخول بحساب: {target_user.username}")
        return redirect('core:dashboard')
        
    except User.DoesNotExist:
        messages.error(request, "مستخدم غير موجود.")
        return redirect('core:dashboard')

def stop_impersonation(request):
    User = get_user_model()
    impersonator_id = request.session.get('impersonator_id')
    
    if impersonator_id:
        try:
            original_user = User.objects.get(id=impersonator_id)
            from django.contrib.auth import login
            login(request, original_user, backend='django.contrib.auth.backends.ModelBackend')
            
            if 'impersonator_id' in request.session:
                del request.session['impersonator_id']
                
            messages.success(request, "تم العودة لحساب المدير.")
            return redirect('core:dashboard')
        except Exception:
            messages.error(request, "خطأ في استعادة الحساب.")
            
    return redirect('core:dashboard')

# 3. System Logs (Mock Data)
def get_system_logs():
    return [
        {'level': 'ERROR', 'msg': 'PermissionDenied: User Ahmed tried to delete stock item #44', 'time': '2023-10-25 14:30', 'user': 'Ahmed (Manager)'},
        {'level': 'WARNING', 'msg': 'Failed Login Attempt: IP 192.168.1.5', 'time': '2023-10-25 14:25', 'user': 'Anonymous'},
        {'level': 'INFO', 'msg': 'New Company Created: Burger King', 'time': '2023-10-25 12:00', 'user': 'Admin'},
        {'level': 'ERROR', 'msg': 'Foodics Sync Failed: Timeout', 'time': '2023-10-24 09:15', 'user': 'System'},
    ]

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        new_username = request.POST.get('username')
        
        # تحديث اسم المستخدم مع فحص التوفر
        if new_username and new_username != user.username:
            if get_user_model().objects.filter(username=new_username).exists():
                messages.error(request, f"اسم المستخدم '{new_username}' محجوز بالفعل.")
            else:
                user.username = new_username
                user.save()
                messages.success(request, "تم تحديث اسم المستخدم بنجاح.")
        else:
            messages.info(request, "لم يتم إجراء أي تغييرات.")
    
    return redirect(request.META.get('HTTP_REFERER', 'core:dashboard'))
