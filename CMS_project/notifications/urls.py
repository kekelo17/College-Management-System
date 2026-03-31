from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification
    path('', views.notification_list, name='notification_list'),
    path('create/', views.notification_create, name='notification_create'),
    path('<int:pk>/', views.notification_detail, name='notification_detail'),
    path('<int:pk>/update/', views.notification_update, name='notification_update'),
    path('<int:pk>/delete/', views.notification_delete, name='notification_delete'),
    
    # Announcement
    path('announcement/', views.announcement_list, name='announcement_list'),
    path('announcement/create/', views.announcement_create, name='announcement_create'),
    path('announcement/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcement/<int:pk>/update/', views.announcement_update, name='announcement_update'),
    
    # Messages
    path('message/', views.message_list, name='message_list'),
    path('message/send/', views.message_send, name='message_send'),
    path('message/<int:pk>/', views.message_detail, name='message_detail'),
    
    # User Notifications
    path('my/', views.my_notifications, name='my_notifications'),
    path('mark-read/<int:pk>/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]
