from django.contrib import admin
from dota.models import UserProfile

from .models import Article
# Register your models here.

admin.site.register(Article)
admin.site.register(UserProfile)
