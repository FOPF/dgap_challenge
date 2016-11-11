from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from dgap_challenge.settings import MAX_TEAM_SIZE


class Article(models.Model):
    title = models.CharField(max_length=255) # заголовок поста
    datetime = models.DateTimeField('Дата публикации') # дата публикации
    content = models.TextField(max_length=10000) # текст поста

    def __str__(self):
        return self.title


class Team(models.Model):
    name = models.CharField('Название', max_length=40, default='')
    invite_key = models.CharField('Ключ для приглашения', max_length=50, default='')

    def get_members(self):
        return self.userprofile_set.all()

    def __str__(self):
        return self.name + ": " + str(len(self.get_members()))


class UserProfile(models.Model):
    user = models.OneToOneField(User, default=None)
    is_approved = models.BooleanField('Пользователь подтверждён', default=False)
    team = models.ForeignKey(Team, default=-1, null=True, blank=True)
    captain = models.BooleanField('Капитан', default=False)
    participant = models.BooleanField('Участник', default=False)
    mmr = models.IntegerField('MMR', default=0)
    mider = models.BooleanField('Мидер', default=False)
    carry = models.BooleanField('Керри', default=False)
    hardliner = models.BooleanField('Хардлайнер', default=False)
    semisupport = models.BooleanField('Семисаппорт', default=False)
    fullsupport = models.BooleanField('Фуллсаппорт', default=False)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


class Tournament(models.Model):
    name = models.CharField('Название чемпионата', max_length=100)
    rules = models.TextField('Правила чемпионата')
    start_dttm = models.DateTimeField('Начало чемпионата')
    end_dttm = models.DateTimeField('Конец чемпионата')
    teams = models.ManyToManyField(Team)

    @property
    def num_teams(self):
        return len(self.teams.all())

    def register_full_teams(self):
        teams = Team.objects.all()
        if not teams:
            return None
        cnt = 0
        for team in teams:
            if len(team.get_members()) == MAX_TEAM_SIZE:
                self.teams.add(team)
            cnt += 1
        return cnt

    @property
    def current_round(self):
        if len(self.tournamentround_set) == 0:
            return None
        return self.tournamentround_set.filter(state=TournamentRound.FINISHED).order_by('-start_dttm')[0]

    def __str__(self):
        return '%s, %s' % (self.name, self.start_dttm)


class TournamentRound(models.Model):
    tournament = models.ForeignKey(Tournament)
    num = models.IntegerField('Номер раунда')
    name = models.CharField('Название раунда', max_length=40, default=None, blank=True, null=True)
    start_dttm = models.DateTimeField('Начало раунда')
    end_dttm = models.DateTimeField('Конец раунда')

    NOT_READY = 0
    CAN_START = 1
    STARTED = 2
    FINISHED = 3
    CANCELLED = 4
    states = (
        (NOT_READY, 'Раунд не готов к началу'),
        (CAN_START, 'Раунд может начинаться'),
        (STARTED, 'Раунд начался'),
        (FINISHED, 'Раунд завершен'),
        (CANCELLED, 'Раунд отменен')
    )
    state = models.IntegerField('Статус раунда', default=NOT_READY, choices=states)

    def __str__(self):
        return self.name


class TournamentGame(models.Model):
    round = models.ForeignKey(TournamentRound)
    team1 = models.ForeignKey(Team, related_name='team1')
    team2 = models.ForeignKey(Team, related_name='team2')
    is_active = models.BooleanField("Игра идет", default=False)
    score = models.CharField('Результат', max_length=40, blank=True, null=True, default=None)
    winner = models.ForeignKey(Team, related_name='winner', blank=True, null=True)

    @property
    #TODO self.winner == None => CRASH!!!
    def loser(self):
        if self.is_active:
            return None
        try:
            if self.winner == self.team1:
                return self.team2
            return self.team1
        except ObjectDoesNotExist:
            return None

    def add_teams(self, team1, team2):
        self.team1 = team1
        self.team2 = team2

    def set_results(self, winner, score):
        self.winner, self.score = winner, score
        self.save()

    def __str__(self):
        return self.team1.name + ' vs. ' + self.team2.name