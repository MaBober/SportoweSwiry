from flask import Blueprint, render_template, flash , redirect, url_for, request, current_app, session, abort
from start import app, db
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
import os

from .classes import User
from activity.classes import Activities
from event.classes import CoefficientsList, DistancesTable
from event.functions import giveUserEvents
from .forms import UserForm, LoginForm, NewPasswordForm, VerifyEmailForm, UploadAvatarForm
from other.functions import send_email
from .functions import SaveAvatarFromFacebook, PasswordGenerator, account_confirmation_check, login_from_messenger_check
from .functions import createStandardAccount, createAccountFromSocialMedia

from werkzeug.utils import secure_filename
import datetime
import math
import pygal
from PIL import Image
from flask_avatars import Avatars

from authlib.integrations.flask_client import OAuth

import flask
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
import os 

#Google login
import requests
import pathlib
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

from user_agents import parse
from config import Config

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# app.config['AVATARS_SAVE_PATH'] = os.path.join(app.static_folder, 'avatars')

avatars = Avatars(app)

loginManager=LoginManager(app) #Instancy for Login Manager
loginManager.login_view = 'user.login' #Redirect to login for restricted pages
loginManager.login_message = "Musisz się zalogować, żeby przejść do tej zawartości"

user = Blueprint("user", __name__,
    template_folder='templates')


# FB_CLIENT_ID = '427488192540443'
# FB_CLIENT_SECRET = '1be908a75d832de15065167023567373'


FB_CLIENT_ID = Config.FB_CLIENT_ID
FB_CLIENT_SECRET = Config.FB_CLIENT_SECRET
FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
URL = "https://sportoweswiry.com.pl"
FB_SCOPE = ["email"]
GOOGLE_CLIENT_ID = Config.GOOGLE_CLIENT_ID

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
def createAccount():
    
    form=UserForm()
    #Delete of not necessary inputs
    del form.isAdmin
    del form.avatar
    del form.id

    if form.validate_on_submit():
        newUser = createStandardAccount(form)
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
def listOfUsers():

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

    users=User.query.all()
    return render_template('listOfUsers.html', avatarsPath=avatarsPath, users=users, title_prefix = "Lista użytkowników")


@user.route('/deleteUser/<userName>')
@account_confirmation_check
@login_required #This page needs to be login
def deleteUser(userName):

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    userToDelete=User.query.filter(User.id == userName).first()
    if not userToDelete.isAdmin:
        db.session.delete(userToDelete)
        db.session.commit()
        flash("Użytkownik {} {} został usunięty z bazy danych".format(userToDelete.name, userToDelete.lastName))
    else:
        flash("Nie można usunąć użytkownika {} {}".format(userToDelete.name, userToDelete.lastName),'danger')

    return redirect(url_for('user.listOfUsers'))


@user.route("/login", methods=['POST', 'GET'])
def login():

    logForm=LoginForm()
    if logForm.validate_on_submit():
        user=User.query.filter(User.id == logForm.name.data).first() #if login=userName
        if not user:
            user=User.query.filter(User.mail == logForm.name.data).first() #if login=mail

        verify=User.verify_password(user.password, logForm.password.data)

        if user != None and verify:
            login_user(user, remember=logForm.remember.data)

            #Checking if next page is exist and if it is safe
            next = request.args.get('next')
            if next and isSafeUrl(next):
                flash("Jesteś zalogowany jako: {} {}".format(current_user.name, current_user.lastName))
                return redirect(next)
            else:
                flash("Jesteś zalogowany jako: {} {}".format(current_user.name, current_user.lastName),"success")

            return redirect(url_for('user.basicDashboard'))
        else:
            flash("Nie udało się zalogować. Podaj pawidłowe hasło")

    return render_template('login.html', logForm=logForm, title_prefix = "Zaloguj")


@user.route("/logout")
def logout():
    logout_user()
    flash("Wylogowałeś się")
    return redirect(url_for('other.hello'))


