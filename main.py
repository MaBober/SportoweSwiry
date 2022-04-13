from asyncio import constants
from math import floor
from random import choice
import string
import sys
from start import app, db
from flask import Flask, render_template, flash , redirect, url_for, request, current_app, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from urllib.parse import urlparse, urljoin

from flask_mail import Mail, Message

from startupFunctions import checkIfIsAdmin

from classesDefinition import CoefficientsList, DistancesForm, DistancesTable, Participation, User, UserForm, LoginForm, CoeficientsForm, EventForm, Event, NewPasswordForm, VerifyEmailForm, ActivityForm, Activities, UploadAvatarForm, MessageForm, NewCoeficientsSetForm
from eventFunctions import passCoefficientsTableToDB, passEventToDB, addUserToEvent, createCofficientTemplate, deleteEvent, changeEvent, giveUserEvents, giveEventParticipants, passDistancesToDB, deleteUserFromEvent

import datetime
import time
import math
import array

import pygal
from pygal.style import Style

from flask_avatars import Avatars

import os
from werkzeug.utils import secure_filename

from PIL import Image
#from io import BytesIO



mail = Mail(app)
avatars = Avatars(app)
app.debug = True

eventStatusOptions = ['Zapisy otwarte', 'W trakcie', 'Zakończone']

loginManager=LoginManager(app) #Instancy for Login Manager
loginManager.login_view = 'login' #Redirect to login for restricted pages
loginManager.login_message = "Musisz się zalogować, żeby przejść do tej zawartości"



#Function which can connect user with good ID (for logging)
@loginManager.user_loader
def UserLoader(userName):
    return User.query.filter(User.id == userName).first()

#Function which check if url adress is correct (from your app)
def isSafeUrl(target): 
    ref_url = urlparse(request.host_url) 
    test_url = urlparse(urljoin(request.host_url, target)) 
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject, recipients=[to])
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    mail.send(msg)
    return None
    


@app.before_first_request
def appStartup():
    db.create_all()
    checkIfIsAdmin()
    createCofficientTemplate()


# @app.before_request
# def beforeRequest():
#      #Co robić gdy konto nie potwierdzone
#      if current_user.is_authenticated and not current_user.confirmed and request.endpoint != 'unconfirmed':
#          return redirect(url_for('unconfirmed'))



@app.route("/")
def hello():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if current_user.is_authenticated:
        return redirect(url_for('basicDashboard'))

    return render_template("pages/index.html", title_prefix = "Home")


@app.route("/unconfirmed")
@login_required
def unconfirmed():
    return render_template('unconfirmed.html')

@app.route("/sendTokenAgain")
@login_required
def sendTokenAgain():
    #Re-sending the email with the account confirmation token
    user=User.query.filter(User.id == current_user.id).first()
    token = user.generate_confirmation_token()
    send_email(user.mail, 'Potwierdź swoje konto.','confirm', user=user, token=token)
    flash('Na twój adres e-mail wysłano nowego linka potwierdzającego.')
    return render_template("pages/index.html", title_prefix = "Home")

@app.route('/confirm/<token>')
@login_required
def confirm(token):
    #Accepting the token confirmation from the link in the email
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('Potwierdziłeś swoje konto. Dzięki!')
    else:
        flash('Link potwierdzający jest nieprawidłowy lub już wygasł.')
    return redirect(url_for('hello'))

@app.route('/reset', methods=['POST', 'GET'])
def reset():

    form=VerifyEmailForm()
    if form.validate_on_submit():

        #Sending a token to an e-mail to reset the password
        user=User.query.filter(User.mail == form.mail.data).first()
        token = user.generate_reset_token()
        send_email(user.mail, 'Zresetuj hasło','reset', user=user, token=token)
        flash("Na twój adres e-mail wysłano link do resetowania hasła")
        return render_template("pages/index.html", title_prefix = "Home")

    return render_template("verifyEmail.html", title_prefix = "Resetowanie hasła", form=form)

@app.route('/resetPassword/<token>', methods=['POST', 'GET'])
def resetPassword(token):

    form=NewPasswordForm()
    del form.oldPassword

    if form.validate_on_submit():

        #Token acceptance and password reset
        if User.reset_password(token, form.newPassword.data):
            db.session.commit()
            flash("Hasło zostało poprawnie zmienione. Możesz się zalogować")
            return redirect(url_for('login'))
        else:
            return redirect(url_for('hello'))

    return render_template("resetPassword.html", title_prefix = "Resetowanie hasła", form=form)

