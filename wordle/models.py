from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

class Word(models.Model):
    word = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Слово'
        verbose_name_plural = 'Слова'

    def __str__(self):
        return self.word
    
    def get_guesses(self):
        return len(self.word)
    
class Try(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    word = models.ForeignKey(Word, on_delete = models.CASCADE)
    guesses = models.TextField(null=True, blank=True)
    guesses_left = models.IntegerField()
    wrong_letters =  models.CharField(max_length=200, null=True, blank=True)
    done = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Попытка'
        verbose_name_plural = 'Попытки'

    def __str__(self):
        return self.word.word
    
    def check_if_acceptable(self, guess):
        if guess in self.guesses:
            return 0
        if len(guess) != len(self.word.word):
            return 1
        return 2

    def remove_guess(self):
        self.guesses_left -= 1

    def analize(self, guess):
        returned_result = []
        for letter in guess:
            if letter in self.word.word and guess.index(letter) == self.word.word.index(letter):
                returned_result.append(letter)
            elif letter in self.word.word and guess.index(letter) != self.word.word.index(letter):
                returned_result.append(f'[{letter}]')
            else:
                returned_result.append(f'_')
                if letter not in self.wrong_letters:
                    self.wrong_letters = self.wrong_letters + letter + ' '
        self.guesses += guess+': '+' '.join(returned_result)+' | '
        self.remove_guess()
        return returned_result
    
    def lose_condition(self):
        if self.guesses_left <= 0:
            print('++++++++++++++', self.guesses_left)
            return True
        else: return False

        
    
class Score(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    word = models.ForeignKey(Word, on_delete = models.CASCADE)
    guesses = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Счет'