from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from dota import views
from django.contrib import admin
from django.views.generic import TemplateView
from dota import views


urlpatterns = [
    url(r'^$', views.Index.as_view(), name="index"),
    # url(r'^team/$', views.Team.as_view(), name="my_team"),
    # url(r'^live/$', views.Live.as_view(), name="live"),
    # url(r'^tournament/$', views.Tournament.as_view(), name="tournament"),
    url(r'^news/$', views.ArticlesList.as_view(), name="article_list"),
    url(r'^news/(?P<pk>\d+)/$', views.ArticleDetail.as_view(), name="article_detail"),
    url(r'^live/$', TemplateView.as_view(template_name="dota/live.html"), name="live"),
    url(r'^tournament/$', TemplateView.as_view(template_name="dota/tournament.html"), name="tournament"),
    url(r'^team/$', login_required(views.TeamView.as_view()), name="team"),
    url(r'^join/$', login_required(views.join), name="join"),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^create_team/$', login_required(views.create_team), name="create_team"),
    url(r'^single_gamer$', login_required(views.single_gamer), name="single_gamer"),
]
