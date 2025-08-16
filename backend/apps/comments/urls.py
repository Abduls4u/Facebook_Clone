from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet

# We'll use nested routing for comments under posts
app_name = 'comments'

urlpatterns = [
    path(
        'posts/<int:post_id>/comments/', 
        CommentViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }), 
        name='post_comments'
    ),
    path(
        'posts/<int:post_id>/comments/<int:pk>/', 
        CommentViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), 
        name='comment_detail'
    ),
    path(
        'posts/<int:post_id>/comments/<int:pk>/replies/', 
        CommentViewSet.as_view({'get': 'replies'}), 
        name='comment_replies'
    ),
]