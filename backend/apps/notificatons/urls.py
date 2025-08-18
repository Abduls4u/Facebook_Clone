from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('create/', views.NotificationCreateView.as_view(), name='notification-create'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/read/', views.mark_notification_read, name='mark-read'),
    path('<int:pk>/seen/', views.mark_notification_seen, name='mark-seen'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark-all-read'),
    path('mark-all-seen/', views.mark_all_notifications_seen, name='mark-all-seen'),
    path('counts/', views.notification_counts, name='notification-counts'),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),
]