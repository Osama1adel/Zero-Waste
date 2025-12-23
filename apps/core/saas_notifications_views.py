from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from apps.notifications.models import SystemUpdate, UserNotification, EmailLog
from apps.notifications.utils import send_system_update_notification
from apps.authentication.models import User


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def saas_notifications_center(request):
    """
    مركز إدارة الإشعارات الشامل للسوبر أدمن في SaaS Dashboard
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_notification':
            # إنشاء وإرسال إشعار جديد
            title = request.POST.get('title')
            message = request.POST.get('message')
            scheduled_time = request.POST.get('scheduled_time')
            send_email = request.POST.get('send_email') == 'on'
            send_notification = request.POST.get('send_notification') == 'on'
            send_now = request.POST.get('send_now') == 'on'
            target_type = request.POST.get('target_type', 'managers')
            selected_users = request.POST.getlist('selected_users')
            
            if title and message:
                # معالجة التاريخ الفارغ
                if not scheduled_time:
                    if send_now:
                        scheduled_time = timezone.now()
                    else:
                        scheduled_time = None

                update = SystemUpdate.objects.create(
                    title=title,
                    message=message,
                    scheduled_time=scheduled_time,
                    created_by=request.user,
                    send_email=send_email,
                    send_notification=send_notification,
                    target_type=target_type
                )
                
                if target_type == 'selected' and selected_users:
                    update.target_users.set(selected_users)
                
                if send_now:
                    count = send_system_update_notification(update)
                    messages.success(request, f'✅ تم إرسال الإشعار بنجاح إلى {count} مستخدم')
                else:
                    messages.success(request, '✅ تم حفظ الإشعار بنجاح')
                
                return redirect('core:saas_notifications')
    
    # إحصائيات
    stats = {
        'total_notifications': UserNotification.objects.count(),
        'unread_notifications': UserNotification.objects.filter(is_read=False).count(),
        'total_emails': EmailLog.objects.count(),
        'successful_emails': EmailLog.objects.filter(is_sent=True).count(),
        'failed_emails': EmailLog.objects.filter(is_sent=False).count(),
        'pending_updates': SystemUpdate.objects.filter(is_sent=False).count(),
        'total_users': User.objects.count(),
        'total_managers': User.objects.filter(role='manager').count(),
        'total_branch_managers': User.objects.filter(role='branch_manager').count(),
    }
    
    # آخر الإشعارات المرسلة
    recent_updates = SystemUpdate.objects.all().order_by('-created_at')[:10]
    
    # آخر الإيميلات
    recent_emails = EmailLog.objects.all().order_by('-sent_at')[:15]
    
    # جميع المستخدمين للاختيار
    all_users = User.objects.all().order_by('username')
    managers = User.objects.filter(role__in=['manager', 'branch_manager']).order_by('username')
    
    # طلبات الدعم (Mock - يمكن إضافة موديل Support Ticket لاحقاً)
    support_tickets = []
    
    context = {
        'stats': stats,
        'recent_updates': recent_updates,
        'recent_emails': recent_emails,
        'all_users': all_users,
        'managers': managers,
        'support_tickets': support_tickets,
        'unread_notifications_count': stats['unread_notifications'], # Added for compatibility
    }
    
    return render(request, 'core/saas_notifications_center.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def send_saved_notification(request, update_id):
    """إرسال إشعار محفوظ"""
    if request.method == 'POST':
        try:
            update = SystemUpdate.objects.get(id=update_id)
            count = send_system_update_notification(update)
            messages.success(request, f'✅ تم إرسال الإشعار بنجاح إلى {count} مستخدم')
        except SystemUpdate.DoesNotExist:
            messages.error(request, '❌ الإشعار غير موجود')
    
    return redirect('core:saas_notifications')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def delete_system_update(request, update_id):
    """حذف إشعار نظام"""
    if request.method == 'POST':
        try:
            update = SystemUpdate.objects.get(id=update_id)
            update.delete()
            messages.success(request, '✅ تم حذف الإشعار بنجاح')
        except SystemUpdate.DoesNotExist:
            messages.error(request, '❌ الإشعار غير موجود')
    
    return redirect('core:saas_notifications')
