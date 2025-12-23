from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('detail/<int:notification_id>/', views.notification_detail, name='detail'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
    path('delete-redirect/<int:notification_id>/', views.delete_notification_view, name='delete_notification_redirect'),
]
