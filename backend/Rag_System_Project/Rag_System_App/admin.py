from django.contrib import admin
from .models import User, File, FaissFile


# Register your models here.
admin.site.register(User)
admin.site.register(File)
admin.site.register(FaissFile)