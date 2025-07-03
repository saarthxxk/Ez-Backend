from django.urls import path
from .views import SignupView, VerifyEmailView, LoginView
from .views import FileUploadView
from .views import FileListView
from .views import GenerateDownloadLinkView
from .views import SecureDownloadView


urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('upload/', FileUploadView.as_view(), name='upload-file'),
    path('files/', FileListView.as_view(), name='file-list'),
    path('download-file/<int:file_id>/', GenerateDownloadLinkView.as_view(), name='generate-download-link'),
    path('secure-download/<str:token>/', SecureDownloadView.as_view(), name='secure-download'),

]
