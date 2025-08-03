from django.urls import path
from api.views import (
    LoginView,
    ExperimentUploadView,
    ExperimentListView,
    ExperimentDetailView,
    UpdateObjectLabelView,
    ClipDeleteView
)

urlpatterns = [
    # Autenticación
    path('auth/login/', LoginView.as_view(), name='login'),
    
    # Endpoints de Experimentos
    path('experiments/', ExperimentUploadView.as_view(), name='experiment-upload'),
    path('experiments/list/', ExperimentListView.as_view(), name='experiment-list'),
    path('experiments/<int:pk>/', ExperimentDetailView.as_view(), name='experiment-detail'),
    path('experiments/<int:pk>/update-label/', UpdateObjectLabelView.as_view(), name='update-label'),
    
    # Endpoints de Clips
    path('experiments/<int:experiment_id>/clips/delete/', ClipDeleteView.as_view(), name='delete-clips'),
]