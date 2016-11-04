from django.shortcuts import render
from django.views import generic

from .models import Article

class ArticlesList(generic.ListView): # представление в виде списка
    model = Article                   # модель для представления

class ArticleDetail(generic.DetailView):
    model = Article

class Index(generic.ListView):
    template_name = 'dota/base.html'

    def get_context_data(self, *args, **kwargs):
        context = super(Index, self).get_context_data(*args, **kwargs)
        if self.request.user.is_authenticated():
            context['is_authenticated'] = True
        else:
            context['is_authenticated'] = False
        return context

    def get_queryset(self):
        return None
