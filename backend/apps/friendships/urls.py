from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FriendshipViewSet

app_name = 'friendships'

router = DefaultRouter()
router.register(r'friends', FriendshipViewSet, basename='friendships')

urlpatterns = [
    path('', include(router.urls))
]
