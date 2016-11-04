from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    is_approved = models.BooleanField('Пользователь подтверждён', default=False)
