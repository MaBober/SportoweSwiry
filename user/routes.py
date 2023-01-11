from start import app, db
from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, render_template, flash , redirect, url_for, request, session, abort, current_app
from flask_login import LoginManager, logout_user, login_required, current_user
from flask_avatars import Avatars

from .classes import User, DashboardPage, UserBans
from .forms import UserForm, LoginForm, NewPasswordForm, VerifyEmailForm, UploadAvatarForm, BanReason, SubscribeNewsletter
from .functions import account_confirmation_check, login_from_messenger_check

from urllib.parse import urlparse, urljoin

import os


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
    template_folder='templates',
    static_folder='static',
    static_url_path='/user/static')

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



@user.route("/create_user", methods=['POST', 'GET'])
def create_account():
    
    form = UserForm()
    #Delete of not necessary inputs
    del form.isAdmin
    del form.avatar
    del form.id

    if form.validate_on_submit():

        message, status, action = User.create_standard_account(form)
        flash(message, status)
        if form.subscribe_newsletter.data == True:
            current_user.subscribe_newsletter()

        return action

    return render_template('new_user_form.html',
                 form = form,
                 title_prefix = "Nowe konto")


@user.route("/unconfirmed_user")
@login_required
def unconfirmed():

    return render_template('unconfirmed.html')


@user.route("/banned_user")
@login_required
def banned():

    message = UserBans.query.filter(UserBans.user_id == current_user.id).first().description
    return render_template('banned.html', reason_description = message)



@user.route("/send_token_again")
@login_required
def send_token_again():
    #Re-sending the email with the account confirmation token
    user = User.query.filter(User.id == current_user.id).first()
    user.generate_confirmation_token()

    flash('Na Twój adres e-mail wysłano nowy link potwierdzający.')
    return redirect(url_for('other.hello'))


@user.route('/confirm_user/<token>')
@login_required
def confirm(token):

    message, status, action = current_user.confirm(token)
    flash(message, status)

    return action


@user.route('/reset_password', methods=['POST', 'GET'])
def reset():

    form = VerifyEmailForm()
    if form.validate_on_submit():

        #Sending a token to an e-mail to reset the password
        user = User.query.filter(User.mail == form.mail.data).first()
        message, staus, action = user.generate_reset_token()

        #flash(message, staus)
        return action

    return render_template("verify_email.html", title_prefix = "Resetowanie hasła", form=form)


@user.route('/reset_password/<token>', methods=['POST', 'GET'])
def reset_password(token):

    form = NewPasswordForm()
    del form.oldPassword

    if form.validate_on_submit():

        message, status, action = User.reset_password(token, form.newPassword.data)
        flash(message, status)
        return action

    return render_template("reset_password.html", title_prefix = "Resetowanie hasła", form=form)

