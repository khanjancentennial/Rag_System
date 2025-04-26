from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Custom User model extending Django's built-in User"""
    
    # Add unique `related_name` to avoid clashes
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="Rag_System_App_users",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="Rag_System_App_user_permissions",
        blank=True
    )

    def __str__(self):
        return self.username

class File(models.Model):
    """Model to store uploaded files and FAISS index"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link file to user
    file_path = models.FileField(upload_to='uploaded_files/')  # File storage path
    file_name = models.CharField(max_length=255)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name}"
    
class FaissFile(models.Model):
    """Model to store FAISS index linked to an uploaded file"""
    faiss_index_path = models.CharField(max_length=255, blank=True, null=True)  # Path to FAISS index
    index_id = models.CharField(max_length=100, blank=True, null=True)  # FAISS index ID

    def __str__(self):
        return f"{self.faiss_index_path}"