@user.route("/settingsUser", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def settings():

    avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

    form=UserForm(userName=current_user.id, name=current_user.name, lastName=current_user.lastName, mail=current_user.mail)
    avatarForm=UploadAvatarForm()
    del form.password
    del form.verifyPassword
    del form.id
    del form.mail
    if not avatarForm.image.data and form.validate_on_submit():
        #update name and last name in date base
        actualUser=User.query.filter(User.name == current_user.name).first()
        actualUser.name=form.name.data
        actualUser.lastName=form.lastName.data
        db.session.commit()
        flash('Dane zmienione poprawnie')
        return redirect(url_for('user.settings'))

    
    if avatarForm.validate_on_submit():
        #Upload a new avatar photo

        file = avatarForm.image.data
        #image = Image.open(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))
        avatar = Image.open(file)
        #avatar = rawAvatar.resize((60, 60))
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

    return render_template("accountSettings.html", title_prefix = "Ustawienia konta", form=form, avatarsPath=avatarsPath, avatarForm=avatarForm, current_user=current_user, menuMode="mainApp", mode="settings")

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

    return render_template("passwordChange.html", title_prefix = "Prywatność", form=form, menuMode="mainApp", mode="passwordChange")


@user.route("/basicDashboard/")
@account_confirmation_check
@login_required #This page needs to be login
def basicDashboard():

    if 'eventCount' in request.args:
        try:
            eventCount = int(request.args['eventCount'])
        except:
            eventCount = 0
    
    else:
        eventCount = 0


    activities=Activities.query.filter(Activities.userName == current_user.id).all()

    avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

    if activities:

        sumTime = datetime.timedelta()

        #creating a pie chart
        pie_chart = pygal.Pie(inner_radius=.4, width=500, height=400)
        pie_chart.title = 'Różnorodność aktywności (w %)'

        #Render a URL adress for chart
        pie_chart = pie_chart.render_data_uri()

        #Return list of user events
        userEvents = giveUserEvents(current_user.id, 'ongoing')

        #Return array with data to event data to present
        if userEvents != None:

            eventNames = {}
            eventWeek = {}
            eventWeekDistance = {}
            eventWeekTarget = {}
            eventsDistanceSum = {}
            eventsDistanceAverege = {}
            eventsActivtiyTimeAverege = {}

            for event in userEvents:

                #Defines present week of event
                days = abs(datetime.date.today() - event.start).days
                week = math.ceil((days+1)/7) 
                weekStart = event.start + datetime.timedelta(weeks=1*week-1)
                weekEnd = event.start + datetime.timedelta(weeks=1*week-1, days=6)
     
                activities=Activities.query.filter(Activities.userName == current_user.id).filter(Activities.date >= weekStart).filter(Activities.date <= weekEnd).all()
                if week <= event.lengthWeeks:
                    target = DistancesTable.query.filter(DistancesTable.event_ID == event.id).filter(DistancesTable.week == week).first()
                    target = target.value
                else:
                    target = 0

                WeekDistance = 0
            
                #Create dictionary which keeps calculated distance of activity
                for position in activities:
                    coef = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).filter(CoefficientsList.activityName == position.activity).first()
                    if coef != None:
                        if coef.constant == False:
                            WeekDistance = WeekDistance + (coef.value*position.distance)
                        else: 
                            WeekDistance = WeekDistance + coef.value

                eventNames.update({event.id:event.name})
                eventWeek.update({event.id:week})
                eventWeekDistance.update({event.id:round(WeekDistance,2)})
                eventWeekTarget.update({event.id:target})

                #Defines summary distance of event
                allEventActivities = Activities.query.filter(Activities.userName == current_user.id).filter(Activities.date>=event.start).filter(Activities.date <= event.end).all()
                amount=len(allEventActivities)
                sumDistanceForEvent = 0 
                averageDistanceForEvent = 0

                timeList=[]
                for position in allEventActivities:
                    coef = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).filter(CoefficientsList.activityName == position.activity).first()
                    if coef != None:
                        if coef.constant == False:
                            sumDistanceForEvent = sumDistanceForEvent + (coef.value*position.distance)
                        else: 
                            sumDistanceForEvent = sumDistanceForEvent + coef.value

                    
                    timeList.append(str(position.time))
                    #Sum of total time of activities in event

                sumTime = datetime.timedelta()
                for time in timeList:
                    (h, m, s) = time.split(':')
                    d = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
                    sumTime += d

                try:
                    averageTime=(sumTime/amount)
                except:
                    print("Błąd w: averageTime=sumTime/amount")

                try:
                    (h, m, s) = str(averageTime).split(':')
                    (s1, s2)=s.split(".") #s1-seconds, s2-miliseconds
                    averageTime = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s1))
                except:
                    print("Błąd w: averageTime.split(':')")

                sumDistanceForEvent = round(sumDistanceForEvent,0)
                try:
                    averageDistanceForEvent = sumDistanceForEvent/len(allEventActivities)
                except:
                    print("Błąd w: averageDistanceForEvent = sumDistanceForEvent/len(allEventActivities)")
                averageDistanceForEvent = round(averageDistanceForEvent, 2)
                
                eventsActivtiyTimeAverege.update({event.id:averageTime})
                eventsDistanceSum.update({event.id:sumDistanceForEvent})
                eventsDistanceAverege.update({event.id:averageDistanceForEvent})

            d1 = 100
            try:
                if eventWeek[userEvents[eventCount].id] < userEvents[eventCount].lengthWeeks:
                    d1= eventWeek[userEvents[eventCount].id] / userEvents[eventCount].lengthWeeks * 100
                    d1 = round(d1,0)
                
                else:
                    d1 = 100
            except:
                    print("Błąd w: eventWeek[userEvents[eventCount].id] < userEvents[eventCount].lengthWeeks")


            d2 = 100
            try:
                if eventWeekDistance[userEvents[eventCount].id] < eventWeekTarget[userEvents[eventCount].id]:
                    d2 = eventWeekDistance[userEvents[eventCount].id] / eventWeekTarget[userEvents[eventCount].id] * 100
                    d2 = round(d2, 0)
                
                else:
                    d2=100
            except:
                    print("Błąd w: eventWeekDistance[userEvents[eventCount].id] < eventWeekTarget[userEvents[eventCount].id]")


            if eventCount == len(userEvents)-1:
                nextEvent=0
            else:
                nextEvent = eventCount+1

            if eventCount == 0:   
                previousEvent = len(userEvents)-1
            else:
                previousEvent = eventCount-1
                
            return render_template('NewBasicDashboard.html', activities=activities, title_prefix = "Dashboard", amount=amount,
                            sumDistance=eventsDistanceSum, sumTime=sumTime,  pie_chart=pie_chart, today_7 = datetime.date.today() + datetime.timedelta(days=-7), averageDistance = eventsDistanceAverege,
                            averegeTime = eventsActivtiyTimeAverege, eventsNames=eventNames, event=userEvents[eventCount], nextEvent = nextEvent, previousEvent= previousEvent, eventWeek=eventWeek,
                            eventWeekDistance=eventWeekDistance, eventWeekTarget=eventWeekTarget, menuMode="mainApp", d1=d1, d2=d2, avatarsPath=avatarsPath, eventCount = eventCount, eventAmount = len(userEvents))
                        
        else:
            return render_template('NewBasicDashboard.html', activities=activities, title_prefix = "Dashboard", 
                            event=[], pie_chart=pie_chart, menuMode="mainApp",  d1=0, d2=0, d3=0, avatarsPath=avatarsPath)

    else:
        pie_chart = pygal.Pie(inner_radius=.4, width=500, height=400)
        pie_chart.title = 'Różnorodność aktywności (w %)'
        checkTable=[]
        pie_chart = pie_chart.render_data_uri()
        
        return render_template('NewBasicDashboard.html', activities=activities, title_prefix = "Dashboard", 
                            sumDistance=0, sumTime=0, amount=0, pie_chart=pie_chart, menuMode="mainApp", event=[] , d1=0, d2=0, d3=0)
        
  
