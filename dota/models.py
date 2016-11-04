from django.db import models
from django.contrib.auth.models import User


class Article(models.Model):
    title = models.CharField(max_length=255) # заголовок поста
    datetime = models.DateTimeField('Дата публикации') # дата публикации
    content = models.TextField(max_length=10000) # текст поста

    def __str__(self):
        return self.title

class Team(models.Model):
    name = models.CharField('Название', max_length=40, default='')
    invite_key = models.CharField('Ключ для приглашения', max_length=50, default='')

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, default=None)
    is_approved = models.BooleanField('Пользователь подтверждён', default=False)
    team = models.ForeignKey(Team, default=-1)
    captain = models.BooleanField('Капитан', default=False)
    mmr = models.IntegerField('MMR', default=0)

    def __sts__(self):
        return self.user.first_name + self.user.last_name