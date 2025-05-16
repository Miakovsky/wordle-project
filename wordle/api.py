from ninja import NinjaAPI, Schema, Field, Router
from .models import *
from ninja import UploadedFile, File
from django.shortcuts import get_object_or_404
from typing import List
from django.contrib.auth import authenticate, login, logout
from ninja.security import django_auth
from ninja.errors import HttpError, AuthenticationError
from django.contrib.auth.models import User
from ninja import Query
from typing import Optional
import random
from django.contrib.admin.views.decorators import staff_member_required

api = NinjaAPI(docs_url="docs/")
router = Router()

############## СЛОВА ##############
class WordIn(Schema):
    word: str

class WordOut(Schema):
    id: int
    word: str

@api.post("/create_word")
def create_word(request, new_word: str):
    if request.user.has_perm('auth.create_Слово'):
        new_word = "".join(filter(lambda x: x.isalpha(), new_word))
        data = ",".join("%s" % tup for tup in list((Word.objects.all().values_list('word'))))
        if new_word.lower() in data:
            return ('This word is already at play!')
        else:
            info = {'word': new_word.lower()}
            word = Word.objects.create(**info)
            return {"id": word.id}
    else:
        raise HttpError(403, 'No rights + maidenless + parried')
    

@api.get("/all_words", response=List[WordOut])
def list_words(request):
    words = Word.objects.all()
    return words

@api.get("/get_word/{word_id}", response=WordOut)
def get_word(request, word_id: int):
    word = get_object_or_404(Word, id= word_id)
    return word

@api.put("/get_word/{word_id}")
def update_word(request, word_id: int, changed_word: str):
    if request.user.has_perm('auth.change_Слово'):
        changed_word = "".join(filter(lambda x: x.isalpha(), changed_word))
        data = ",".join("%s" % tup for tup in list((Word.objects.all().values_list('word'))))
        if changed_word.lower() in data:
            return ('This word is already at play!')
        else:
            word = get_object_or_404(Word, id=word_id)
            word.word = changed_word.lower()
            word.save()
            return {"success": True}
    else:
        raise HttpError(403, 'No rights + maidenless + parried')
    

@api.delete("/get_word/{word_id}")
def delete_word(request, word_id: str):
    if request.user.has_perm('auth.delete_Слово'):
        word = get_object_or_404(Word, id=word_id)
        word.delete()
        return {"success": True}
    else:
        raise HttpError(403, 'No rights + maidenless + parried')

############## ПОПЫТКИ ##############

class TryIn(Schema):
    user: int
    word: int
    guesses_left: int

class TryOut(Schema):
    user: int
    word: int
    guesses: str = None
    guesses_left: int
    wrong_letters: str = None

@api.post("/create_try")
def create_try(request):
    info = {}
    if request.user.is_authenticated:
        word = get_object_or_404(Word, id=random.choice(list(Word.objects.all())).id)
        print('++++++++++++++++++',word)
        info = {'word': word, 'user': request.user, 'guesses_left': word.get_guesses(), 'guesses':'', 'wrong_letters': ''}
        a_try = Try.objects.create(**info)
        return {"id": a_try.id, "guesses": a_try.guesses_left}
    else:
        raise HttpError(401, 'pls login')

@api.get("/cheat/{try_id}")
def cheat_word(request, try_id: int):
    if request.user.has_perm('auth.view_Слово'):
        a_try = get_object_or_404(Try, id= try_id)
        print(a_try.word)
        return str(a_try.word)
    else:
        raise HttpError(403, 'No rights + maidenless + parried')
   
   
@api.get("/play/{try_id}", )
def play(request, try_id: int, word_guess: str):
    if request.user.is_authenticated:
        word_guess = word_guess.lower()
        a_try = get_object_or_404(Try, id=try_id, user = request.user)
        if a_try.done:
            return ("You've already played this one!")
        else:
            print(a_try.lose_condition(), a_try.guesses_left)
            word_guess = "".join(filter(lambda x: x.isalpha(), word_guess))
            check = a_try.check_if_acceptable(word_guess)
            if check == 0:
                return ("you already tried to use this word!")
            elif check == 1:
                return ("The word is of incorrect length! It should consist of "+ str(len(a_try.word.word))+' letters!')

            print(word_guess, str(Word.objects.get(word = a_try)))
            if word_guess == str(Word.objects.get(word = a_try)):
                a_try.done = True
                a_try.save()
                create_score = {'user': a_try.user, 'word': a_try.word, 'guesses': len(a_try.word.word)-a_try.guesses_left}
                print(create_score)
                Score.objects.create(**create_score)
                return ("YOU WON")
            else:
                print("==============ANALIZING")
                a_try.analize(word_guess)
                if a_try.lose_condition():
                    a_try.done = True
                    a_try.save()
                    create_score = {'user': a_try.user, 'word': a_try.word, 'guesses': len(a_try.word.word)}
                    print(create_score)
                    Score.objects.create(**create_score)
                    return ("YOU LOST")
            a_try.save()
            try_result = {'guesses': a_try.guesses,
                        'guesses_left': a_try.guesses_left,
                        'wrong_letters': a_try.wrong_letters}
            return try_result
    else:
        raise HttpError(401, 'pls login')

############## АУТЕНТИФИКАЦИЯ ##############
class UserLogin(Schema):
    username: str
    password: str


class UserRegistration(Schema):
    username: str
    email: str
    password1: str
    password2: str
    

class UserOut(Schema):
    username: str
    email: str

@api.get('/user')
def get_user(request):
    print('GET_USER began')
    print(request.user.username)
    if request.user.is_authenticated:
        return request.user.username
    else:
        raise HttpError(401, 'pls login')

    
@api.get('/users', response = List[UserOut])
def get_users(request):
    get_user(request)   
    if request.user.has_perm('auth.view_user'):
        return User.objects.all()
    else:
        raise HttpError(403, 'No rights + maidenless + parried')
    

@api.post('/login')
def login_user(request, payload: UserLogin):
    user = authenticate(username = payload.username, password = payload.password)
    if user is not None:
        login(request, user)
        print(user.username)
        return {"success": True}
    raise AuthenticationError("AUTHENTICATION ERROR")


@api.post('/registration')
def registration_user(request, payload: UserRegistration):
    if User.objects.filter(username = payload.username).exists():
        raise HttpError(400, 'This user exists')
    
    user = User.objects.create_user(
        username = payload.username,
        email = payload.email,
        password = payload.password1
    )
    login(request, user)
    
    return {"success": True}


@api.post('/logout', auth = None)
def logout_user(request):
    logout(request)
    return {"success": True}

############## СЧЕТ ##############   
class ScoreOut(Schema):
    id: int
    user: UserOut
    word: WordOut
    guesses: int


@api.get("/leaderboard", response=List[ScoreOut])
def leaderboard(request, word_id: int):
    scores = Score.objects.filter(word = word_id).order_by('guesses')
    return scores

@api.get("/userboard", response=List[ScoreOut])
def userboard(request):
    if request.user.is_authenticated:
        scores = Score.objects.filter(user = request.user)
        return scores
    else:
        raise HttpError(401, 'pls login')