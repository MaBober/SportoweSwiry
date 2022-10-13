import csv
from start import app, db
from flask import Blueprint, render_template, flash , redirect, url_for, request, session, abort


from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
from sqlalchemy.exc import SQLAlchemyError
import os


from .classes import User, DashboardPage
from .forms import UserForm, LoginForm, NewPasswordForm, VerifyEmailForm, UploadAvatarForm
from other.functions import account_confirmation_check, send_email
import functools
from .functions import save_avatar_from_facebook, account_confirmation_check, login_from_messenger_check
from .functions import create_standard_account, create_account_from_social_media, standard_login, login_from_facebook

from werkzeug.utils import secure_filename
import datetime as dt
import math

from PIL import Image
from flask_avatars import Avatars

#Google and Facebook authorization
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
from authlib.integrations.flask_client import OAuth
import flask
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

from config import Config

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

avatars = Avatars(app)

loginManager=LoginManager(app) #Instancy for Login Manager
loginManager.login_view = 'user.login' #Redirect to login for restricted pages
loginManager.login_message = "Musisz się zalogować, żeby przejść do tej zawartości"

user = Blueprint("user", __name__,
    template_folder='templates')

FB_CLIENT_ID = Config.FB_CLIENT_ID
FB_CLIENT_SECRET = Config.FB_CLIENT_SECRET
FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
URL = "https://sportoweswiry.com.pl"
FB_SCOPE = ["email"]

GOOGLE_CLIENT_ID = Config.GOOGLE_CLIENT_ID
GOOGLE_PROJECT_ID = Config.GOOGLE_PROJECT_ID
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_PROVIDER_X509_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
CLIENT_SECRET = Config.CLIENT_SECRET
REDIRECT_URI_MAIN = "https://test.sportoweswiry.atthost24.pl/google_callback"
REDIRECT_URI_LOCAL = "http://127.0.0.1:5000/google_callback"

google_client_config = {"web": {
        "client_id": GOOGLE_CLIENT_ID,
        "project_id": GOOGLE_PROJECT_ID,
        "auth_uri": GOOGLE_AUTH_URI,
        "token_uri": TOKEN_URI,
        "auth_provider_x509_cert_url": AUTH_PROVIDER_X509_CERT_URL,
        "client_secret": CLIENT_SECRET,
        "redirect_uris":[REDIRECT_URI_MAIN, REDIRECT_URI_LOCAL]
    }
}

oauth = OAuth(app)



#Function which can connect user with good ID (for logging)
@loginManager.user_loader
def UserLoader(userName):
    return User.query.filter(User.id == userName).first()

#Function which check if url adress is correct (from your app)
def isSafeUrl(target): 
    ref_url = urlparse(request.host_url) 
    test_url = urlparse(urljoin(request.host_url, target)) 
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc



@user.route("/createUser", methods=['POST', 'GET'])
def create_account():
    
    form=UserForm()
    #Delete of not necessary inputs
    del form.is_admin
    del form.avatar
    del form.id

    if form.validate_on_submit():
        newUser = create_standard_account(form)
        token = newUser.generate_confirmation_token()
        send_email(newUser.mail, 'Potwierdź swoje konto','confirm', user=newUser, token=token)
        login_user(newUser)
        flash("Nowe konto zostało utworzone a na Twój adres e-mail wysłano prośbę o potwierdzenie konta.")
        return redirect(url_for('other.hello'))

    return render_template('NewUserForm.html', form=form, title_prefix = "Nowe konto")

@user.route("/unconfirmedUser")
@login_required
def unconfirmed():
    return render_template('unconfirmed.html')

@user.route("/sendTokenAgain")
@login_required
def sendTokenAgain():
    #Re-sending the email with the account confirmation token
    user=User.query.filter(User.id == current_user.id).first()
    token = user.generate_confirmation_token()
    send_email(user.mail, 'Potwierdź swoje konto.','confirm', user=user, token=token)
    flash('Na twój adres e-mail wysłano nowego linka potwierdzającego.')
    return redirect(url_for('other.hello'))

@user.route('/confirmUser/<token>')
@login_required
def confirm(token):
    #Accepting the token confirmation from the link in the email
    if current_user.confirmed:
        return redirect(url_for('other.hello'))
    if current_user.confirm(token):
        db.session.commit()
        flash('Potwierdziłeś swoje konto. Dzięki!')
    else:
        flash('Link potwierdzający jest nieprawidłowy lub już wygasł.')
    return redirect(url_for('other.hello'))

