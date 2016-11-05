from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import logout as auth_logout
import random

from dgap_challenge.settings import MAX_TEAM_SIZE
from .models import Article, Team, UserProfile


class ArticlesList(generic.ListView):
    model = Article


class ArticleDetail(generic.DetailView):
    model = Article


class Index(generic.View):
    def get(self, request):
        return redirect('dota:article_list')
    def post(self, request):
        return redirect('dota:article_list')


class TeamView(generic.View):
    template_name = 'dota/team.html'

    def get_team_info(self, request):
        try:
            team = request.user.userprofile.team
            members = team.get_members()
            free = MAX_TEAM_SIZE - len(members)
            dct = {
                'team': team,
                'members': members,
                'free': free,
            }
        except ObjectDoesNotExist:
            dct = {}
        return render(request, self.template_name, dct)

    def get(self, request, *args, **kwargs):
        return self.get_team_info(request)
    def post(self, request, *args, **kwargs):
        return self.get_team_info(request)



def logout(request):
    messages.success(request, 'Вы вышли из аккаунта')
    auth_logout(request)
    return redirect('index')


def add_profile(backend, user, response, *args, **kwargs):
    if not hasattr(user, 'userprofile'):
        user.userprofile = UserProfile(user=user)
        user.userprofile.save()

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

    teams = Team.objects.filter(invite_key=invite_key).all()
    num_teams = len(teams)
    if num_teams > 1:
        messages.error(request, 'Неизвестная ошибка, напишите, пожалуйста, разработчикам')
        return redirect('dota:team')
    elif num_teams == 0:
        messages.error(request, 'Команды, соответствующей данному ключу, не найдено')
        return redirect('dota:team')
    elif num_teams == 1:
        team = teams[0]
        # TODO Race condition
        num_members = len(team.get_members())
        if num_members < 5:
            user.userprofile.team = team
            user.userprofile.save()
            messages.success(request, 'Вы вступили в команду')

            if user.userprofile.participant:
                user.userprofile.participant = False
                user.userprofile.save()
                messages.info(request, 'Вы отказались от индивидуальной заявки, так как вступили в команду')
            return redirect('dota:index')
        else:
            messages.error(request, 'В этой команде больше нет свободных мест')
            return redirect('dota:team')


def create_team(request):
    user = request.user
    name = request.POST.getlist('name', False)
    if request.method != 'POST':
        return redirect('dota:team')
    if not name:
        messages.error(request, 'Вы не ввели название команды')
        return redirect('dota:team')
    name = name[0]
    if len(Team.objects.filter(name=name)) != 0:
        messages.error(request, 'Команда с таким именем уже существует')
        return redirect('dota:team')

    if user.userprofile.team_id == -1:
        # TODO change int to string
        team = Team.objects.create(invite_key=str(random.randint(0, 10000)), name=name)
        team.save()
        user.userprofile.team_id = team.id
        user.userprofile.captain = 1
        user.userprofile.save()
        messages.success(request, 'Вы создали команду')
        if user.userprofile.participant:
            user.userprofile.participant = False
            user.userprofile.save()
            messages.info(request, 'Вы отказались от индивидуальной заявки, так создали команду')
        return redirect('dota:team')
    else:
        messages.error(request, 'Вы уже в команде')
        return redirect('dota:team')

def refuse(request):
    user = request.user
    if request.method != 'POST':
        return redirect('dota:team')

    if user.userprofile.participant:
        user.userprofile.participant = False
        messages.success(request, 'Вы отказались от индивидуальной заявки')
        return redirect('dota:team')
    else:
        messages.error(request, 'Вы не подавали заявку')
        return redirect('dota:team')


def single_gamer(request):
    user = request.user
    mmr = request.POST.getlist('mmr', False)
    if request.method != 'POST':
        return redirect('dota:team')

    if user.userprofile.team_id == -1:
        # TODO change int to string
        user.userprofile.participant = True
        user.userprofile.save()
        messages.success(request, 'Ваша заявка принята')
        return redirect('dota:team')
    else:
        messages.error(request, 'Вы уже в команде')
        return redirect('dota:team')

def leave_team(request):
    user = request.user
    if request.method != 'POST':
        return redirect('dota:team')
    if user.userprofile.team_id == -1:
        messages.error(request, 'Вы не состоите ни в одной команде')
        return redirect('dota:team')
    team_id = user.userprofile.team_id
    user.userprofile.team_id = -1
    user.userprofile.participant = False
    user.userprofile.save()
    if user.userprofile.captain:
        import random
        members = Team.objects.get(id=team_id).get_members()
        if len(members) != 0:
            new_captain = random.choice(members)
            new_captain.captain = True
            new_captain.save()
        user.userprofile.captain = False
    team = Team.objects.get(id=team_id)
    if len(team.get_members()) == 0:
        team.delete()
    user.userprofile.save()
    messages.success(request, 'Вы вышли из команды')
    return redirect('dota:team')
