from flask import Blueprint, render_template, flash , redirect, url_for, request, current_app, session
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

from werkzeug.utils import secure_filename
import datetime
import math
import pygal
from PIL import Image

from flask_avatars import Avatars
avatars = Avatars(app)



loginManager=LoginManager(app) #Instancy for Login Manager
loginManager.login_view = 'user.login' #Redirect to login for restricted pages
loginManager.login_message = "Musisz się zalogować, żeby przejść do tej zawartości"

user = Blueprint("user", __name__,
    template_folder='templates')



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
    tempAdmin=form.isAdmin.data
    tempAvatar=form.avatar.data
    #Delete of not necessary inputs
    del form.isAdmin
    del form.avatar

    #CreateUser.CreateUser()

    if form.validate_on_submit():
        #Rewriting data from the form
        newUser=User(name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, 
                    id=form.id.data, password=form.password.data, isAdmin=tempAdmin, avatar=tempAvatar)

        #Hash of password       
        newUser.password=newUser.hash_password()

        #adding admins to datebase 
        db.session.add(newUser)
        db.session.commit()

        token = newUser.generate_confirmation_token()
        send_email(newUser.mail, 'Potwierdź swoje konto','confirm', user=newUser, token=token)

        login_user(newUser)
        flash("Nowe konto zostało utworzone a na Twój adres e-mail wysłano prośbę o potwierdzenie konta ;)")
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
        flash("Na twój adres e-mail wysłano link do resetowania hasła")
        return redirect(url_for('other.hello'))

    return render_template("verifyEmail.html", title_prefix = "Resetowanie hasła", form=form)

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
@login_required #This page needs to be login
def listOfUsers():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

    users=User.query.all()
    return render_template('listOfUsers.html', avatarsPath=avatarsPath, users=users, title_prefix = "Lista użytkowników")


@user.route('/deleteUser/<userName>')
@login_required #This page needs to be login
def deleteUser(userName):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    userToDelete=User.query.filter(User.id == userName).first()
    if not userToDelete.isAdmin:
        db.session.delete(userToDelete)
        db.session.commit()
        flash("Użytkownik {} został usunięty z bazy danych".format(userToDelete.id))
    else:
        flash("Nie można usunąć użytkownika {}".format(userToDelete.id))

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
            login_user(user)

            #Checking if next page is exist and if it is safe
            next = request.args.get('next')
            if next and isSafeUrl(next):
                flash("Jesteś zalogowany jako: {}".format(current_user.id))
                return redirect(next)
            else:
                flash("Jesteś zalogowany jako: {}".format(current_user.id))

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
@login_required #This page needs to be login
def settings():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

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
            avatar.save(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))
            flash("Zdjęcie profilowe zostało poprawnie przesłane na serwer")
        else:
            filename = secure_filename(current_user.id + '.png')
            newAvatar = avatar.convert('RGB') #Convert from png to jpg
            filename = secure_filename(current_user.id + '.jpg')
            newAvatar.save(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))
            flash("Zdjęcie profilowe zostało poprawnie przesłane na serwer")

        return redirect(url_for('user.settings'))

    return render_template("accountSettings.html", title_prefix = "Ustawienia konta", form=form, avatarsPath=avatarsPath, avatarForm=avatarForm, current_user=current_user)

@user.route("/passwordChange", methods=['POST','GET'])
@login_required #This page needs to be login
def passwordChange():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    form=NewPasswordForm(userName=current_user.id)

    if form.validate_on_submit():
        #update password in date base
        actualUser=User.query.filter(User.name == current_user.name).first()
        actualUser.password=form.newPassword.data
        actualUser.password=actualUser.hash_password()
        db.session.commit()

        flash("Hasło zmienione. Zaloguj się ponownie")
        return redirect(url_for('user.logout'))

    return render_template("passwordChange.html", title_prefix = "Prywatność", form=form)


@user.route("/basicDashboard")
@login_required #This page needs to be login
def basicDashboard():

    if current_user.is_authenticated and not current_user.confirmed:
       
        return redirect(url_for('user.unconfirmed'))

    activities=Activities.query.filter(Activities.userName == current_user.id).all()

    #avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

    if activities:
        sumDistance=0
        sumTime = datetime.timedelta()
        timeList=[]
        amount=len(activities)

        for activity in activities:
            sumDistance=sumDistance+activity.distance
            timeList.append(str(activity.time))

        #Sum of total time of activities
        for time in timeList:
            (h, m, s) = time.split(':')
            d = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            sumTime += d

        try:
            (h, m, s) = str(sumTime).split(':')
            (s1, s2)=s.split(".") #s1-seconds, s2-miliseconds
            sumTime= datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s1))
        except:
            print("Something went wrong")

        sumDistance=round(sumDistance,2)

        #creating a pie chart
        pie_chart = pygal.Pie(inner_radius=.4, width=500, height=400)
        pie_chart.title = 'Różnorodność aktywności (w %)'
        checkTable=[]

        #calculation of the percentage of activity
        for activityExternal in activities:
            quantity=0
            for activityInternal in activities:
                if activityExternal.activity==activityInternal.activity and not activityExternal.activity in checkTable:
                    quantity=quantity+1
            if quantity>0:
                pie_chart.add(activityExternal.activity, round((quantity/amount)*100,1))
                checkTable.append(activityExternal.activity)
        
        #Render a URL adress for chart
        pie_chart = pie_chart.render_data_uri()

        #Return list of user events
        userEvents = giveUserEvents(current_user.id)

        #Return array with data to event data to present
        if userEvents != None:


            eventNames = {}
            eventWeek = {}
            eventWeekDistance = {}
            eventWeekTarget = {}

            for event in userEvents:

                #Defines present week of event
                days = abs(datetime.date.today() - event.start).days
                week = math.ceil((days+1)/7) 
                weekStart = event.start + datetime.timedelta(weeks=1*week-1)
                weekEnd = event.start + datetime.timedelta(weeks=1*week-1, days=6)
     
                activities=Activities.query.filter(Activities.userName == current_user.id).filter(Activities.date >= weekStart).filter(Activities.date <= weekEnd).all()
                target = DistancesTable.query.filter(DistancesTable.event_ID == event.id).filter(DistancesTable.week == week).first()

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
                eventWeekTarget.update({event.id:target.value})
                
            return render_template('basicDashboard.html', activities=activities, title_prefix = "Dashboard", 
                            sumDistance=sumDistance, sumTime=sumTime, amount=amount, pie_chart=pie_chart, today_7 = datetime.date.today() + datetime.timedelta(days=-7),
                            eventsNames=eventNames, events=userEvents, eventWeek=eventWeek, eventWeekDistance=eventWeekDistance, eventWeekTarget=eventWeekTarget)
        
        else:
            return render_template('basicDashboard.html', activities=activities, title_prefix = "Dashboard", 
                            sumDistance=sumDistance, sumTime=sumTime, amount=amount, pie_chart=pie_chart)

    else:
        flash("Nie posiadasz dodanych żadnych aktywności")
        return render_template("pages/index.html", title_prefix = "Home")