@user.route('/resetPassword', methods=['POST', 'GET'])
def reset():

    form=VerifyEmailForm()
    if form.validate_on_submit():

        #Sending a token to an e-mail to reset the password
        user=User.query.filter(User.mail == form.mail.data).first()
        token = user.generate_reset_token()
        send_email(user.mail, 'Zresetuj hasło','reset', user=user, token=token)
        # flash("Na twój adres e-mail wysłano link do resetowania hasła")
        return redirect(url_for('user.resetSent'))

    return render_template("verifyEmail.html", title_prefix = "Resetowanie hasła", form=form)


@user.route('/resetPasswordSent')
def resetSent():

    return render_template("verifyEmailSent.html", title_prefix = "Resetowanie hasła")

@user.route('/resetPassword/<token>', methods=['POST', 'GET'])
def resetPassword(token):

    form=NewPasswordForm()
    del form.oldPassword

    if form.validate_on_submit():

        #Token acceptance and password reset
        if User.reset_password(token, form.newPassword.data):
            db.session.commit()
            flash("Hasło zostało poprawnie zmienione. Możesz się zalogować")
            return redirect(url_for('user.login'))
        else:
            return redirect(url_for('other.hello'))

    return render_template("resetPassword.html", title_prefix = "Resetowanie hasła", form=form)


@user.route("/listOfUsers")
@account_confirmation_check
@login_required #This page needs to be login
def list_of_users():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    users=User.query.all()
    return render_template('listOfUsers.html',
                    users=users,
                    title_prefix = "Lista użytkowników")


@user.route('/deleteUser/<user_id>')
@account_confirmation_check
@login_required #This page needs to be login
def delete_user(user_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    userToDelete=User.query.filter(User.id == user_id).first()
    if not userToDelete.is_admin:
        try:
            db.session.delete(userToDelete)
            db.session.commit()
            flash("Użytkownik {} {} został usunięty z bazy danych".format(userToDelete.name, userToDelete.last_name))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Nie można usunąć użytkownika {} {}".format(userToDelete.name, userToDelete.last_name),'danger')
    else:
        flash("Nie można usunąć użytkownika {} {}".format(userToDelete.name, userToDelete.last_name),'danger')

    return redirect(url_for('user.list_of_users'))


@user.route("/login", methods=['POST', 'GET'])
def login():

    logForm = LoginForm()
    if logForm.validate_on_submit():
        user = User.query.filter(User.id == logForm.name.data).first() #if login=userName
        if not user:
            user = User.query.filter(User.mail == logForm.name.data).first() #if login=mail

        verify = User.verify_password(user.password, logForm.password.data)

        if user != None and verify:
            standard_login(user, remember=logForm.remember.data)
            return redirect(url_for('user.dashboard'))
        else:
            flash("Nie udało się zalogować. Podaj pawidłowe hasło")

    return render_template('login.html',
                    logForm=logForm,
                    title_prefix = "Zaloguj")


@user.route("/logout")
def logout():
    logout_user()
    flash("Wylogowałeś się")
    return redirect(url_for('other.hello'))


@user.route("/settingsUser", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def settings():

    form = UserForm(userName = current_user.id,
                    name = current_user.name,
                    lastName = current_user.last_name,
                    mail = current_user.mail)

    avatarForm = UploadAvatarForm()

    del form.password
    del form.verifyPassword
    del form.id
    del form.mail

    if not avatarForm.image.data and form.validate_on_submit():
        #update name and last name in date base
        actualUser = User.query.filter(User.name == current_user.name).first()
        actualUser.name = form.name.data
        actualUser.last_name = form.lastName.data
        db.session.commit()

        flash('Dane zmienione poprawnie')
        return redirect(url_for('user.settings'))

    if avatarForm.validate_on_submit():
        #Upload a new avatar photo

        file = avatarForm.image.data
        avatar = Image.open(file)
        avatar.thumbnail((60,60))

        if avatar.format=='jpg':
            filename = secure_filename(current_user.id + '.jpg')
            print(app.root_path, app.config['AVATARS_SAVE_PATH'], filename)
            avatar.save(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))
            flash("Zdjęcie profilowe zostało poprawnie przesłane na serwer")
        else:
            filename = secure_filename(current_user.id + '.png')
            newAvatar = avatar.convert('RGB') #Convert from png to jpg
            filename = secure_filename(current_user.id + '.jpg')
            newAvatar.save(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))
            flash("Zdjęcie profilowe zostało poprawnie przesłane na serwer")

        return redirect(url_for('user.settings'))

    return render_template("accountSettings.html",
                    title_prefix = "Ustawienia konta",
                    form = form,
                    avatarForm = avatarForm,
                    menuMode = "mainApp",
                    mode = "settings")