@app.route("/create", methods=['POST', 'GET'])
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

        token = newUser.generate_reset_token()
        send_email(newUser.mail, 'Potwierdź swoje konto','confirm', user=newUser, token=token)

        flash("Nowe konto zostało utworzone a na Twój adres e-mail wysłano prośbę o potwierdzenie konta ;)")
        return render_template("pages/index.html", title_prefix = "Home")

    return render_template('NewUserForm.html', form=form, title_prefix = "Nowe konto")

@app.route("/listOfUsers")
@login_required #This page needs to be login
def listOfUsers():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))

    avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

    users=User.query.all()
    return render_template('listOfUsers.html', avatarsPath=avatarsPath, users=users, title_prefix = "Lista użytkowników")

@app.route("/listOfCoefficients")
@login_required #This page needs to be login
def listOfCoefficients():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))

    names= []
    coefficients=CoefficientsList.query.all()
    for i in range (0, len(coefficients)):
        names.append(coefficients[i].setName)
    names= list(dict.fromkeys(names))
    return render_template('listOfCoefficients.html', coefficients=coefficients, title_prefix = "Lista współczynników", names=names)

@app.route("/coefficientsSetView/<name>")
@login_required #This page needs to be login
def coefficientsSetView(name):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))

    coefficientsSet=CoefficientsList.query.filter(CoefficientsList.setName == name).all()

    return render_template('/pages/coeficientSet_edit.html', title_prefix = name, name=name, CoefficientsSet=coefficientsSet)

@app.route("/deleteCoeficientsSet/<name>")
@login_required #This page needs to be login
def deleteCoefficientsSet(name):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))
    
    if name !="Podstawowy zestaw współczynników":

        coeficientsSet = CoefficientsList.query.filter(CoefficientsList.setName == name).all()
        for position in coeficientsSet:
            db.session.delete(position)

        db.session.commit()
        flash("Usutnięto zestaw współczynników {}".format(name))
    
    else:
        flash("Podstawowy zestaw współczynników nie może zostać usunięty!")
    return redirect(url_for('listOfCoefficients'))


@app.route("/deleteCoeficientSport/<int:coeficientID>")
@login_required #This page needs to be login
def deleteCoeficientSport(coeficientID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))

    positionToDelete = CoefficientsList.query.filter(CoefficientsList.id==coeficientID).first()
    db.session.delete(positionToDelete)
    db.session.commit()

    return redirect(url_for('coefficientsSetView', name=positionToDelete.setName))

@app.route("/modifyCoeficientSport/<int:coeficientID>", methods=['POST', 'GET'])
@login_required #This page needs to be login
def modifyCoeficientSport(coeficientID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))

    positionToModify = CoefficientsList.query.filter(CoefficientsList.id==coeficientID).first()

    form = CoeficientsForm(setName=positionToModify.setName,
        activityName = positionToModify.activityName,
        value = positionToModify.value,
        constant = positionToModify.constant )


    if form.validate_on_submit():

        positionToModify.value = form.value.data
        positionToModify.constant= form.constant.data
        db.session.commit()
    
        return redirect(url_for('coefficientsSetView', name=positionToModify.setName))

    flash("Nie usunieto!")
    return render_template("/pages/modify_coeficients.html", title_prefix = "Nowa tabela współczynników", form = form , coeficientID = coeficientID)



@app.route("/new_coeficients_table", methods=['POST','GET'])
@login_required #This page needs to be login
def createCoeficientsTable():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))

    form = NewCoeficientsSetForm()
    
    if form.validate_on_submit():

        nameExists = CoefficientsList.query.filter(CoefficientsList.setName == form.setName.data).first()
        if nameExists == None:
            basicTemplate = CoefficientsList.query.filter(CoefficientsList.setName == "Podstawowy zestaw współczynników").all()
            for actvityType in basicTemplate:
                newPosition = CoefficientsList(setName=form.setName.data, activityName=actvityType.activityName, value = actvityType.value, constant=actvityType.constant)
                db.session.add(newPosition)

            db.session.commit()
            flash('Dodano tabelę współczynników "{}"!'.format(form.setName.data))
            return redirect(url_for('coefficientsSetView', name = form.setName.data))
        
        else:
            flash("Zestaw o tej nazwie już istnieje. Podaj inną!")
            return redirect(url_for('createCoeficientsTable'))
    

    return render_template("/pages/new_coeficients.html", title_prefix = "Nowa tabela współczynników", form = form)


