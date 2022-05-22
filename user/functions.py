from start import app
from werkzeug.utils import secure_filename
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