@user.route("/passwordChange", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def passwordChange():

    form=NewPasswordForm(id=current_user.id)

    if form.validate_on_submit():
        #update password in date base
        actualUser=User.query.filter(User.name == current_user.name).first()
        actualUser.password=form.newPassword.data
        actualUser.password=actualUser.hash_password()
        db.session.commit()

        flash("Hasło zmienione. Zaloguj się ponownie")
        return redirect(url_for('user.logout'))

    return render_template("passwordChange.html",
                    title_prefix = "Prywatność",
                    form = form,
                    menuMode = "mainApp",
                    mode = "passwordChange")


@user.route("/dashboard/")
@account_confirmation_check
@login_required #This page needs to be login
def dashboard():

    dashboard = DashboardPage(request.args)
    print(dashboard.event)

    return render_template('dashboard.html',
                    dashboard = dashboard,
                    menuMode = "mainApp")     
        
  
@user.route("/rotateAvatarRight")
@login_required #This page needs to be login
def rotateAvatarRight():

    current_user.rotateAvatar(angle = -90)
    return redirect(url_for('user.settings'))


@user.route("/rotateAvatarLeft")
@login_required #This page needs to be login
def rotateAvatarLeft():

    current_user.rotateAvatar(angle = 90)
    return redirect(url_for('user.settings'))


@login_from_messenger_check
@user.route("/google-login")
def loginGoogle():

    #Gogole
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = Flow.from_client_config(client_config = google_client_config,
                                    scopes = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
                                    redirect_uri="https://sportoweswiry.com.pl/callback")

    authorization_url, state = flow.authorization_url() 
    session["state"] = state   

    return redirect(authorization_url)


@user.route("/callback")
def callbackGoogle():

    #Gogole
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = Flow.from_client_config(client_config=google_client_config,
                                    scopes=["https://www.googleapis.com/auth/userinfo.profile","https://www.googleapis.com/auth/userinfo.email", "openid"],
                                    redirect_uri="https://sportoweswiry.com.pl/callback")
    
    #Gets data from Google
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
                        id_token = credentials._id_token,
                        request = token_request,
                        audience = GOOGLE_CLIENT_ID)

    name = id_info.get("name")
    email = id_info.get("email")

    #Login user to APP
    user=User.query.filter(User.mail == email).first()
    if user != None:
        standard_login(user, remember=True)
        return redirect(url_for('user.dashboard'))

    else:
        fullName = str(name).split(" ")
        firstName = fullName[0]
        last_name = fullName[1]

        create_account_from_social_media(firstName, last_name, email)
        user=User.query.filter(User.mail == email).first()
        standard_login(user, remember=True)

    return redirect(url_for('other.hello'))


@login_from_messenger_check
@user.route("/fb-login")
def loginFacebook():

    facebook = requests_oauthlib.OAuth2Session(FB_CLIENT_ID, redirect_uri=URL + "/fb-callback", scope=FB_SCOPE)
    authorization_url, _ = facebook.authorization_url(FB_AUTHORIZATION_BASE_URL)

    return flask.redirect(authorization_url)


@user.route("/fb-callback", methods=['GET'])
def callback():
    facebook = requests_oauthlib.OAuth2Session(FB_CLIENT_ID, scope=FB_SCOPE, redirect_uri=URL + "/fb-callback")

	# we need to apply a fix for Facebook here
    facebook = facebook_compliance_fix(facebook)

    facebook.fetch_token(FB_TOKEN_URL, client_secret=FB_CLIENT_SECRET, authorization_response=flask.request.url)

	# Fetch a protected resource, i.e. user profile, via Graph API
    facebook_user_data = facebook.get("https://graph.facebook.com/me?fields=id,name,email,picture{url}").json()
    
    email = facebook_user_data["email"]
    name = facebook_user_data["name"]
    picture_url = facebook_user_data.get("picture", {}).get("data", {}).get("url")
    
    user = User.query.filter(User.mail == email).first()
    if user != None:
            login_from_facebook(user, picture_url, remember=True)
            return redirect(url_for('user.dashboard'))
    else:
        fullName = str(name).split(" ")
        firstName = fullName[0]
        last_name = fullName[1]

        create_account_from_social_media(firstName, last_name, email)
        user = User.query.filter(User.mail == email).first()
        login_from_facebook(user, picture_url, remember=True)
        return redirect(url_for('user.dashboard'))


