from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import generic
from dota.models import Team

from .models import Article


class ArticlesList(generic.ListView): # представление в виде списка
    model = Article                   # модель для представления


class ArticleDetail(generic.DetailView):
    model = Article


class Index(generic.TemplateView):
    pass



class TeamView(generic.TemplateView):
    @property
    def get_members(self):
        pass


def join(request):
    user = request.user
    if request.method != 'POST':
        return redirect('dota:team')
    if not user.is_authenticated():
        messages.error(request, 'Вы не вошли как зарегистрированный пользователь')
        return redirect('dota:team')
    invite_key = request.POST.getlist('invite_key', False)
    if not invite_key:
        messages.error(request, 'Вы ввели пустой ключ')
        return redirect('dota:team')
    invite_key = invite_key[0]

    team = Team.objects.filter(invite_key=invite_key).all()
    len_team = len(team)
    if len_team > 1:
        messages.error(request, 'Неизвестная ошибка, напишите, пожалуйста, разработчикам')
        return redirect('dota:team')
    elif len_team == 0:
        messages.info(request, 'Команды, соответствующей данному ключу, не найдено')
        return redirect('dota:team')
    elif len_team == 1:
        # TODO Race condition
        if not hasattr(team[0], 'user'):
            number_of_member = 0
        else:
            number_of_member = team[0].user.objects.count()
        if number_of_member < 5:
            user.userprofile.team_id = team[0].id
            user.userprofile.save()
            messages.success(request, 'Вы вступили в команду')
            return redirect('dota:index')
        else:
            messages.error(request, 'В этой команде больше нет свободных мест')
            return redirect('dota:team')