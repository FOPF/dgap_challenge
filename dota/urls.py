from django.conf.urls import url
from dota import views
from django.contrib import admin

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index')
    # url(r'^/team/', name="my_team"),
]
