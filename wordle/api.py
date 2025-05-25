from django.http import HttpResponse
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
from django.contrib.auth.decorators import permission_required
from ninja.security import django_auth
from ninja.security import HttpBearer, HttpBasicAuth
from django.core.exceptions import PermissionDenied

class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(username=username, password=password)
        if user:
            return user
        raise AuthenticationError()


api = NinjaAPI(docs_url="docs/", auth=BasicAuth())
router = Router()

############## СЛОВА ##############
class WordIn(Schema):
    word: str

class WordOut(Schema):
    id: int
    word: str

@api.post("/create_word")
@permission_required('auth.create_Слово', raise_exception=True)
def create_word(request, new_word: str):
    if request.auth.has_perm('auth.create_Слово'):
        new_word = "".join(filter(lambda x: x.isalpha(), new_word))
        data = ",".join("%s" % tup for tup in list((Word.objects.all().values_list('word'))))
        if new_word.lower() in data:
            raise HttpError(400, 'This word is already at play!')
        else:
            info = {'word': new_word.lower()}
            word = Word.objects.create(**info)
            return {"id": word.id}
    raise HttpError(403, "no rights + maidenless + parried")
    

@api.get("/all_words", response=List[WordOut], auth = None)
def list_words(request):
    words = Word.objects.all()
    return words

@api.get("/get_word/{word_id}", response=WordOut)
def get_word(request, word_id: int):
    word = get_object_or_404(Word, id= word_id)
    return word

@api.put("/get_word/{word_id}")
@permission_required('auth.change_Слово', raise_exception=True)
def update_word(request, word_id: int, changed_word: str):
    if request.auth.has_perm('auth.change_Слово'):
        changed_word = "".join(filter(lambda x: x.isalpha(), changed_word))
        data = ",".join("%s" % tup for tup in list((Word.objects.all().values_list('word'))))
        if changed_word.lower() in data:
            raise HttpError(400, 'This word is already at play!')
        else:
            word = get_object_or_404(Word, id=word_id)
            word.word = changed_word.lower()
            word.save()
            return {"success": True}
    raise HttpError(403, "no rights + maidenless + parried")

@api.delete("/get_word/{word_id}")
@permission_required('auth.delete_Слово', raise_exception=True)
def delete_word(request, word_id: str):
    if request.auth.has_perm('auth.delete_Слово'):
        word = get_object_or_404(Word, id=word_id)
        word.delete()
        return {"success": True}
    raise HttpError(403, "no rights + maidenless + parried")


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
    word = get_object_or_404(Word, id=random.choice(list(Word.objects.all())).id)
    print('++++++++++++++++++',word)
    info = {'word': word, 'user': request.auth, 'guesses_left': word.get_guesses(), 'guesses':'', 'wrong_letters': ''}
    a_try = Try.objects.create(**info)
    return {"id": a_try.id, "guesses": a_try.guesses_left}


@api.get("/cheat/{try_id}")
@permission_required('auth.view_Слово', raise_exception=True)
def cheat_word(request, try_id: int):
    if request.auth.has_perm('auth.view_Слово'):
        a_try = get_object_or_404(Try, id= try_id)
        print(a_try.word)
        return str(a_try.word)
    raise HttpError(403, "no rights + maidenless + parried")

   
   
@api.get("/play/{try_id}", )
def play(request, try_id: int, word_guess: str):
    word_guess = word_guess.lower()
    a_try = get_object_or_404(Try, id=try_id, user = request.auth)
    if a_try.done:
        try_result = {'details':str({'guesses': a_try.guesses,
                    'guesses_left': a_try.guesses_left,
                    'wrong_letters': a_try.wrong_letters,
                    'status': 'You already played this one!'})}
        raise HttpError(400, str(try_result))
    else:
        print(a_try.lose_condition(), a_try.guesses_left)
        word_guess = "".join(filter(lambda x: x.isalpha(), word_guess))
        check = a_try.check_if_acceptable(word_guess)
        if check == 0:
            try_result = {'details':str({'guesses': a_try.guesses,
                    'guesses_left': a_try.guesses_left,
                    'wrong_letters': a_try.wrong_letters,
                    'status': 'You already tried this one!'})}
            raise HttpError(400, try_result)
        elif check == 1:
            try_result = {'details':str({'guesses': a_try.guesses,
                    'guesses_left': a_try.guesses_left,
                    'wrong_letters': a_try.wrong_letters,
                    'status': "The word is of incorrect length!"})}
            raise HttpError(400, str(try_result))

        print(word_guess, str(Word.objects.get(word = a_try)))
        if word_guess == str(Word.objects.get(word = a_try)):
            a_try.done = True
            a_try.save()
            create_score = {'user': a_try.user, 'word': a_try.word, 'guesses': len(a_try.word.word)-a_try.guesses_left}
            print(create_score)
            Score.objects.create(**create_score)
            try_result = {'details':str({'guesses': a_try.guesses,
                    'guesses_left': a_try.guesses_left,
                    'wrong_letters': a_try.wrong_letters,
                    'status': 'YOU WON'})}
            return try_result
        else:
            print("==============ANALIZING")
            a_try.analize(word_guess)
            if a_try.lose_condition():
                a_try.done = True
                a_try.save()
                create_score = {'user': a_try.user, 'word': a_try.word, 'guesses': len(a_try.word.word)}
                print(create_score)
                Score.objects.create(**create_score)
                try_result = {'details':str({'guesses': a_try.guesses,
                    'guesses_left': a_try.guesses_left,
                    'wrong_letters': a_try.wrong_letters,
                    'status': 'YOU LOST'})}
                return try_result
        a_try.save()
        try_result = {'details':str({'guesses': a_try.guesses,
                    'guesses_left': a_try.guesses_left,
                    'wrong_letters': a_try.wrong_letters,
                    'status': '-'})}
        return try_result


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

@api.exception_handler(PermissionDenied)
def permission_errors(request, exc):
    return HttpResponse('Permission denied', status = 403)

@api.get('/user', auth=BasicAuth())
def get_user(request):
    return {"user": request.auth.username}

@api.get("/basic", auth=BasicAuth())
def basic(request):
    return {"httpuser": request.auth.username}

@api.get('/login', auth=None)
def login(request, username:str, password:str):
    user = authenticate(username=username, password=password)
    if user:
        return {"Loggen in as": request.auth.username}
    raise AuthenticationError()
    
    
@api.get('/users', response = List[UserOut])
@permission_required('auth.view_user', raise_exception=True)
def get_users(request): 
    if request.auth.has_perm('auth.view_user'):
        return User.objects.all()
    raise HttpError(403, "no rights + maidenless + parried")

@api.post('/registration', auth = None)
def registration_user(request, payload: UserRegistration):
    if User.objects.filter(username = payload.username).exists():
        raise HttpError(400, 'This user exists')
   
    
    user = User.objects.create_user(
        username = payload.username,
        email = payload.email,
        password = payload.password1
    ) 
    return {"success": True}

'''
@api.post('/logout')
def logout_user(request):
    logout(request)
    return {"success": True}
'''
############## СЧЕТ ##############   
class ScoreOut(Schema):
    id: int
    user: UserOut
    word: WordOut
    guesses: int


@api.get("/leaderboard", response=List[ScoreOut], auth = None)
def leaderboard(request, word_id: int):
    scores = Score.objects.filter(word = word_id).order_by('guesses')
    return scores

@api.get("/userboard", response=List[ScoreOut])
def userboard(request):
    scores = Score.objects.filter(user = request.auth)
    return scores