
from start import db
from event.classes import CoefficientsList, Event, DistancesTable, Participation, User

from datetime import timedelta

def passCoefficientsTableToDB(form):

    newCoeficentTable = CoefficientsList(name = form.name.data,
        running = form.running.data,
        runningIsConstant = form.runningIsConstant.data,
        trailRunning = form.trailRunning.data,
        trailRunningIsConstant = form.trailRunningIsConstant.data,
        walking = form.walking.data,
        walkingIsConstant = form.walkingIsConstant.data,
        trekking = form.trekking.data,
        trekkingIsConstant = form.trekkingIsConstant.data,
        cycling = form.cycling.data,
        cyclingIsConstant =  form.cyclingIsConstant.data,
        moutainBike = form.moutainBike.data,
        moutainBikeIsConstant=form.moutainBikeIsConstant.data,
        swimming = form.swimming.data,
        swimmingIsConstant = form.swimmingIsConstant.data,
        skiing = form.skiing.data,
        skiingIsConstant = form.skiingIsConstant.data,
        squash = form.squash.data,
        squashIsConstant = form.squashIsConstant.data,
        football = form.football.data,
        footballIsConstant = form.footballIsConstant.data,
        fitness = form.fitness.data,
        fitnessIsConstant = form.fitnessIsConstant.data)  

    db.session.add(newCoeficentTable)
    db.session.commit()

    return newCoeficentTable

# Function which fill database with information from user + standarized values
def passEventToDB(form, formDist):

    newEvent = Event(name = form.name.data,
        start = form.start.data,
        lengthWeeks = form.length.data,
        end = form.start.data + timedelta(weeks = form.length.data, days=-1), 
        adminID = form.adminID.data,
        isPrivate = form.isPrivate.data,
        isSecret = form.isSecret.data,
        coefficientsSetName = form.coefficientsSetName.data,
        maxUserAmount = 0,
        status = "Zapisy otwarte") 


    db.session.add(newEvent)
    db.session.commit()

    passDistancesToDB(formDist, Event.query.order_by(Event.id.desc()).first().id)

    return newEvent.id

def changeEvent(eventID, form, formDist):

    eventToChange = Event.query.filter(Event.id==eventID).first()

    oldDistances =  DistancesTable.query.filter(DistancesTable.event_ID == eventID).all()
    for position in oldDistances:
        db.session.delete(position)
        db.session.commit()

    passDistancesToDB(formDist, eventID)

    eventToChange.name = form.name.data
    eventToChange.start = form.start.data
    eventToChange.lengthWeeks = form.length.data,
    eventToChange.end = form.start.data + timedelta(weeks = form.length.data, days=-1)
    eventToChange.adminID = form.adminID.data,
    eventToChange.isPrivate = form.isPrivate.data
    eventToChange.isSecret = form.isSecret.data
    eventToChange.coefficientsSetName = form.coefficientsSetName.data
    eventToChange.status = form.status.data

    db.session.commit()

    return eventToChange.id

def deleteEvent(eventToDelete):
    
    db.session.delete(eventToDelete)
    db.session.commit()

    return None

def deleteUserFromEvent(positionID, eventID):

    position = Participation.query.filter(Participation.event_id==eventID).filter(Participation.id==positionID).first()
    db.session.delete(position)
    db.session.commit()

def passDistancesToDB(formDist, eventID):

    print(eventID)
    newDistance = DistancesTable(event_ID = eventID, week = 1, value = formDist.w1.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 2, value = formDist.w2.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 3, value = formDist.w3.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 4, value = formDist.w4.data )
    db.session.add(newDistance)
    db.session.commit()
    
    newDistance = DistancesTable(event_ID = eventID, week = 5, value = formDist.w5.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 6, value = formDist.w6.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 7, value = formDist.w7.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 8, value = formDist.w8.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 9, value = formDist.w9.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 10, value = formDist.w10.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 11, value = formDist.w11.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 12, value = formDist.w12.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 13, value = formDist.w13.data )
    db.session.add(newDistance)
    db.session.commit()

    newDistance = DistancesTable(event_ID = eventID, week = 14, value = formDist.w14.data )
    db.session.add(newDistance)
    db.session.commit()
    
    newDistance = DistancesTable(event_ID = eventID, week = 15, value = formDist.w15.data )
    db.session.add(newDistance)
    db.session.commit()

def addUserToEvent(userName, eventID):

    participation = Participation(user_name = userName, event_id = eventID)
    db.session.add(participation)
    db.session.commit()

    return None

def createCofficientTemplate():
    
    if CoefficientsList.query.all() == []:

        standardSetCoef = {'Bieg':1,
         'Bieg Trailowy':1.25,
         'Spacer':0.5,
         'Trekking':0.625,
         'Kolarstwo':0.3,
         'Kolarstwo górskie':0.4,
         'Pływanie':5.00}

        standardSetConst = {'Fitness':5,
         'Piłka nożna':5,
         'Squash':5,
         'Siatkówka':5,
         'Badminton':5,
         'Narciarstwo zjadowe':5}


        for type in standardSetCoef:
            coefficient = CoefficientsList(setName = "Podstawowy zestaw współczynników", activityName = type, value = standardSetCoef[type], constant = False)
            db.session.add(coefficient)
            db.session.commit()

        for type in standardSetConst:
            coefficient = CoefficientsList(setName = "Podstawowy zestaw współczynników", activityName = type, value = standardSetConst[type], constant = True)
            db.session.add(coefficient)
            db.session.commit()


        print("NIE MA!")

    return None

def giveUserEvents(userID, eventStatus="all"):

    userEventsNames=[]
    userParticipations = Participation.query.filter(Participation.user_name == userID).all()

    if userParticipations == []:
        return None

    #Creates list of events id in which user takes part
    for event in userParticipations:
        userEventsNames.append(event.event_id)
    if eventStatus =="all":
        userEvents = Event.query.filter(Event.id.in_(userEventsNames)).all()
    elif eventStatus == "ongoing":
        userEvents = Event.query.filter(Event.id.in_(userEventsNames)).filter(db.or_(Event.status=="W trakcie", Event.status=="Zapisy otwarte")).all()
    elif eventStatus == "finished":
        userEvents = Event.query.filter(Event.id.in_(userEventsNames)).filter(Event.status=="Zakończone").all()


    return userEvents

def giveEventParticipants(eventID):


    eventParticipantsUserNames = []
    eventParticipations = Participation.query.filter(Participation.event_id==eventID).all()

    for user in eventParticipations:
        eventParticipantsUserNames.append(user.user_name)

    eventUsers = User.query.filter(User.id.in_(eventParticipantsUserNames)).all()

    return eventUsers