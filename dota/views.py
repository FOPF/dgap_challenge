from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import logout as auth_logout
import random
from datetime import datetime
from functools import reduce
from pandas import DataFrame, Series

from dgap_challenge.settings import MAX_TEAM_SIZE
from .models import Article, Team, UserProfile, Tournament, TournamentRound, TournamentGame
from dgap_challenge.settings import END_TIME_REGISTRATION
from django.db.models import Q


def _tournament_results(tournament):
    teams = tournament.teams.all()  # participants
    rounds = TournamentRound.objects
    data = DataFrame(index=[team.name for team in teams],
                     columns=[str(round.num) + ' тур' for round in rounds.filter(~Q(name='Финал'))])
    rounds = rounds.filter(state__in=[TournamentRound.FINISHED, TournamentRound.CANCELLED,
                                      TournamentRound.STARTED])
    last_score = {}
    for team in teams:
        for round in rounds:
            try:
                tournamentgame = round.tournamentgame_set.filter(Q(team1=team) | Q(team2=team)).first()
            except ObjectDoesNotExist:
                continue
            if not tournamentgame:
                continue
            # TODO if either try. We need only one

            if not tournamentgame.winner:
                continue
            else:
                score = len(round.tournamentgame_set.filter(winner=team)) + last_score.get(team.name, 0)
            data.loc[team.name, str(round.num) + ' тур'] = score
            last_score[team.name] = score
    return data

class ArticlesList(generic.ListView):
    model = Article
    queryset = model.objects.filter(datetime__lte=datetime.now).order_by('-datetime')


class ArticleDetail(generic.DetailView):
    model = Article


class Index(generic.View):
    def get(self, request):
        return redirect('dota:article_list')
    def post(self, request):
        return redirect('dota:article_list')


class TournamentView(generic.View):
    def get(self, request, *args, **kwargs):
        dct = {}
        if datetime.now() > END_TIME_REGISTRATION:
            template_name = "dota/draw.html"
            dct = {
                'round_list': TournamentRound.objects.all().order_by('-num')
            }
            table = _tournament_results(Tournament.objects.first())
            if len(table) > 0:
                dct['table'] = True
                dct['table_html'] = table.to_html(classes="table", na_rep='', border='0')
        else:
            template_name = "dota/tournament.html"
            dct = {
                'day': END_TIME_REGISTRATION.day,
                'month': END_TIME_REGISTRATION.strftime('%H'), # TODO Problem with localization
                'hour': END_TIME_REGISTRATION.strftime('%H'),
                'minute': END_TIME_REGISTRATION.strftime('%M')
            }
        return render(request, template_name, dct)


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
            if datetime.now() > END_TIME_REGISTRATION:
                dct['finished_registration'] = True
            else:
                dct['finished_registration'] = False
        return render(request, self.template_name, dct)

    def get(self, request, *args, **kwargs):
        return self.get_team_info(request)
    def post(self, request, *args, **kwargs):
        return self.get_team_info(request)


class Choose_new_name(generic.View):
    template_name = 'dota/choose_new_name.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.userprofile.team_id == -1:
            messages.error(request, "Вы не вступили ни в одну из команд")
            return redirect('dota:team')
        elif not user.userprofile.captain:
            messages.error(request, "Вы не можете изменять название команды, так как не являетесь капитаном")
            return redirect('dota:team')
        else:
            dct = {
                'team': user.userprofile.team
            }
            return render(request, self.template_name, dct)




def round_list(request):
    rounds = TournamentRound.objects.prefetch_related('tournamentgame_set').all().order_by('-start_dttm')
    return render(request, 'dota/draw.html', {'round_list': rounds})


def logout(request):
    messages.success(request, 'Вы вышли из аккаунта')
    auth_logout(request)
    return redirect('index')


def add_profile(backend, user, response, *args, **kwargs):
    if not hasattr(user, 'userprofile'):
        user.userprofile = UserProfile(user=user)
        user.userprofile.save()


def _leave_team(user):
    team = user.userprofile.team
    user.userprofile.team_id = -1
    user.userprofile.participant = False
    user.userprofile.save()
    if user.userprofile.captain:
        import random
        members = team.get_members()
        if len(members) != 0:
            new_captain = random.choice(members)
            new_captain.captain = True
            new_captain.save()
        user.userprofile.captain = False
    user.userprofile.save()
    if len(team.get_members()) == 0:
        team.delete()
    return user.userprofile


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

        if user.userprofile.team_id == team.id:
            messages.error(request, 'Вы уже вступили в эту команду')
            return redirect('dota:team')

        if user.userprofile.team_id != -1:
            user.userprofile = _leave_team(user)

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
            return redirect('dota:team')
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
        team = Team.objects.create(invite_key=str(random.randint(0, 9999)), name=name)
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
        user.userprofile.save()
        messages.success(request, 'Вы отказались от индивидуальной заявки')
        return redirect('dota:team')
    else:
        messages.error(request, 'Вы не подавали заявку')
        return redirect('dota:team')


def single_gamer(request):
    user = request.user
    if request.method != 'POST':
        return redirect('dota:team')

    mmrs = request.POST.getlist('mmr', False)
    if mmrs:
        try:
            mmr = int(mmrs[0])
        except ValueError:
            messages.error(request, 'ММР должен быть целым числом')
            return redirect('dota:team')
    else:
        mmr = 0

    role = request.POST.getlist('role', False)
    if role:
        role = reduce(lambda x, y: int(x) + int(y), role, 0)
        user.userprofile.mider = role & 1 != 0
        user.userprofile.carry = role & 2 != 0
        user.userprofile.hardliner = role & 4 != 0
        user.userprofile.semisupport = role & 8 != 0
        user.userprofile.fullsupport = role & 16 != 0
        user.userprofile.save()

    if user.userprofile.team_id == -1:
        # TODO change int to string
        user.userprofile.participant = True
        user.userprofile.mmr = mmr
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
    user.userprofile = _leave_team(user)
    messages.success(request, 'Вы вышли из команды')
    return redirect('dota:team')


def join_invite_key(request, invite_key):
    try:
        team = Team.objects.get(invite_key=invite_key)
    except ObjectDoesNotExist:
        messages.error(request, 'Команды с таким кодом не существует')
        return redirect('dota:index')

    if datetime.now() > END_TIME_REGISTRATION:
        messages.error(request, 'Регистрация закрыта')
        return redirect('dota:index')

    #TODO Do we need error checking here? There MUST be exactly ONE cap in each team, but who knows...
    captain = team.captain
    dct = {
        'team': {
            'name': team.name,
            'invite_key': team.invite_key
        },
        'captain': {
            'name': captain.user.first_name + ' ' + captain.user.last_name,
            'link': captain.link
        }
    }
    return render(request, 'dota/invite_key.html', dct)


def change_name(request):
    user = request.user
    if request.method != 'POST':
        return redirect('dota:team')
    names = request.POST.getlist("name", False)
    if not names:
        messages.error(request, "Вы не вели название команды")
        return redirect('dota:team')
    name = names[0]
    if not user.userprofile.captain:
        messages.error(request, "Вы не можете изменять название команды, так как не являетесь капитаном")
    elif user.userprofile.team_id == -1:
        messages.error(request, "Вы не вступили ни в одну из команд")
    else:
        user.userprofile.team.change_name(name)
        user.userprofile.team.save()
        messages.success(request, "Название изменено")
    return redirect("dota:team")
