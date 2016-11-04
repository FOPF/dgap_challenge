from django.shortcuts import render

# Create your views here.

from django.views import generic

class Index(generic.ListView):
    template_name = 'index.html'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return [True]
        else:
            return [False]