@app.route('/addNewSport/', methods=['POST','GET'])
@login_required #This page needs to be login
def addNewSport():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('hello'))

    form = CoeficientsForm(setName="Podstawowy zestaw współczynników")


    if form.validate_on_submit():
        newSport = CoefficientsList(setName=form.setName.data,
            activityName = form.activityName.data,
            value = form.value.data,
            constant = form.constant.data)

        db.session.add(newSport)
        db.session.commit()
        return redirect(url_for('coefficientsSetView', name="Podstawowy zestaw współczynników"))

    return render_template("/pages/new_sport.html", title_prefix = "Nowy sport", form = form) 



@app.route('/deleteUser/<userName>')
@login_required #This page needs to be login
def deleteUser(userName):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('hello'))

    userToDelete=User.query.filter(User.id == userName).first()
    if not userToDelete.isAdmin:
        db.session.delete(userToDelete)
        db.session.commit()
        flash("Użytkownik {} został usunięty z bazy danych".format(userToDelete.id))
    else:
        flash("Nie można usunąć użytkownika {}".format(userToDelete.id))

    return redirect(url_for('listOfUsers'))


@app.route('/deleteActivity/<int:activityID>')
@login_required #This page needs to be login
def deleteActivity(activityID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    activityToDelete=Activities.query.filter(Activities.id == activityID).first()
    db.session.delete(activityToDelete)
    db.session.commit()
    flash("Aktywność ({}) została usunięta z bazy danych".format(activityToDelete.activity))
  

    return redirect(url_for('myActivities'))


@app.route("/modifyActivity/<int:activityID>", methods=['POST','GET'])
@login_required #This page needs to be login
def modifyActivity(activityID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))
 
    activity = Activities.query.filter(Activities.id == activityID).first()

    # Creating list of available activities type
    availableActivityTypes = CoefficientsList.query.all()
    availableActivityTypes = [(a.activityName) for a in availableActivityTypes]
    availableActivityTypes = list(dict.fromkeys(availableActivityTypes))


    form = ActivityForm(date = activity.date,
                        activity = activity.activity,
                        distance = activity.distance,
                        time=activity.time)

    form.activity.choices= availableActivityTypes          
    

    if form.validate_on_submit():

        activity.date=form.date.data
        activity.activity=form.activity.data
        activity.distance=form.distance.data
        activity.time=form.time.data
        db.session.commit()
    
        flash('Zmodyfikowano aktywność: {}'.format(form.activity.data))
        return redirect(url_for('myActivities'))

    return render_template("addActivity.html", title_prefix = "Modyfikuj aktywność", form=form, mode="edit", activityID=activity.id)



@app.route("/login", methods=['POST', 'GET'])
def login():

    logForm=LoginForm()
    if logForm.validate_on_submit():
        user=User.query.filter(User.id == logForm.name.data).first()
        #password=User.query.filter(User.password == logForm.password.data).first()

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

            return redirect(url_for('basicDashboard'))
        else:
            flash("Nie udało się zalogować. Podaj pawidłowe dane")

    return render_template('login.html', logForm=logForm, title_prefix = "Zaloguj")


@app.route("/logout")
def logout():
    logout_user()
    flash("Wylogowałeś się")
    return render_template("pages/index.html", title_prefix = "Home")



@app.route("/new_event", methods=['POST','GET'])
@login_required #This page needs to be login
def createEvent():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))

    form = EventForm()
    formDist = DistancesForm()

    del form.status

    #Creating list of available admins (for form)
    admins=User.query.filter(User.isAdmin == True).all()
    adminIDs = [(a.id, a.name) for a in admins]
    form.adminID.choices=adminIDs

    #Creating list of available coefficients (for form)
    coefficients=CoefficientsList.query.filter(CoefficientsList.setName != "Podstawowy zestaw współczynników").all()
    coefficientIDs = [(c.setName) for c in coefficients]
    coefficientIDs = list(dict.fromkeys(coefficientIDs))

    form.coefficientsSetName.choices=coefficientIDs

    
    if form.validate_on_submit and formDist.validate_on_submit():

        passEventToDB(form, formDist)
    
        flash('Stworzono wydarzenie "{}"!'.format(form.name.data))
        return redirect(url_for('hello'))
    

    return render_template("/pages/new_event.html", title_prefix = "Nowe wydarzenie", form = form, formDist = formDist, mode = "create")


