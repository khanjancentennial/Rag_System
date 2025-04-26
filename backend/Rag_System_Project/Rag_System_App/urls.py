from django.urls import path
from .views import UploadMultipleFilesView, RegisterView, LoginView, RefreshTokenView, UpdateFileView, QueryVectorDBView,DeleteFileView, GetAllFilesView

urlpatterns = [
    path('upload/', UploadMultipleFilesView.as_view(), name='upload-file'),
    path("all-files/", GetAllFilesView.as_view(), name="all_files"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path('update-file/<int:file_id>/', UpdateFileView.as_view(),name='update-file'),
    path("query/", QueryVectorDBView.as_view(), name="query_vector_db"),
    path('delete-file/<int:file_id>/', DeleteFileView.as_view(), name='delete-file'),

]
