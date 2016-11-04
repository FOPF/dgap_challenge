from django.contrib import admin
from .models import Article, Team, UserProfile
# Register your models here.

admin.site.register(Article)
admin.site.register(Team)
admin.site.register(UserProfile)