@app.route("/settings", methods=['POST','GET'])
@login_required #This page needs to be login
def settings():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

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
        return redirect(url_for('settings'))

    
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

        return redirect(url_for('settings'))

    return render_template("accountSettings.html", title_prefix = "Ustawienia konta", form=form, avatarsPath=avatarsPath, avatarForm=avatarForm, current_user=current_user)

@app.route("/passwordChange", methods=['POST','GET'])
@login_required #This page needs to be login
def passwordChange():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    form=NewPasswordForm(userName=current_user.id)

    if form.validate_on_submit():
        #update password in date base
        actualUser=User.query.filter(User.name == current_user.name).first()
        actualUser.password=form.newPassword.data
        actualUser.password=actualUser.hash_password()
        db.session.commit()

        flash("Hasło zmienione. Zaloguj się ponownie")
        return redirect(url_for('logout'))

    return render_template("passwordChange.html", title_prefix = "Prywatność", form=form)

@app.route("/addActivity", methods=['POST','GET'])
@login_required #This page needs to be login
def addActivity():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    form=ActivityForm()

    # Creating list of available activities type
    availableActivityTypes = CoefficientsList.query.all()
    availableActivityTypes = [(a.activityName) for a in availableActivityTypes]
    availableActivityTypes = list(dict.fromkeys(availableActivityTypes))

    form.activity.choices= availableActivityTypes


    form.userName=current_user.id

    if form.validate_on_submit():

        newActivity=Activities(date=form.date.data, week=1, activity=form.activity.data, distance=form.distance.data, 
                         time=form.time.data, userName=current_user.id)

        #adding new activity to datebase
        db.session.add(newActivity)
        db.session.commit()
        flash("Poprawnie dodano nową aktywność")

    return render_template("addActivity.html", title_prefix = "Dodaj aktywność", form=form, mode="create")



@app.route("/basicDashboard")
@login_required #This page needs to be login
def basicDashboard():

    if current_user.is_authenticated and not current_user.confirmed:
       
        return redirect(url_for('unconfirmed'))

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


@app.route("/myActivities")
@login_required #This page needs to be login
def myActivities():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    activities=Activities.query.filter(Activities.userName == current_user.id).all()

    if activities:
        sumDistance=0
        sumTime = datetime.timedelta()
        timeList=[]
        amount=len(activities)
        averageDistance=0
        averageTime=0

        for activity in activities:
            sumDistance=sumDistance+activity.distance
            timeList.append(str(activity.time))

        #Sum of total time of activities
        for time in timeList:
            (h, m, s) = time.split(':')
            d = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            sumTime += d


        #Calculation of basic data about the user's activities
        averageDistance=round(sumDistance/amount,2)
        averageTime=(sumTime/amount)

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


        today=datetime.date.today()
        dataList=[]
        dates=[]

        for dayActivity in range(10):
            distance=0
            for no in activities:
                date=today-datetime.timedelta(days=dayActivity)
                if date==no.date:
                    distance=distance+no.distance
            dataList.append(distance)
            dates.append(date)

        customStyle = Style(colors=["#30839f"])
        line_chart = pygal.Bar(fill=True, x_label_rotation=45, style=customStyle)
        line_chart.x_labels = map(str, dates)
        line_chart.add('Dystans [km]', dataList)


        #Render a URL adress for chart
        line_chart = line_chart.render_data_uri()


        return render_template('myActivities.html', activities=activities, title_prefix = "Moje aktywności", 
                                sumDistance=sumDistance, averageDistance=averageDistance, averageTime=averageTime, pie_chart=pie_chart, line_chart=line_chart)
        
    else:
        flash("Nie posiadasz dodanych żadnych aktywności")
        return redirect(url_for('hello'))


############################


@app.route("/eksploruj_wyzwania")
@login_required #This page needs to be login
def exploreEvents():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    events=Event.query.filter(Event.status == "Zapisy otwarte").filter(Event.isPrivate == False).filter().all()

    return render_template('/pages/explore_events.html', events=events, title_prefix = "Dostępne wyzwania" )


@app.route("/join_event/<int:eventID>")
@login_required #This page needs to be login
def joinEvent(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))
    
    event = Event.query.filter(Event.id == eventID).first()

    if event.status == "Zapisy otwarte":
        # Check is user isn't signed already
        isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()
        if isParticipating == None:

            addUserToEvent(current_user.id, eventID)
            send_email(current_user.mail, "Witaj w wyzwaniu {}".format(event.name),'welcome', event=event)
            flash("Zapisano do wyzwania " + event.name + "!")
            return redirect(url_for('viewEvent', eventID = eventID))

        else:
            flash("Już jesteś zapisny/a na to wyzwanie!")

        return redirect(url_for('exploreEvents'))

    else:
        flash('Wyzwanie "{}" już się rozpoczęło, nie możesz się do niego dopisać!'.format(event.name))
        return redirect(url_for('exploreEvents'))



