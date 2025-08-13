from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserListSerializer,
    LoginSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate Tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)
    
class LoginView(generics.GenericAPIView):
    """User login endpoint"""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]


    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Update online status
        user.is_online = True
        user.save(update_fields=['is_online', 'last_seen'])

        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_202_ACCEPTED)
    

class ProfileView(generics.RetrieveUpdateAPIView):
    """View and update a profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    

class UserListView(generics.ListAPIView):
    """List all users (for testing purposes only)"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    "Logs out the user"
    try:
        # Update online status
        request.user.is_online = False
        request.user.save(update_fields=['is_online', 'last_seen'])

        return Response({'message': 'Logged out successfully ☺️'})
    except Exception as error:
        return Response({'Error': str(error)}, status=status.HTTP_400_BAD_REQUEST)