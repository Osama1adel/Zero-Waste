from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from .models import EmailLog, UserNotification
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """
    إرسال إيميل ترحيب للمستخدم الجديد
    
    Args:
        user: كائن المستخدم الذي تم إنشاؤه
    
    Returns:
        bool: True إذا تم الإرسال بنجاح، False إذا فشل
    """
    try:
        subject = f"مرحباً بك في نظام Zero Waste، {user.get_full_name() or user.username}!"
        
        # سياق البيانات للقالب
        context = {
            'user': user,
            'role_display': user.get_role_display(),
            'login_url': f"{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'}/login/",
        }
        
        # تحميل القالب HTML
        html_message = render_to_string('notifications/emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        # إنشاء الإيميل
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_message, "text/html")
        
        # إرسال الإيميل
        email.send()
        
        # تسجيل في قاعدة البيانات
        EmailLog.objects.create(
            recipient=user.email,
            email_type='welcome',
            subject=subject,
            body=plain_message,
            is_sent=True
        )
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        EmailLog.objects.create(
            recipient=user.email,
            email_type='welcome',
            subject=subject if 'subject' in locals() else 'Welcome Email',
            body='',
            is_sent=False,
            error_message=str(e)
        )
        return False


def send_password_reset_email(user, reset_url):
    """
    إرسال إيميل إعادة تعيين كلمة المرور
    
    Args:
        user: كائن المستخدم
        reset_url: رابط إعادة تعيين كلمة المرور
    
    Returns:
        bool: True إذا تم الإرسال بنجاح
    """
    try:
        subject = "إعادة تعيين كلمة المرور - Zero Waste"
        
        context = {
            'user': user,
            'reset_url': reset_url,
        }
        
        html_message = render_to_string('notifications/emails/password_reset.html', context)
        plain_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        EmailLog.objects.create(
            recipient=user.email,
            email_type='password_reset',
            subject=subject,
            body=plain_message,
            is_sent=True
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return False


def send_system_update_notification(update):
    """
    إرسال إشعار تحديث النظام للمستخدمين المستهدفين
    
    Args:
        update: كائن SystemUpdate
    
    Returns:
        int: عدد الإيميلات المرسلة بنجاح
    """
    from apps.authentication.models import User
    
    # تحديد المستخدمين المستهدفين بناءً على نوع الاستهداف
    if update.target_type == 'all':
        # جميع المستخدمين
        target_users = User.objects.all()
    elif update.target_type == 'managers':
        # المدراء فقط (General Manager و Branch Manager)
        target_users = User.objects.filter(role__in=['manager', 'branch_manager'])
    else:  # selected
        # مستخدمين محددين
        target_users = update.target_users.all()
    
    sent_count = 0
    
    if not target_users.exists():
        logger.warning(f"No target users found for system update: {update.title}")
        update.is_sent = True # Mark as 'processed' even if no one got it, to avoid re-sending attempts? Or maybe not. 
        # Actually better to just return 0 and let the view handle it.
        update.save()
        return 0

    for user in target_users:
        user_reached = False
        try:
            # إرسال إيميل إذا كان مفعّل
            if update.send_email and user.email:
                subject = f"تحديث النظام: {update.title}"
                
                context = {
                    'user': user,
                    'update': update,
                }
                
                html_message = render_to_string('notifications/emails/system_update.html', context)
                plain_message = strip_tags(html_message)
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
                
                EmailLog.objects.create(
                    recipient=user.email,
                    email_type='system_update',
                    subject=subject,
                    body=plain_message,
                    is_sent=True
                )
                user_reached = True
            
            # إنشاء إشعار داخلي إذا كان مفعّل
            if update.send_notification:
                create_in_app_notification(
                    user=user,
                    title=update.title,
                    message=update.message,
                    notification_type='system_update',
                    related_update=update
                )
                user_reached = True
                
            if user_reached:
                sent_count += 1
        
        except Exception as e:
            logger.error(f"Failed to send update notification to {user.email if user.email else user.username}: {str(e)}")
            continue
    
    # تحديث حالة الإرسال
    update.is_sent = True
    update.save()
    
    logger.info(f"System update notification sent to {sent_count} users (target_type: {update.target_type})")
    return sent_count


def create_in_app_notification(user, title, message, notification_type='info', related_update=None):
    """
    إنشاء إشعار داخلي للمستخدم
    
    Args:
        user: كائن المستخدم
        title: عنوان الإشعار
        message: نص الإشعار
        notification_type: نوع الإشعار
        related_update: التحديث المرتبط (اختياري)
    
    Returns:
        UserNotification: كائن الإشعار المنشأ
    """
    notification = UserNotification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_update=related_update
    )
    
    logger.info(f"In-app notification created for {user.username}: {title}")
    return notification


def mark_notification_as_read(notification_id, user):
    """
    تحديد إشعار كمقروء
    
    Args:
        notification_id: معرّف الإشعار
        user: المستخدم (للتحقق من الصلاحية)
    
    Returns:
        bool: True إذا تم التحديث بنجاح
    """
    try:
        notification = UserNotification.objects.get(id=notification_id, user=user)
        notification.is_read = True
        notification.save()
        return True
    except UserNotification.DoesNotExist:
        return False


def get_unread_notifications_count(user):
    """
    الحصول على عدد الإشعارات غير المقروءة للمستخدم
    
    Args:
        user: كائن المستخدم
    
    Returns:
        int: عدد الإشعارات غير المقروءة
    """
    return UserNotification.objects.filter(user=user, is_read=False).count()