@app.route("/leave_event/<int:eventID>")
@login_required
def leaveEvent(eventID):
    event = Event.query.filter(Event.id == eventID).first()

    # Check is user isn't signed already
    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()
    if isParticipating != None and event.status == "Zapisy otwarte":

        deleteUserFromEvent(isParticipating.id, eventID)
        flash("Wypisano się z wyzwania " + event.name + "!")

    elif isParticipating != None and event.status != "Zapisy otwarte":
        flash("Nie możesz się wypisać z tego wyzwania, gdyż zapisy na nie zostały zamknięte!")
    
    elif isParticipating == None:
        flash("Nie jesteś zapisany na to wyzwanie!")

    return redirect(url_for('exploreEvents'))



@app.route("/twoje_wyzwania/<mode>")
@login_required #This page needs to be login
def yourEvents(mode):

    userEvents = giveUserEvents(current_user.id )

    if userEvents != None:
        return render_template('/pages/your_events.html', events=userEvents, title_prefix = "Twoje wyzwania", mode  = mode)

    
    else:
       flash ("Nie bierzesz udziału w żadnych wyzwaniach. Zapisz się już dziś!")
       return redirect(url_for('exploreEvents'))

###############################

@app.route("/view_events/<int:eventID>")
@login_required
def viewEvent(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

    if isParticipating != None or current_user.isAdmin:

        event = Event.query.filter(Event.id == eventID).first()   
        eventUsers = giveEventParticipants(event.id)

        eventData=[]
        weekDays=[]
        targets=[]
        beerData=[]
        targetDone = False

        days = abs(datetime.date.today() - event.start).days
        presentWeek = math.ceil((days+1)/7) 

        weekStart = event.start + datetime.timedelta(weeks=1*presentWeek-1)
        weekEnd = event.start + datetime.timedelta(weeks=1*presentWeek-1, days=6)
        presentWeekActivities = Activities.query.filter(Activities.userName == current_user.id).filter(Activities.date >= weekStart).filter(Activities.date <= weekEnd).all()

        activitiesAmount = 0
        WeekDistance = 0
        #Create dictionary which keeps calculated distance of activity
        for position in presentWeekActivities:
            coef = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).filter(CoefficientsList.activityName == position.activity).first()
            if coef != None:
                if coef.constant == False:
                    WeekDistance = WeekDistance + (coef.value*position.distance)
                else: 
                    WeekDistance = WeekDistance + coef.value

        
        #3-D Array with data (weeks -> users -> days)
        for week in range (event.lengthWeeks):
            beerWeek = []
            currentWeek = []
            weekStart = event.start + datetime.timedelta(weeks=1*week)
            weekEnd = event.start + datetime.timedelta(weeks=1*week, days=6)
            coefSet = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).all()



            weekTarget = DistancesTable.query.filter(DistancesTable.event_ID == event.id).filter(DistancesTable.week == week+1).first()
            targets.append(weekTarget)

            oneWeekDays=[]
            for number in range(0,7):
                oneWeekDays.append([weekStart + datetime.timedelta(days=number), number])
            weekDays.append(oneWeekDays)


            for user in eventUsers:
                weekData = []
                userWeekSum = 0
               

                for j in range(0,7):
                    activities=Activities.query.filter(Activities.userName == user.id).filter(Activities.date == event.start + datetime.timedelta(weeks = week, days=j)).all()
                    dayDistance = 0

                    for position in activities:
                        coef = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).filter(CoefficientsList.activityName == position.activity).first()
                        activitiesAmount += 1
                        if coef != None:
                            if coef.constant == False:
                                dayDistance = dayDistance + (coef.value*position.distance)

                            else: 
                                dayDistance = dayDistance + coef.value
                    
                    if activities != None:
                        weekData.append(round(dayDistance,2))
                        userWeekSum += dayDistance

                    else:
                        weekData .append(0)

                weekData.append(round(userWeekSum,2))
                currentWeek.append(weekData)
                if weekData[7]>=weekTarget.value: 
                    beerWeek.append(1)
                else:
                    beerWeek.append(0)

            beerData.append(beerWeek)
            eventData.append(currentWeek)


        beerToBuy = []
        for i in range(0, len(eventUsers)):
            userRecive = 0
            userBuy = 0
            for weekB in range(0, event.lengthWeeks):
                if beerData[weekB][i] == 1:
                    userRecive = userRecive + beerData[weekB].count(0)
                elif beerData[weekB][i] == 0:
                    userBuy = userBuy + beerData[weekB].count(1)
            beerToBuy.append([userRecive,userBuy])

        print(beerData)
        print(beerToBuy)
        avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

        return render_template('/pages/event_view/event_main.html', event=event,avatarsPath=avatarsPath, weekDays=weekDays, title_prefix = event.name, eventUsers=eventUsers, eventData=eventData, targets=targets, usersAmount = len(eventUsers),
                activitiesAmount = activitiesAmount, coefSet =coefSet, presentWeek=presentWeek, WeekDistance=round(WeekDistance,2), today = datetime.date.today())
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('exploreEvents'))


