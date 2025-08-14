from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, permissions
from api.serializers import LoginSerializer, UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginView(TokenObtainPairView):
    """Endpoint para autenticación (POST)"""
    serializer_class = LoginSerializer

class UserCreateView(generics.CreateAPIView):
    """Endpoint para creación de usuarios (POST)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Permite registro sin autenticación