@login_from_messenger_check
@user.route("/fb-login-connect")
def loginConnectFacebook():

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    facebook = requests_oauthlib.OAuth2Session(FB_CLIENT_ID, redirect_uri=URL + "/fb-callback-connect", scope=FB_SCOPE)
    authorization_url, _ = facebook.authorization_url(FB_AUTHORIZATION_BASE_URL)

    return flask.redirect(authorization_url)


@user.route("/fb-callback-connect", methods=['GET'])
@login_required #This page needs to be login
def callbackConnect():
    facebook = requests_oauthlib.OAuth2Session(FB_CLIENT_ID, scope=FB_SCOPE, redirect_uri=URL + "/fb-callback-connect")

	# we need to apply a fix for Facebook here
    facebook = facebook_compliance_fix(facebook)

    facebook.fetch_token(FB_TOKEN_URL, client_secret = FB_CLIENT_SECRET, authorization_response = flask.request.url)

	# Fetch a protected resource, i.e. user profile, via Graph API
    facebook_user_data = facebook.get("https://graph.facebook.com/me?fields=id,name,email,picture{url}").json()
    
    email = facebook_user_data["email"]
    name = facebook_user_data["name"]
    picture_url = facebook_user_data.get("picture", {}).get("data", {}).get("url")

    checkingExistUser=User.query.filter(User.mail == email).first()

    if checkingExistUser:
        flash("Konto facebook ({}) jest już wykorzystywane przez innego użytkownika. Użyj innego konta facebook".format(email))
    else:
        user = User.query.filter(User.id == current_user.id).first()
        fullName = str(name).split(" ")
        firstName = fullName[0]
        last_name = fullName[1]
        user.name = firstName
        user.last_name = last_name
        user.mail = email
        db.session.commit()
        save_avatar_from_facebook(picture_url, current_user.id)
        flash("Twoje konto zostało połączone z kontem na facebooku: {} ({})".format(name,email))

    return redirect(url_for('user.settings'))


@login_from_messenger_check
@user.route("/google-login-connect")
def googleLoginConnect():

    #Gogole
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = Flow.from_client_config(client_config = google_client_config,
                                    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
                                    redirect_uri="https://sportoweswiry.com.pl/callback")
    
    authorization_url, state = flow.authorization_url() 
    session["state"] = state   

    return redirect(authorization_url)


@user.route("/google-callback-connect", methods=['GET'])
@login_required
def googleConnectCallback():

    #Gogole
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = Flow.from_client_config(client_config = google_client_config,
                                    scopes = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
                                    redirect_uri="https://sportoweswiry.com.pl/callback")
    
    #Gets data from Google
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
                                    id_token=credentials._id_token,
                                    request=token_request,
                                    audience=GOOGLE_CLIENT_ID)

    name = id_info.get("name")
    email = id_info.get("email")

    checkingExistUser = User.query.filter(User.mail == email).first()

    if checkingExistUser:
        flash("Konto gmail ({}) jest już wykorzystywane przez innego użytkownika. Użyj innego konta gmail".format(email))
    else:
        user = User.query.filter(User.id == current_user.id).first()
        fullName = str(name).split(" ")
        firstName = fullName[0]
        last_name = fullName[1]
        user.name = firstName
        user.last_name = last_name
        user.mail = email
        db.session.commit()
        flash("Twoje konto zostało połączone z kontem gmial: {} ({})".format(name,email))

    return redirect(url_for('user.settings'))


@user.route('/copy_users')
def copy_users():

    copy_users_from_csv('user.csv')

    return redirect(url_for('other.hello'))


def copy_users_from_csv(file_path):

    with open(file_path, encoding="utf8") as user_file:
        a = csv.DictReader(user_file)
        for row in a:

            if row["isAddedByGoogle"] == 'NULL' or row["isAddedByGoogle"] == '0':
                row["isAddedByGoogle"] = False
            else:
                row["isAddedByGoogle"] = True

            if row["isAddedByFB"] == 'NULL' or row["isAddedByFB"] == '0':
                row["isAddedByFB"] = False
            else:
                row["isAddedByFB"] = True

            if row["isAdmin"] == '0':
                row["isAdmin"] = False
            else:
                row["isAdmin"] = True

            if row["confirmed"] == '1':
                row["confirmed"] = True

            newUser = User(id = row["id"], name = row["name"], last_name = row["lastName"], mail=row["mail"], 
            password = row["password"], is_admin=row["isAdmin"], confirmed = row["confirmed"], is_added_by_google = row["isAddedByGoogle"], is_added_by_fb = row["isAddedByFB"] )

            try:

                db.session.add(newUser)
                db.session.commit()

            except:
                print('Error', row['id'])

    return True
    


