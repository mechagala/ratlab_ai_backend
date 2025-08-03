from rest_framework_simplejwt.views import TokenObtainPairView
from api.serializers import LoginSerializer

class LoginView(TokenObtainPairView):
    """Endpoint para autenticación (POST)"""
    serializer_class = LoginSerializer