@app.route("/event_activities/<int:eventID>")
@login_required #This page needs to be login
def eventActivities(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

    if isParticipating != None or current_user.isAdmin:

        event = Event.query.filter(Event.id == eventID).first()

        eventParticipantsUserNames = []
        eventParticipations = Participation.query.filter(Participation.event_id==event.id).all()

        for user in eventParticipations:
            eventParticipantsUserNames.append(user.user_name)

        activities=Activities.query.filter(Activities.userName.in_(eventParticipantsUserNames)).filter(Activities.date >= event.start).filter(Activities.date <= event.end).all()
        # for position in activities:
        #     nameToShow = User.query.filter(User.id == position.userName).first()
        #     position.userName = nameToShow.name

        calculatedDistance = {}
        
        #Create dictionary which keeps calculated distance of activity
        for position in activities:

            coef = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).filter(CoefficientsList.activityName == position.activity).first()
            if coef.constant == False:
                calculatedDistance.update({position.id:round(coef.value*position.distance,2)})
            else: 
                calculatedDistance.update({position.id:coef.value})

        return render_template('/pages/event_view/event_activities.html', activities=activities,calculatedDistance=calculatedDistance, event=event, title_prefix = "Aktywności wyzwania" )
        
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('exploreEvents'))

@app.route("/event_preview/<int:eventID>")
@login_required #This page needs to be login
def eventPreview(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    event = Event.query.filter(Event.id == eventID).first()
    eventUsers = giveEventParticipants(event.id)
    coefSet = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).all()
    weekTargets = DistancesTable.query.filter(DistancesTable.event_ID == event.id).all()

    return render_template('/pages/event_view/event_preview.html', event=event, title_prefix = event.name , usersAmount = len(eventUsers), coefSet =coefSet, weekTargets=weekTargets) 



@app.route("/event_statistics/<int:eventID>")
@login_required #This page needs to be login
def eventStatistics(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

    usersDistances = 2
    usersActivitiesAmount =(["Bob",20],["Bar",330])

    if isParticipating != None or current_user.isAdmin:

        event = Event.query.filter(Event.id == eventID).first()

        eventParticipantsUserNames = []
        eventParticipations = Participation.query.filter(Participation.event_id==event.id).all()

        usersDistances = []
        usersActivitiesAmount = []

        for user in eventParticipations:
            
            userCalculatedDistance = 0
            userAmount = 0
            userRow = []
            userRowAmount = []
            #eventParticipantsUserNames.append(user.user_name)
            userObject = User.query.filter(User.id == user.user_name).first()
            userName = userObject.name
            userSurname = userObject.lastName
            userActivities = Activities.query.filter(Activities.userName==user.user_name).filter(Activities.date >= event.start).filter(Activities.date <= event.end).all()

            for position in userActivities:
                
                coef = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).filter(CoefficientsList.activityName == position.activity).first()
                userAmount= userAmount +  1
                if coef.constant == False:
                    userCalculatedDistance = userCalculatedDistance +  round(coef.value*position.distance,2)
                else: 
                    userCalculatedDistance = userCalculatedDistance + coef.value
            # usersDistances.append(userObject.name)
            userRow = [userCalculatedDistance, userName + " " + userSurname]
            userRowAmount = [userAmount, userName + " " + userSurname]
            
            usersDistances.append(userRow)
            usersActivitiesAmount.append(userRowAmount)

        usersDistances.sort(key=lambda x:x[0], reverse=True)
        usersActivitiesAmount.sort(key=lambda x:x[0], reverse=True)
 

        return render_template('/pages/event_view/event_statistics.html', event=event, title_prefix = event.name , usersDistances = usersDistances, usersAmount = len(eventParticipations), usersActivitiesAmount=usersActivitiesAmount)
        
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('exploreEvents'))


