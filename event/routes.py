from dataclasses import replace
import datetime
import math
import string

from flask_login import current_user
from start import db, app
from flask import Blueprint, render_template, redirect, url_for, flash
from .classes import CoefficientsList, Event, Participation, User, DistancesTable
from .forms import CoeficientsForm, DistancesForm, EventForm, NewCoeficientsSetForm
from flask_login import login_required, current_user
from .functions import passEventToDB, addUserToEvent, deleteEvent, changeEvent, giveUserEvents, giveEventParticipants, deleteUserFromEvent
from activity.classes import Activities
from other.functions import send_email
from urllib.parse import unquote

import os


event = Blueprint("event", __name__,
    template_folder='templates')


eventStatusOptions = ['Zapisy otwarte', 'W trakcie', 'Zakończone']


@event.route("/new_coeficients_table", methods=['POST','GET'])
@login_required #This page needs to be login
def createCoeficientsTable():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    form = NewCoeficientsSetForm()
    
    if form.validate_on_submit():

        nameExists = CoefficientsList.query.filter(CoefficientsList.setName == form.setName.data).first()
        if nameExists == None:
            basicTemplate = CoefficientsList.query.filter(CoefficientsList.setName == "Podstawowy zestaw współczynników").all()
            for actvityType in basicTemplate:
                newPosition = CoefficientsList(setName=form.setName.data, activityName=actvityType.activityName, value = actvityType.value, constant=actvityType.constant)
                db.session.add(newPosition)

            db.session.commit()
            #flash('Dodano tabelę współczynników "{}"!'.format(str(form.setName.data)))
            flash("123!")
            return redirect(url_for('event.coefficientsSetView', setName = form.setName.data))
        
        else:
            flash("Zestaw o tej nazwie już istnieje. Podaj inną!")
            return redirect(url_for('event.createCoeficientsTable'))
    

    return render_template("/pages/new_coeficients.html", title_prefix = "Nowa tabela współczynników", form = form)
    

@event.route("/explore_events")
@login_required #This page needs to be login
def exploreEvents():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    events=Event.query.filter(Event.status == "Zapisy otwarte").filter(Event.isPrivate == False).filter().all()

    return render_template('/pages/explore_events.html', events=events, title_prefix = "Dostępne wyzwania" )


@event.route("/join_event/<int:eventID>")
@login_required #This page needs to be login
def joinEvent(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))
    
    event = Event.query.filter(Event.id == eventID).first()

    if event.status == "Zapisy otwarte":
        # Check is user isn't signed already
        isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()
        if isParticipating == None:

            addUserToEvent(current_user.id, eventID)
            send_email(current_user.mail, "Witaj w wyzwaniu {}".format(event.name),'welcome', event=event)
            flash("Zapisano do wyzwania " + event.name + "!")
            return redirect(url_for('event.viewEvent', eventID = eventID))

        else:
            flash("Już jesteś zapisny/a na to wyzwanie!")

        return redirect(url_for('event.exploreEvents'))

    else:
        flash('Wyzwanie "{}" już się rozpoczęło, nie możesz się do niego dopisać!'.format(event.name))
        return redirect(url_for('event.exploreEvents'))



@event.route("/leave_event/<int:eventID>")
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



@event.route("/your_events/<mode>")
@login_required #This page needs to be login
def yourEvents(mode):

    userEvents = giveUserEvents(current_user.id, mode)

    if userEvents != None:
        return render_template('/pages/your_events.html', events=userEvents, title_prefix = "Twoje wyzwania", mode  = mode)

    
    else:
       flash ("Nie bierzesz udziału w żadnych wyzwaniach. Zapisz się już dziś!")
       return redirect(url_for('event.exploreEvents'))

###############################

