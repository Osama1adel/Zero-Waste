"""
URL configuration for zero_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# استيراد الـ views المخصصة للإشعارات
from apps.notifications.admin_views import notification_dashboard, send_notification_now

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # صفحة إدارة الإشعارات المخصصة
    path('admin/notifications/dashboard/', notification_dashboard, name='admin_notification_dashboard'),
    path('admin/notifications/send/<int:update_id>/', send_notification_now, name='admin_send_notification_now'),
    
    # استدعاء واحد فقط لتطبيق core مع الـ namespace
    path('', include('apps.core.urls', namespace='core')),
    
    path('inventory/', include('apps.inventory.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('operations/', include('apps.operations.urls')),
    path('auth/', include('apps.authentication.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('ai/', include('apps.ai_engine.urls')),
]

# Force reload
