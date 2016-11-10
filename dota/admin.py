from django.contrib import admin
from .models import Article, Team, UserProfile, Tournament, TournamentRound, TournamentGame
# Register your models here.


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'team', 'participant')
    list_filter = ('participant', 'team')

    def user_name(self, obj):
        return "%s %s" % (obj.user.first_name, obj.user.last_name)


class UserProfileInline(admin.TabularInline):
    model = UserProfile
    min_num = 5
    max_num = 5


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'num_participants')
    inlines = [UserProfileInline,]

    def num_participants(self, obj):
        return len(obj.get_members())


class TournamentRoundInline(admin.TabularInline):
    model = TournamentRound


class TournamentGameInline(admin.TabularInline):
    model = TournamentGame


class TournamentRoundAdmin(admin.ModelAdmin):
    inlines = [TournamentGameInline,]


class TournamentAdmin(admin.ModelAdmin):
    filter_horizontal = ['teams']
    inlines = [TournamentRoundInline,]


admin.site.register(Article)
admin.site.register(Team, TeamAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(TournamentRound, TournamentRoundAdmin)
admin.site.register(TournamentGame)
