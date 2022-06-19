from start import db
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from activity.classes import Activities
from activity.forms import ActivityForm
from event.classes import CoefficientsList, DistancesTable
from event.functions import giveUserEvents


import pygal
from pygal.style import Style
import datetime
import math

activity = Blueprint("activity", __name__,
    template_folder='templates')


@activity.route('/deleteActivity/<int:activityID>')
@login_required #This page needs to be login
def deleteActivity(activityID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    activityToDelete=Activities.query.filter(Activities.id == activityID).first()
    db.session.delete(activityToDelete)
    db.session.commit()
    flash("Aktywność ({}) została usunięta z bazy danych".format(activityToDelete.activity))
  

    return redirect(url_for('activity.myActivities'))


@activity.route("/modifyActivity/<int:activityID>", methods=['POST','GET'])
@login_required #This page needs to be login
def modifyActivity(activityID):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))
 
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
        return redirect(url_for('activity.myActivities'))

    return render_template("/pages/addActivity.html", title_prefix = "Modyfikuj aktywność", form=form, mode="edit", activityID=activity.id)


@activity.route("/addActivity", methods=['POST','GET'])
@login_required #This page needs to be login
def addActivity():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    form=ActivityForm()

    # Creating list of available activities type
    availableActivityTypes = CoefficientsList.query.all()
    availableActivityTypes = [(a.activityName) for a in availableActivityTypes]
    availableActivityTypes = list(dict.fromkeys(availableActivityTypes))

    form.activity.choices= availableActivityTypes


    form.userName=current_user.id

     #Return list of user events
    userEvents = giveUserEvents(current_user.id)
    activities=Activities.query.filter(Activities.userName == current_user.id).all()
    #Return array with data to event data to present

    eventNames = {}
    eventWeek = {}
    eventWeekDistance = {}
    eventWeekTarget = {}

    if form.validate_on_submit():

        newActivity=Activities(date=form.date.data, week=1, activity=form.activity.data, distance=form.distance.data, 
                         time=form.time.data, userName=current_user.id)

        #adding new activity to datebase
        db.session.add(newActivity)
        db.session.commit()
        flash("Poprawnie dodano nową aktywność")
        return  redirect(url_for('activity.addActivity'))


    if userEvents != None:

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

        return render_template("/pages/addActivity.html", title_prefix = "Dodaj aktywność", form=form, mode="create" , activities=activities, 
                            today_7 = datetime.date.today() + datetime.timedelta(days=-7), eventsNames=eventNames, events=userEvents, eventWeek=eventWeek, eventWeekDistance=eventWeekDistance, eventWeekTarget=eventWeekTarget, menuMode="mainApp")
    
    else:
        return render_template('/pages/addActivity.html', form=form, mode="create", title_prefix = "Dodaj aktywnośćd", menuMode="mainApp")



@activity.route("/myActivities")
@login_required #This page needs to be login
def myActivities():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

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

        try:
            (h, m, s) = str(averageTime).split(':')
            (s1, s2)=s.split(".") #s1-seconds, s2-miliseconds
            averageTime= datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s1))
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


        return render_template('/pages/myActivities.html', activities=activities, title_prefix = "Moje aktywności", 
                                sumDistance=sumDistance, averageDistance=averageDistance, averageTime=averageTime, pie_chart=pie_chart, line_chart=line_chart)
        
    else:
        return redirect(url_for('other.hello'))