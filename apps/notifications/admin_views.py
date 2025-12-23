from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from .models import SystemUpdate, UserNotification, EmailLog
from .utils import send_system_update_notification
from apps.authentication.models import User


@staff_member_required
def notification_dashboard(request):
    """
    صفحة إدارة الإشعارات للأدمن
    """
    if request.method == 'POST':
        # إنشاء إشعار جديد
        title = request.POST.get('title')
        message = request.POST.get('message')
        scheduled_time = request.POST.get('scheduled_time')
        send_email = request.POST.get('send_email') == 'on'
        send_notification = request.POST.get('send_notification') == 'on'
        send_now = request.POST.get('send_now') == 'on'
        
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
                send_notification=send_notification
            )
            
            # إرسال فوراً إذا تم تحديد الخيار
            if send_now:
                count = send_system_update_notification(update)
                if count > 0:
                    messages.success(request, f'✅ تم إرسال الإشعار بنجاح إلى {count} مستخدم')
                else:
                    messages.warning(request, '⚠️ لم يتم إرسال الإشعار لأي مستخدم. تأكد من وجود مستخدمين مستهدفين وتفعيل خيارات الإرسال.')
            else:
                messages.success(request, '✅ تم حفظ الإشعار بنجاح. يمكنك إرساله لاحقاً.')
            
            return redirect('admin_notification_dashboard')
    
    # إحصائيات
    total_notifications = UserNotification.objects.count()
    unread_notifications = UserNotification.objects.filter(is_read=False).count()
    total_emails = EmailLog.objects.count()
    successful_emails = EmailLog.objects.filter(is_sent=True).count()
    pending_updates = SystemUpdate.objects.filter(is_sent=False).count()
    
    # آخر الإشعارات المرسلة
    recent_updates = SystemUpdate.objects.all().order_by('-created_at')[:10]
    
    # آخر الإيميلات
    recent_emails = EmailLog.objects.all().order_by('-sent_at')[:10]
    
    # عدد المدراء
    managers_count = User.objects.filter(role__in=['manager', 'branch_manager']).count()
    
    context = {
        'title': 'إدارة الإشعارات والإيميلات',
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'total_emails': total_emails,
        'successful_emails': successful_emails,
        'pending_updates': pending_updates,
        'recent_updates': recent_updates,
        'recent_emails': recent_emails,
        'managers_count': managers_count,
    }
    
    return render(request, 'admin/notifications/dashboard.html', context)


@staff_member_required
def send_notification_now(request, update_id):
    """إرسال إشعار محفوظ"""
    if request.method == 'POST':
        try:
            update = SystemUpdate.objects.get(id=update_id)
            count = send_system_update_notification(update)
            if count > 0:
                messages.success(request, f'✅ تم إرسال الإشعار بنجاح إلى {count} مستخدم')
            else:
                messages.warning(request, '⚠️ لم يتم إرسال الإشعار لأي مستخدم.')
        except SystemUpdate.DoesNotExist:
            messages.error(request, '❌ الإشعار غير موجود')
    
    return redirect('admin_notification_dashboard')