@user.route("/rotateAvatarRight")
@login_required #This page needs to be login
def rotateAvatarRight():

    current_user.rotateAvatar(angle=-90)
    return redirect(url_for('user.settings'))

@user.route("/rotateAvatarLeft")
@login_required #This page needs to be login
def rotateAvatarLeft():

    current_user.rotateAvatar(angle=90)
    return redirect(url_for('user.settings'))

@login_from_messenger_check
@user.route("/google-login")
def loginGoogle():

    #Gogole
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
    flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file, scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],redirect_uri="https://sportoweswiry.com.pl/callback")


    authorization_url, state = flow.authorization_url() 
    session["state"] = state   
    #flash(session["google_id"])

    return redirect(authorization_url)


@user.route("/callback")
def callbackGoogle():

    #Gogole
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
    flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file, scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],redirect_uri= "https://sportoweswiry.com.pl/callback")



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
        audience=GOOGLE_CLIENT_ID
    )

    name = id_info.get("name")
    email = id_info.get("email")

    #Login user to APP
    user=User.query.filter(User.mail == email).first()
    if user != None:
            login_user(user, remember=True)

            #SaveAvatarFromFacebook(picture_url, current_user.id)

            #Checking if next page is exist and if it is safe
            next = request.args.get('next')
            if next and isSafeUrl(next):
                flash("Jesteś zalogowany jako: {}".format(name))
                return redirect(next)
            else:
                flash("Jesteś zalogowany jako: {}".format(name))

            return redirect(url_for('user.basicDashboard'))

    else:
        fullName=str(name).split(" ")
        firstName=fullName[0]
        lastName=fullName[1]

        createAccountFromSocialMedia(firstName, lastName, email)

        # newUser=User(name=firstName, lastName=lastName, mail=email, 
        #             id='x', password=PasswordGenerator(), isAdmin=False, confirmed=True, isAddedByGoogle=True)

        # #Generatin new user ID
        # newUser.id = newUser.generate_ID()
        # newUser.id = newUser.removeAccents()

        # #Hash of password       
        # newUser.password=newUser.hash_password()

        # #adding admins to datebase 
        # db.session.add(newUser)
        # db.session.commit()

        user=User.query.filter(User.mail == email).first()
        login_user(user, remember=True)

        #SaveAvatarFromFacebook(picture_url, current_user.id)

        #Checking if next page is exist and if it is safe
        next = request.args.get('next')
        if next and isSafeUrl(next):
            flash("Jesteś zalogowany jako: {}".format(name))
            return redirect(next)
        else:
            flash("Jesteś zalogowany jako: {}".format(name))

    return redirect(url_for('other.hello'))

