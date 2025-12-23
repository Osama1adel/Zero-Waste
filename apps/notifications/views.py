from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import UserNotification
from .utils import mark_notification_as_read, get_unread_notifications_count


@login_required(login_url='login')
def mark_notification_read(request, notification_id):
    """تحديد إشعار كمقروء عبر AJAX"""
    if request.method == 'POST':
        success = mark_notification_as_read(notification_id, request.user)
        return JsonResponse({'success': success})
    return JsonResponse({'success': False}, status=400)


@login_required(login_url='login')
def get_unread_count(request):
    """الحصول على عدد الإشعارات غير المقروءة"""
    count = get_unread_notifications_count(request.user)
    return JsonResponse({'count': count})


@login_required(login_url='login')
def notification_detail(request, notification_id):
    """عرض تفاصيل الإشعار بالكامل"""
    notification = get_object_or_404(
        UserNotification, 
        id=notification_id, 
        user=request.user
    )
    
    # تحديد كمقروء تلقائياً عند فتح التفاصيل
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    return render(request, 'notifications/detail.html', {
        'notification': notification
    })


@login_required(login_url='login')
def delete_notification(request, notification_id):
    """حذف إشعار معين"""
    if request.method == 'POST':
        try:
            notification = get_object_or_404(
                UserNotification,
                id=notification_id,
                user=request.user
            )
            notification.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required(login_url='login')
def delete_notification_view(request, notification_id):
    """حذف إشعار مع إعادة التوجيه (للطلبات العادية)"""
    if request.method == 'POST':
        try:
            notification = get_object_or_404(
                UserNotification,
                id=notification_id,
                user=request.user
            )
            notification.delete()
            # يمكن إضافة رسالة نجاح هنا إذا لزم الأمر
            # messages.success(request, 'تم حذف الإشعار')
        except Exception:
            pass # تجاهل الأخطاء عند الحذف وإعادة التوجيه
            
    return redirect(request.META.get('HTTP_REFERER', 'core:dashboard'))
