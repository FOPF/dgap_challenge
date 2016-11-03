from django.shortcuts import render
from django.views import generic

from .models import Article

class ArticlesList(generic.ListView): # представление в виде списка
    model = Article                   # модель для представления

class ArticleDetail(generic.DetailView):
    model = Article