@app.route("/event_contestants/<int:eventID>")
@login_required
def eventContestants(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

    if isParticipating != None or current_user.isAdmin:
    
        event = Event.query.filter(Event.id == eventID).first()
        eventUsers = giveEventParticipants(event.id)
        avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

        return render_template('/pages/event_view/event_contestants.html', event=event,avatarsPath=avatarsPath, eventUsers=eventUsers, title_prefix = event.name, current_user=current_user )

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('exploreEvents'))

@app.route("/event_beers/<int:eventID>")
@login_required
def eventBeers(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

    if isParticipating != None or current_user.isAdmin:

        event = Event.query.filter(Event.id == eventID).first()   
        eventUsers = giveEventParticipants(event.id)

        eventData=[]
        weekDays=[]
        targets=[]
        beerData=[]
        targetDone = False

        days = abs(datetime.date.today() - event.start).days
        presentWeek = math.ceil((days+1)/7) 

        weekStart = event.start + datetime.timedelta(weeks=1*presentWeek-1)
        weekEnd = event.start + datetime.timedelta(weeks=1*presentWeek-1, days=6)
        presentWeekActivities = Activities.query.filter(Activities.userName == current_user.id).filter(Activities.date >= weekStart).filter(Activities.date <= weekEnd).all()

        activitiesAmount = 0
        WeekDistance = 0
        #Create dictionary which keeps calculated distance of activity
        for position in presentWeekActivities:
            coef = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).filter(CoefficientsList.activityName == position.activity).first()
            if coef != None:
                if coef.constant == False:
                    WeekDistance = WeekDistance + (coef.value*position.distance)
                else: 
                    WeekDistance = WeekDistance + coef.value

        
        #3-D Array with data (weeks -> users -> days)
        for week in range (event.lengthWeeks):
            beerWeek = []
            currentWeek = []
            weekStart = event.start + datetime.timedelta(weeks=1*week)
            weekEnd = event.start + datetime.timedelta(weeks=1*week, days=6)
            coefSet = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).all()



            weekTarget = DistancesTable.query.filter(DistancesTable.event_ID == event.id).filter(DistancesTable.week == week+1).first()
            targets.append(weekTarget)

            oneWeekDays=[]
            for number in range(0,7):
                oneWeekDays.append([weekStart + datetime.timedelta(days=number), number])
            weekDays.append(oneWeekDays)


            for user in eventUsers:
                weekData = []
                userWeekSum = 0
               

                for j in range(0,7):
                    activities=Activities.query.filter(Activities.userName == user.id).filter(Activities.date == event.start + datetime.timedelta(weeks = week, days=j)).all()
                    dayDistance = 0

                    for position in activities:
                        coef = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).filter(CoefficientsList.activityName == position.activity).first()
                        activitiesAmount += 1
                        if coef != None:
                            if coef.constant == False:
                                dayDistance = dayDistance + (coef.value*position.distance)

                            else: 
                                dayDistance = dayDistance + coef.value
                    
                    if activities != None:
                        weekData.append(round(dayDistance,2))
                        userWeekSum += dayDistance

                    else:
                        weekData .append(0)

                weekData.append(round(userWeekSum,2))
                currentWeek.append(weekData)
                if weekData[7]>=weekTarget.value: 
                    beerWeek.append(1)
                else:
                    beerWeek.append(0)

            beerData.append(beerWeek)
            eventData.append(currentWeek)


        beerToBuy = []
        for i in range(0, len(eventUsers)):
            userRecive = 0
            userBuy = 0
            for weekB in range(0, event.lengthWeeks):
                if beerData[weekB][i] == 1:
                    userRecive = userRecive + beerData[weekB].count(0)
                elif beerData[weekB][i] == 0:
                    userBuy = userBuy + beerData[weekB].count(1)
            beerToBuy.append([userRecive,userBuy])

        print(beerData)
        print(beerToBuy)
        avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

        return render_template('/pages/event_view/event_beers.html', event=event,avatarsPath=avatarsPath, eventUsers=eventUsers, title_prefix = event.name, current_user=current_user, beerToBuy=beerToBuy)

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('exploreEvents'))

##################################


