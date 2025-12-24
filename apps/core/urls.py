# apps/core/urls.py
from django.urls import path
from . import views
from .admin_notifications_views import admin_notifications_dashboard, send_notification_now
from .saas_notifications_views import saas_notifications_center, send_saved_notification

app_name = 'core'

urlpatterns = [
    path('', views.landing_page, name='landing'), # الرابط الرئيسي (Router)
    path('dashboard/', views.dashboard_router, name='dashboard'), # الرابط الرئيسي (Router)
    path('company/add/', views.add_company_view, name='add_company'), # رابط إضافة شركة
    path('api/chart-data/', views.chart_data_api, name='chart_data_api'),
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/add/', views.add_branch_view, name='add_branch'), # رابط إضافة فرع
    path('integrations/', views.integrations_view, name='integrations'),
    path('impersonate/<int:user_id>/', views.impersonate_user, name='impersonate_user'),
    path('impersonate/stop/', views.stop_impersonation, name='stop_impersonation'),
    path('company/<int:company_id>/toggle-status/', views.toggle_company_status, name='toggle_company_status'),
    
    # صفحة إدارة الإشعارات (للمدراء)
    path('admin/notifications/', admin_notifications_dashboard, name='admin_notifications'),
    path('admin/notifications/send/<int:update_id>/', send_notification_now, name='send_notification_now'),
    
    # مركز الإشعارات الشامل (للسوبر أدمن في SaaS Dashboard)
    path('saas/notifications/', saas_notifications_center, name='saas_notifications'),
    path('saas/notifications/send/<int:update_id>/', send_saved_notification, name='send_saved_notification'),

    # إعدادات الحساب
    path('profile/update/', views.update_profile, name='update_profile'),
]





   