@event.route("/view_events/<int:eventID>")
@login_required
def viewEvent(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

    if isParticipating != None or current_user.isAdmin:

        event = Event.query.filter(Event.id == eventID).first()   
        eventUsers = giveEventParticipants(event.id)

        eventData=[]
        weekDays=[]
        targets=[]
        beerData=[]
        targetDone = False

        if datetime.date.today() >= event.start:
            days = abs(datetime.date.today() - event.start).days
            presentWeek = math.ceil((days+1)/7) 
        else:
            presentWeek = 0

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

        avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

        return render_template('/pages/event_view/event_main.html', event=event,avatarsPath=avatarsPath, weekDays=weekDays, title_prefix = event.name, eventUsers=eventUsers, eventData=eventData, targets=targets, usersAmount = len(eventUsers),
                activitiesAmount = activitiesAmount, coefSet =coefSet, presentWeek=presentWeek, WeekDistance=round(WeekDistance,2), today = datetime.date.today())
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.exploreEvents'))


@event.route("/event_activities/<int:eventID>")
@login_required #This page needs to be login
def eventActivities(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

    if isParticipating != None or current_user.isAdmin:

        event = Event.query.filter(Event.id == eventID).first()

        eventParticipantsUserNames = []
        eventParticipations = Participation.query.filter(Participation.event_id==event.id).all()

        eventActivityTypes = []
        eventSports = CoefficientsList.query.filter(CoefficientsList.setName==event.coefficientsSetName).all()

        for sport in eventSports:
            eventActivityTypes.append(sport.activityName)

        for user in eventParticipations:
            eventParticipantsUserNames.append(user.user_name)

        activities=Activities.query.filter(Activities.userName.in_(eventParticipantsUserNames)) \
            .filter(Activities.date >= event.start) \
            .filter(Activities.date <= event.end) \
            .filter(Activities.activity.in_(eventActivityTypes)) \
            .order_by(Activities.date.desc()).all()
        
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
        return redirect(url_for('event.exploreEvents'))

@event.route("/event_preview/<int:eventID>")
@login_required #This page needs to be login
def eventPreview(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    event = Event.query.filter(Event.id == eventID).first()
    eventUsers = giveEventParticipants(event.id)
    coefSet = CoefficientsList.query.filter(CoefficientsList.setName == event.coefficientsSetName).all()
    weekTargets = DistancesTable.query.filter(DistancesTable.event_ID == event.id).all()

    return render_template('/pages/event_view/event_preview.html', event=event, title_prefix = event.name , usersAmount = len(eventUsers), coefSet =coefSet, weekTargets=weekTargets) 



@event.route("/event_statistics/<int:eventID>")
@login_required #This page needs to be login
def eventStatistics(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

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
                if coef != None:
                    if coef.constant == False:
                        userCalculatedDistance = userCalculatedDistance +  round(coef.value*position.distance,2)
                    else: 
                        userCalculatedDistance = userCalculatedDistance + coef.value

            # usersDistances.append(userObject.name)
            userRow = [round(userCalculatedDistance,2), userName + " " + userSurname]
            userRowAmount = [userAmount, userName + " " + userSurname]
            
            usersDistances.append(userRow)
            usersActivitiesAmount.append(userRowAmount)

        usersDistances.sort(key=lambda x:x[0], reverse=True)
        usersActivitiesAmount.sort(key=lambda x:x[0], reverse=True)
 

        return render_template('/pages/event_view/event_statistics.html', event=event, title_prefix = event.name , usersDistances = usersDistances, usersAmount = len(eventParticipations), usersActivitiesAmount=usersActivitiesAmount)
        
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('exploreEvents'))


@event.route("/event_contestants/<int:eventID>")
@login_required
def eventContestants(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    isParticipating = Participation.query.filter(Participation.user_name == current_user.id).filter(Participation.event_id == eventID).first()

    if isParticipating != None or current_user.isAdmin:
    
        event = Event.query.filter(Event.id == eventID).first()
        eventUsers = giveEventParticipants(event.id)
        avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

        return render_template('/pages/event_view/event_contestants.html', event=event,avatarsPath=avatarsPath, eventUsers=eventUsers, title_prefix = event.name, current_user=current_user )

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.exploreEvents'))

@event.route("/event_beers/<int:eventID>")
@login_required
def eventBeers(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

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


        avatarsPath = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

        return render_template('/pages/event_view/event_beers.html', event=event,avatarsPath=avatarsPath, eventUsers=eventUsers, title_prefix = event.name, current_user=current_user, beerToBuy=beerToBuy)

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.exploreEvents'))


@event.route("/new_event", methods=['POST','GET'])
@login_required #This page needs to be login
def createEvent():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

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
        return redirect(url_for('other.hello'))
    

    return render_template("/pages/new_event.html", title_prefix = "Nowe wydarzenie", form = form, formDist = formDist, mode = "create")


@event.route("/admin_event_list")
@login_required #This page needs to be login
def adminListOfEvents():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    events=Event.query.all()
    return render_template('/pages/admin_events.html', events=events, title_prefix = "Lista wyzwań")


    

@event.route("/admin_delete_contestant/<int:eventID>/<userID>")
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



@event.route("/delete_event/<int:eventID>")
@login_required #This page needs to be login
def adminDeleteEvent(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))
    
    event = Event.query.filter(Event.id == eventID).first()

    deleteEvent(event)

    flash("Usunięto wyzwanie {}!".format(event.name))

    return redirect(url_for('event.adminListOfEvents'))



@event.route("/modify_event/<int:eventID>", methods=['POST','GET'])
@login_required #This page needs to be login
def adminModifyEvent(eventID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))
    
    event = Event.query.filter(Event.id == eventID).first()
    
    distanceSet = DistancesTable.query.filter(DistancesTable.event_ID == event.id).all()

    form = EventForm(name = event.name,
            start = event.start,
            length = event.lengthWeeks,
            status = event.status)

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
        return redirect(url_for('event.adminListOfEvents'))

    return render_template("/pages/modify_event.html", title_prefix = "Modfyfikuj wydarzenie", form = form, formDist=formDist, mode = "edit", eventID=event.id)


@event.route("/listOfCoefficients")
@login_required #This page needs to be login
def listOfCoefficients():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    names= []
    coefficients=CoefficientsList.query.all()
    for i in range (0, len(coefficients)):
        names.append(coefficients[i].setName)
    names= list(dict.fromkeys(names))
    return render_template('/pages/listOfCoefficients.html', coefficients=coefficients, title_prefix = "Lista współczynników", names=names)

@event.route("/coefficientsSetView/<setName>")
@login_required #This page needs to be login
def coefficientsSetView(setName):

    correctedSetName = unquote(setName)

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    coefficientsSet=CoefficientsList.query.filter(CoefficientsList.setName == correctedSetName).all()
    return render_template('/pages/coeficientSet_edit.html', title_prefix = correctedSetName, name=correctedSetName, CoefficientsSet=coefficientsSet)

@event.route("/deleteCoeficientsSet/<setName>")
@login_required #This page needs to be login
def deleteCoefficientsSet(setName):

    correctedSetName = unquote(setName)
    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))
    
    if correctedSetName !="Podstawowy zestaw współczynników":

        coeficientsSet = CoefficientsList.query.filter(CoefficientsList.setName == correctedSetName).all()
        for position in coeficientsSet:
            db.session.delete(position)

        db.session.commit()
        flash("Usutnięto zestaw współczynników {}".format(correctedSetName))
    
    else:
        flash("Podstawowy zestaw współczynników nie może zostać usunięty!")
    return redirect(url_for('event.listOfCoefficients'))


@event.route("/deleteCoeficientSport/<int:coeficientID>")
@login_required #This page needs to be login
def deleteCoeficientSport(coeficientID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    positionToDelete = CoefficientsList.query.filter(CoefficientsList.id==coeficientID).first()
    db.session.delete(positionToDelete)
    db.session.commit()

    return redirect(url_for('event.coefficientsSetView', name=positionToDelete.setName))

@event.route("/modifyCoeficientSport/<int:coeficientID>", methods=['POST', 'GET'])
@login_required #This page needs to be login
def modifyCoeficientSport(coeficientID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    positionToModify = CoefficientsList.query.filter(CoefficientsList.id==coeficientID).first()

    form = CoeficientsForm(setName=positionToModify.setName,
        activityName = positionToModify.activityName,
        value = positionToModify.value,
        constant = positionToModify.constant )


    if form.validate_on_submit():

        positionToModify.value = form.value.data
        positionToModify.constant= form.constant.data
        db.session.commit()
    
        return redirect(url_for('event.coefficientsSetView', name=positionToModify.setName))

    flash("Nie usunieto!")
    return render_template("/pages/modify_coeficients.html", title_prefix = "Nowa tabela współczynników", form = form , coeficientID = coeficientID)


@event.route('/addNewSport/', methods=['POST','GET'])
@login_required #This page needs to be login
def addNewSport():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if not current_user.isAdmin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    form = CoeficientsForm(setName="Podstawowy zestaw współczynników")


    if form.validate_on_submit():
        newSport = CoefficientsList(setName=form.setName.data,
            activityName = form.activityName.data,
            value = form.value.data,
            constant = form.constant.data)

        db.session.add(newSport)
        db.session.commit()
        return redirect(url_for('event.coefficientsSetView', name="Podstawowy zestaw współczynników"))

    return render_template("/pages/new_sport.html", title_prefix = "Nowy sport", form = form) 