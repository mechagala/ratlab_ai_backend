from .auth_view import LoginView
from .experiment_view import (
    ExperimentUploadView,
    ExperimentListView,
    ExperimentDetailView,
    UpdateObjectLabelView
)
from .clip_view import ClipDeleteView
from .auth_view import (UserCreateView, LoginView)  # Asegúrate de que tu vista de creación de usuario esté importada

__all__ = [
    'UserCreateView',
    'LoginView',
    'ExperimentUploadView',
    'ExperimentListView',
    'ExperimentDetailView',
    'UpdateObjectLabelView',
    'ClipDeleteView'
]