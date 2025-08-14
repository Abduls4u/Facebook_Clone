from django.urls import include, path
from .views import get_likes, toggle_like, check_user_reaction

app_name = 'likes'

urlpatterns = [
    path(
        'like/<str:content_type>/<int:object_id>/',
        toggle_like,
        name='toggle_like'
    ),
    path(
        'likes/<str:content_type>/<int:object_id>/',
        get_likes,
        name='get_likes'
    ),
    path(
        'check/<str:content_type>/<int:object_id>/',
        check_user_reaction,
        name='check_reaction'
    ),
]
