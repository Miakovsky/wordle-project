from django.contrib import admin
from .models import *

class WordAdmin(admin.ModelAdmin):
    list_display = ['word', ]
admin.site.register(Word, WordAdmin)

class TryAdmin(admin.ModelAdmin):
    list_display = ['user','word', 'guesses', 'guesses_left', 'wrong_letters']
admin.site.register(Try, TryAdmin)

class ScoreAdmin(admin.ModelAdmin):
    list_display = ['user','word', 'guesses']
admin.site.register(Score, ScoreAdmin)