@app.route("/admin_event_list")
@login_required #This page needs to be login
def adminListOfEvents():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))

    events=Event.query.all()
    return render_template('/pages/admin_events.html', events=events, title_prefix = "Lista wyzwań")




@app.route("/admin_delete_contestant/<int:eventID>/<userID>")
@login_required
def adminDeleteContestant(eventID, userID):
    event = Event.query.filter(Event.id == eventID).first()


    # Check is user isn't signed already
    isParticipating = Participation.query.filter(Participation.user_name == userID).filter(Participation.event_id == eventID).first()

    if isParticipating != None:
        deleteUserFromEvent(isParticipating.id, eventID)
        flash("Usunięto użytkownika {} z wyzwania {}".format(isParticipating.user_name, event.name))
    
    elif isParticipating == None:
        flash("Użytkownik {} nie jest zapisany na wyzwanie {}!".format(userID, event.name))

    return redirect(url_for('eventContestants', eventID=eventID))



@app.route("/delete_event/<int:eventID>")
@login_required #This page needs to be login
def adminDeleteEvent(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))
    
    event = Event.query.filter(Event.id == eventID).first()

    deleteEvent(event)

    flash("Usunięto wyzwanie {}!".format(event.name))

    return redirect(url_for('adminListOfEvents'))



@app.route("/modify_event/<int:eventID>", methods=['POST','GET'])
@login_required #This page needs to be login
def adminModifyEvent(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('hello'))
    
    event = Event.query.filter(Event.id == eventID).first()
    
    distanceSet = DistancesTable.query.filter(DistancesTable.event_ID == event.id).all()

    form = EventForm(name = event.name,
            start = event.start,
            length = event.lengthWeeks)

    formDist = DistancesForm(w1 = distanceSet[0].value,
    w2 = distanceSet[1].value,
    w3 = distanceSet[2].value,
    w4 = distanceSet[3].value,
    w5 = distanceSet[4].value,
    w6 = distanceSet[5].value,
    w7 = distanceSet[6].value,
    w8 = distanceSet[7].value,
    w9 = distanceSet[8].value,
    w10 = distanceSet[9].value,
    w11 = distanceSet[10].value,
    w12 = distanceSet[11].value,
    w13 = distanceSet[12].value,
    w14 = distanceSet[13].value,
    w15 = distanceSet[14].value)

    #Creating list of available admins (for form)
    admins=User.query.filter(User.isAdmin == True).all()
    adminIDs = [(a.id, a.name) for a in admins]
    form.adminID.choices=adminIDs

    #Creating list of available coefficients (for form)
    coefficients=CoefficientsList.query.all()
    coefficientIDs = [(c.setName) for c in coefficients]
    coefficientIDs = list(dict.fromkeys(coefficientIDs))

    form.status.choices = eventStatusOptions

    form.coefficientsSetName.choices=coefficientIDs

    if form.validate_on_submit and formDist.validate_on_submit():

        changeEvent(event.id, form, formDist)
    
        flash('Zmodyfikowano wydarzenie "{}"!'.format(form.name.data))
        return redirect(url_for('hello'))

    return render_template("/pages/modify_event.html", title_prefix = "Modfyfikuj wydarzenie", form = form, formDist=formDist, mode = "edit", eventID=event.id)


##################################

@app.route("/sendMessage", methods=['POST','GET'])
def sendMessage():

    if current_user.is_authenticated:
        form=MessageForm(name=current_user.name, lastName=current_user.lastName, mail=current_user.mail)
    else:
        form=MessageForm()

    if form.validate_on_submit():

        admins=User.query.filter(User.isAdmin == True).all()

        for admin in admins:
            send_email("admin@sportoweswiry.atthost24.pl", "Wiadomość od użytkownika {} {} - {}".format(form.name.data, form.lastName.data, form.subject.data),'message', 
                        name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, message=form.message.data)

        
        flash("Wiadomość została wysłana. Odpowiemy najszybciej jak to możliwe.")
        return redirect(url_for('hello'))

    return render_template('/sendMessage.html', form=form, title_prefix = "Formularz kontaktowy" )


@app.route("/faq")
def faq():

    return render_template('/pages/faq.html', title_prefix = "FAQ" )

@app.route("/about")
def about():

    return render_template('/pages/about.html', title_prefix = "FAQ" )


@app.route("/test")
@login_required #This page needs to be login
def TEST():

    createCofficientTemplate()

    return render_template('/pages/index.html', title_prefix = "Twoje wyzwania" )


if __name__ == "__main__":
    app.debug = True
    app.run()
