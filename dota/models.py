from django.db import models
from django.contrib.auth.models import User


class Article(models.Model):
    title = models.CharField(max_length=255) # заголовок поста
    datetime = models.DateTimeField('Дата публикации') # дата публикации
    content = models.TextField(max_length=10000) # текст поста

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    is_approved = models.BooleanField('Пользователь подтверждён', default=False)
