from start import app, db
from flask import redirect, url_for, request, flash
from flask_login import current_user, login_user

from .classes import User

from urllib.parse import urlparse, urljoin
from werkzeug.utils import secure_filename
from functools import wraps
import urllib.request
import os
from PIL import Image
import random
import string


def standard_login(user, remember=True):
    login_user(user, remember)
    check_next_url(current_user)
    return None

def is_safe_url(target): 
    ref_url = urlparse(request.host_url) 
    test_url = urlparse(urljoin(request.host_url, target)) 
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def check_next_url(current_user):
    next = request.args.get('next')
    if next and is_safe_url(next):
        flash("Jesteś zalogowany jako: {} {}".format(current_user.name, current_user.lastName))
        return redirect(next)
    else:
        flash("Jesteś zalogowany jako: {} {}".format(current_user.name, current_user.lastName))
    return None


def SaveAvatarFromFacebook(picture_url, id):
    filename = secure_filename(id + '.jpg')
    urllib.request.urlretrieve(picture_url, os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))
    return True


def createStandardAccount(form):
        #Rewriting data from the form
        newUser=User(name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, 
                    id=form.name.data[0:3]+form.lastName.data[0:3], password=form.password.data)

        #Generatin new user ID
        newUser.id = newUser.generate_ID()
        newUser.id = newUser.removeAccents()

        #Hash of password       
        newUser.password=newUser.hash_password()

        #adding admins to datebase 
        db.session.add(newUser)
        db.session.commit()

        return newUser

def createAccountFromSocialMedia(firstName, lastName, email):
    
        newUser=User(name=firstName, lastName=lastName, mail=email, 
                    id=firstName[0:3]+lastName[0:3], password=PasswordGenerator(), isAdmin=False, confirmed=True, isAddedByGoogle=True)

        #Generatin new user ID
        newUser.id = newUser.generate_ID()
        newUser.id = newUser.removeAccents()

        #Hash of password       
        newUser.password=newUser.hash_password()

        #adding admins to datebase 
        db.session.add(newUser)
        db.session.commit()

        return True

def PasswordGenerator():
    characters=[]
    Letters=string.ascii_letters
    Numbers=string.digits
    SpecialSigns=string.punctuation
    
    characters.append(Letters)
    characters.append(Numbers)
    characters.append(SpecialSigns)
    characters="".join(characters)

    password=[]
    for i in range (8):
        position=random.randint(0,len(characters)-1)
        password.append(characters[position])

    password="".join(password)
    return password


def account_confirmation_check(initial_function):
    @wraps(initial_function)
    def wrapped_function(*args, **kwargs):

        if current_user.is_authenticated and not current_user.confirmed:
            return redirect(url_for('user.unconfirmed'))

        else:
            return initial_function(*args, **kwargs)
    return wrapped_function


def login_from_messenger_check(initial_function):
    @wraps(initial_function)
    def wrapped_function(*args, **kwargs):

        if "FB_IAB" in request.headers.get('User-Agent'):
            flash("Autoryzacja Google nie działa bezpośrednio z aplikacji Messenger")
            return redirect(url_for('user.login'))
		
        return initial_function(*args, **kwargs)
    return wrapped_function