from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import Notification, NotificationPreference
from .serializers import (
    NotificationCreateSerializer, 
    NotificationSerializer,
    NotificationPreferenceSerializer
)

class NotificatonPagination(PageNumberPagination):
    """Paginate notification"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificatonPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user).select_related(
            'sender', 'recipient', 'content_type'
        )

        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        return queryset
    

class NotificationCreateView(generics.CreateAPIView):
    serializer_class = NotificationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Auto-set sender to current user if not provided
        if not serializer.validated_data.get('sender'):
            serializer.save(sender=self.request.user)
        serializer.save()


class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, pk):
    notification = get_object_or_404(
        Notification, 
        pk=pk, 
        recipient=request.user
    )
    notification.mark_as_read()
    return Response({'status': 'notification marked as read'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_seen(request, pk):
    notification = get_object_or_404(
        Notification, 
        pk=pk, 
        recipient=request.user
    )
    notification.mark_as_seen()
    return Response({'status': 'notification marked as seen'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    updated_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True, updated_at=timezone.now())
    
    return Response({
        'status': 'all notifications marked as read',
        'updated_count': updated_count
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_seen(request):
    updated_count = Notification.objects.filter(
        recipient=request.user,
        is_seen=False
    ).update(is_seen=True, updated_at=timezone.now())
    
    return Response({
        'status': 'all notifications marked as seen',
        'updated_count': updated_count
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_counts(request):
    user = request.user
    total_count = Notification.objects.filter(recipient=user).count()
    unread_count = Notification.objects.filter(
        recipient=user, 
        is_read=False
    ).count()
    unseen_count = Notification.objects.filter(
        recipient=user, 
        is_seen=False
    ).count()
    
    return Response({
        'total_count': total_count,
        'unread_count': unread_count,
        'unseen_count': unseen_count
    })


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preferences
