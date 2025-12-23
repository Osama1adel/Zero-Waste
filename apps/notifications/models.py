from django.db import models
from django.conf import settings
from django.utils import timezone


class EmailLog(models.Model):
    """سجل جميع الإيميلات المرسلة من النظام"""
    
    EMAIL_TYPES = [
        ('welcome', 'إيميل ترحيب'),
        ('activation', 'تفعيل الحساب'),
        ('password_reset', 'إعادة تعيين كلمة المرور'),
        ('system_update', 'تحديث النظام'),
        ('other', 'أخرى'),
    ]
    
    recipient = models.EmailField(verbose_name="المستلم")
    email_type = models.CharField(max_length=50, choices=EMAIL_TYPES, verbose_name="نوع الإيميل")
    subject = models.CharField(max_length=200, verbose_name="الموضوع")
    body = models.TextField(verbose_name="المحتوى")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    is_sent = models.BooleanField(default=False, verbose_name="تم الإرسال؟")
    error_message = models.TextField(blank=True, null=True, verbose_name="رسالة الخطأ")
    
    class Meta:
        verbose_name = "سجل إيميل"
        verbose_name_plural = "سجلات الإيميلات"
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.get_email_type_display()} - {self.recipient}"


class SystemUpdate(models.Model):
    """إشعارات تحديثات النظام من الأدمن"""
    
    title = models.CharField(max_length=200, verbose_name="عنوان الإشعار")
    message = models.TextField(verbose_name="نص الإشعار")
    scheduled_time = models.DateTimeField(verbose_name="موعد التحديث", null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="أنشأه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    is_sent = models.BooleanField(default=False, verbose_name="تم الإرسال؟")
    send_email = models.BooleanField(default=True, verbose_name="إرسال إيميل؟")
    send_notification = models.BooleanField(default=True, verbose_name="إرسال إشعار داخلي؟")
    
    # حقول جديدة للاستهداف الانتقائي
    target_type = models.CharField(
        max_length=20,
        choices=[
            ('all', 'جميع المستخدمين'),
            ('managers', 'المدراء فقط'),
            ('selected', 'مستخدمين محددين'),
        ],
        default='managers',
        verbose_name="نوع الاستهداف"
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='targeted_updates',
        verbose_name="المستخدمين المستهدفين"
    )
    
    class Meta:
        verbose_name = "تحديث النظام"
        verbose_name_plural = "تحديثات النظام"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"


class UserNotification(models.Model):
    """الإشعارات الداخلية للمستخدمين"""
    
    NOTIFICATION_TYPES = [
        ('system_update', 'تحديث النظام'),
        ('welcome', 'ترحيب'),
        ('alert', 'تنبيه'),
        ('info', 'معلومة'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="المستخدم"
    )
    title = models.CharField(max_length=200, verbose_name="العنوان")
    message = models.TextField(verbose_name="الرسالة")
    notification_type = models.CharField(
        max_length=50, 
        choices=NOTIFICATION_TYPES,
        default='info',
        verbose_name="نوع الإشعار"
    )
    is_read = models.BooleanField(default=False, verbose_name="مقروء؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    related_update = models.ForeignKey(
        SystemUpdate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="التحديث المرتبط"
    )
    
    class Meta:
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"
        ordering = ['-created_at']
    
    def __str__(self):
        status = "✓" if self.is_read else "●"
        return f"{status} {self.title} - {self.user.username}"