@user.route("/ban_user/<user_id>", methods=['POST', 'GET'])
def ban_user(user_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    user_to_ban = User.query.filter(User.id == user_id).first()
    if user_to_ban != None:

        ban_reason = ''
        if request.method == 'POST':
            ban_reason = request.form['ban_reason']

        message, status, action = user_to_ban.ban(ban_reason)
        flash(message, status)
        return action

    return redirect(url_for('other.hello'))

@user.route("/unban_user/<user_id>", methods=['POST', 'GET'])
def unban_user(user_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    user_to_unban = User.query.filter(User.id == user_id).first()
    if user_to_unban != None:

        message, status, action = user_to_unban.unban()
        flash(message, status)
        return action

    return redirect(url_for('other.hello'))


@user.route("/list_of_users", methods=['POST', 'GET'])
@account_confirmation_check
@login_required #This page needs to be login
def list_of_users():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    ban_form = BanReason()

    users = User.query.all()
    return render_template('list_of_users.html',
                    users=users,
                    ban_form = ban_form,
                    menu_mode = "mainApp",
                    title_prefix = "Lista użytkowników")


@user.route('/delete_user/<user_id>')
@account_confirmation_check
@login_required #This page needs to be login
def delete_user(user_id):

    if not current_user.is_admin and not user_id == current_user.id :
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    user_to_delete = User.query.filter(User.id == user_id).first()
    message, status, action = user_to_delete.delete()

    flash(message, status)
    return action


@user.route("/login", methods=['POST', 'GET'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('other.hello'))

    logForm = LoginForm()
    if logForm.validate_on_submit():

        # Defines uset to login
        user = User.query.filter(User.id == logForm.name.data).first() #if login=userName
        if not user:
            user = User.query.filter(User.mail == logForm.name.data).first() #if login=mail

        message, status, action = user.standard_login(login_form = logForm, remember = logForm.remember.data)

        flash(message, status)
        return action

    return render_template('login.html',
                    logForm=logForm,
                    title_prefix = "Zaloguj")


@user.route("/logout")
def logout():
    logout_user()
    flash("Wylogowałeś się")
    return redirect(url_for('other.hello'))


@user.route("/settings_user", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def settings():

    form = UserForm(id = current_user.id,
                    name = current_user.name,
                    last_name = current_user.last_name,
                    mail = current_user.mail,
                    statute_acceptance = True)
    del form.password
    del form.verifyPassword
    del form.id
    del form.mail
    del form.statute_acceptance

    avatar_form = UploadAvatarForm()
    newsletter_form = SubscribeNewsletter()

    if newsletter_form.validate_on_submit():
        message, status, action = current_user.subscribe_newsletter()
        flash(message, status)

        return action


    if avatar_form.image.data == None and form.validate_on_submit():       

        #update name and last name in date base
        message, status, action = current_user.modify(form)

        flash(message, status)
        return action

    if avatar_form.validate_on_submit():
        
        picture = avatar_form.image.data
        message, status, action = current_user.upload_avatar(picture)
        flash(message, status)
        return action

    return render_template("account_settings.html",
                    title_prefix = "Ustawienia konta",
                    form = form,
                    newsletter_form = newsletter_form,
                    avatarForm = avatar_form,
                    menu_mode = "mainApp",
                    mode = "settings")



@user.route("/password_change", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def password_change():

    form = NewPasswordForm(id=current_user.id)

    if form.validate_on_submit():

        #update password in date base
        message, status, action = current_user.change_password(form)

        flash(message, status)
        return action

    return render_template("password_change.html",
                    title_prefix = "Prywatność",
                    form = form,
                    menu_mode = "mainApp",
                    mode = "passwordChange")


@user.route("/dashboard/")
@account_confirmation_check
@login_required #This page needs to be login
def dashboard():
    # print(f'auth: {current_user.is_authenticated}')
    # print(f'banned: {current_user.is_banned}')
    # print(f'confirmed: {current_user.confirmed}')
    dashboard = DashboardPage(request.args)

    return render_template('dashboard.html',
                    dashboard = dashboard,
                    menu_mode = "mainApp")     
        
  
@user.route("/rotate_avatar_right")
@login_required #This page needs to be login
def rotate_avatar_right():

    action = current_user.rotate_avatar(angle = -90)
    return action


@user.route("/rotate_avatar_left")
@login_required #This page needs to be login
def rotate_avatar_left():

    action = current_user.rotate_avatar(angle = 90)
    return action


@login_from_messenger_check
@user.route("/google-login")
def loginGoogle():

    if '127.0.0.1:5000' in request.base_url or 'test' in request.base_url:
        flash("Ta funkcjonalność dostępna wyłącznie w aplikacji produkcyjnej.", 'danger')
        return redirect(url_for('user.login'))

    if "FB_IAB" in request.headers.get('User-Agent'):
        flash("Autoryzacja Google nie działa bezpośrednio z aplikacji Messenger", 'danger')
        return redirect(url_for('user.login'))

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
    user = User.query.filter(User.mail == email).first()
    if user != None:
        message, status, action = user.standard_login(remember=True, social_media_login = True)
        flash(message, status)
        return action

    else:
        full_name = str(name).split(" ")
        first_name = full_name[0]
        last_name = full_name[1]

        message, status, action = User.create_account_from_social_media(first_name, last_name, email, "Google")
        flash(message, status)

        return action


@login_from_messenger_check
@user.route("/fb-login")
def loginFacebook():

    if '127.0.0.1:5000' in request.base_url or 'test' in request.base_url:
        flash("Ta funkcjonalność dostępna jest wyłącznie w aplikacji produkcyjnej.", 'danger')
        return redirect(url_for('user.login'))

    try:
        if "error" not in request.args:

            facebook = requests_oauthlib.OAuth2Session(FB_CLIENT_ID, redirect_uri=URL + "/fb-callback", scope=FB_SCOPE)
            authorization_url, _ = facebook.authorization_url(FB_AUTHORIZATION_BASE_URL)

            return flask.redirect(authorization_url)

        else:
            message = "Nie udało się połączyć z Facebook. Spróbuj ponownie za chwilę, lub skontaktuj się z administratorem."
            current_app.logger.warning(f"User {current_user.id} failed in login by facebook")
            return message, 'danger', redirect(url_for('user.login'))

    except:
        message = "W czasie synchronizacji z Facebook pojawił się nieoczekiwany błąd. Spróbuj ponownie za chwilę, lub skontaktuj się z administratorem."
        current_app.logger.exception(f"User {current_user.id} failed in login by facebook")
        return message, 'danger', redirect(url_for('user.login'))
    

@user.route("/fb-callback", methods=['GET'])
def callback():

    current_app.logger.info("Zaczynam fb-callback!")
    try:
        if "error" not in request.args:
            current_app.logger.info("Jestem w if error!")

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
                message, status, action = user.standard_login(remember=True, social_media_login = True)
                flash(message, status)
                return action

            else:
                full_name = str(name).split(" ")
                first_name = full_name[0]
                last_name = full_name[1]

                message, status, action = User.create_account_from_social_media(first_name, last_name, email, "Facebook")
                flash(message, status)

                return action

        else:
            current_app.logger.info("Jestem w if else!")
            message = "Nie udało się połączyć z Facebook. Spróbuj ponownie za chwilę, lub skontaktuj się z administratorem."
            current_app.logger.warning(f"User failed in login by facebook")
            return message, 'danger', redirect(url_for('user.login'))

    except:
        current_app.logger.info("Jestem w if except!")
        message = "W czasie synchronizacji z Facebook pojawił się nieoczekiwany błąd. Spróbuj ponownie za chwilę, lub skontaktuj się z administratorem."
        current_app.logger.exception(f"User failed in login by facebook")
        return message, 'danger', redirect(url_for('user.login'))

        

@user.route("/subscribe_newsletter", methods=['GET'])
@login_required
def subscribe_newsletter():

    message, status, action = current_user.subscribe_newsletter()
    flash(message, status)

    return action



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




