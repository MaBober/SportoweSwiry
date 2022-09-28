from start import app
from flask import redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from functools import wraps
import urllib.request
import os
from PIL import Image
import random
import string


def SaveAvatarFromFacebook(picture_url, id):
    filename = secure_filename(id + '.jpg')
    urllib.request.urlretrieve(picture_url, os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))
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
            # wrapped_route = initial_function(*args, **kwargs)
            return initial_function(*args, **kwargs)
        
    return wrapped_function