@user.route("/fb-login")
def loginFacebook():

    if "FB_IAB" in request.headers.get('User-Agent'):
        flash("Autoryzacja Google nie działa bezpośrednio z aplikacji Messenger")
        return redirect(url_for('user.login'))

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
    
    user=User.query.filter(User.mail == email).first()
    if user != None:
            login_user(user, remember=True)

            SaveAvatarFromFacebook(picture_url, current_user.id)

            #Checking if next page is exist and if it is safe
            next = request.args.get('next')
            if next and isSafeUrl(next):
                flash("Jesteś zalogowany jako: {}".format(name))
                return redirect(next)
            else:
                flash("Jesteś zalogowany jako: {}".format(name))

            return redirect(url_for('user.basicDashboard'))
    else:
        fullName=str(name).split(" ")
        firstName=fullName[0]
        lastName=fullName[1]

        createAccountFromSocialMedia(firstName, lastName, email)

        # newUser=User(name=firstName, lastName=lastName, mail=email, 
        #             id='x', password=PasswordGenerator(), isAdmin=False, confirmed=True, isAddedByFB=True)

        # #Generatin new user ID
        # newUser.id = newUser.generate_ID()
        # newUser.id = newUser.removeAccents()

        # #Hash of password       
        # newUser.password=newUser.hash_password()

        # #adding admins to datebase 
        # db.session.add(newUser)
        # db.session.commit()

        user=User.query.filter(User.mail == email).first()
        login_user(user, remember=True)

        SaveAvatarFromFacebook(picture_url, current_user.id)

        #Checking if next page is exist and if it is safe
        next = request.args.get('next')
        if next and isSafeUrl(next):
            flash("Jesteś zalogowany jako: {}".format(name))
            return redirect(next)
        else:
            flash("Jesteś zalogowany jako: {}".format(name))

        return redirect(url_for('user.basicDashboard'))

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

    facebook.fetch_token(FB_TOKEN_URL, client_secret=FB_CLIENT_SECRET, authorization_response=flask.request.url)

	# Fetch a protected resource, i.e. user profile, via Graph API
    facebook_user_data = facebook.get("https://graph.facebook.com/me?fields=id,name,email,picture{url}").json()
    
    email = facebook_user_data["email"]
    name = facebook_user_data["name"]
    picture_url = facebook_user_data.get("picture", {}).get("data", {}).get("url")

    checkingExistUser=User.query.filter(User.mail == email).first()

    if checkingExistUser:
        flash("Konto facebook ({}) jest już wykorzystywane przez innego użytkownika. Użyj innego konta facebook".format(email))
    else:
        user=User.query.filter(User.id == current_user.id).first()
        fullName=str(name).split(" ")
        firstName=fullName[0]
        lastName=fullName[1]
        user.name=firstName
        user.lastName=lastName
        user.mail=email
        db.session.commit()
        SaveAvatarFromFacebook(picture_url, current_user.id)
        flash("Twoje konto zostało połączone z kontem na facebooku: {} ({})".format(name,email))


    return redirect(url_for('user.settings'))

@login_from_messenger_check
@user.route("/google-login-connect")
def googleLoginConnect():

    #Gogole
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
    flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file, scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],redirect_uri="https://sportoweswiry.com.pl/google-callback-connect")

    authorization_url, state = flow.authorization_url() 
    session["state"] = state   


    return redirect(authorization_url)

@user.route("/google-callback-connect", methods=['GET'])
@login_required
def googleConnectCallback():

    #Gogole
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
    flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file, scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],redirect_uri="https://sportoweswiry.com.pl/google-callback-connect")


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
        audience=GOOGLE_CLIENT_ID
    )

    name = id_info.get("name")
    email = id_info.get("email")

    checkingExistUser=User.query.filter(User.mail == email).first()

    if checkingExistUser:
        flash("Konto gmail ({}) jest już wykorzystywane przez innego użytkownika. Użyj innego konta gmail".format(email))
    else:
        user=User.query.filter(User.id == current_user.id).first()
        fullName=str(name).split(" ")
        firstName=fullName[0]
        lastName=fullName[1]
        user.name=firstName
        user.lastName=lastName
        user.mail=email
        db.session.commit()
        flash("Twoje konto zostało połączone z kontem gmial: {} ({})".format(name,email))

    return redirect(url_for('user.settings'))

