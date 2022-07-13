from configparser import ConverterMapping
from itertools import count
import re
import os
from start import app, db
from ssl import ALERT_DESCRIPTION_UNSUPPORTED_CERTIFICATE
from start import db
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from activity.classes import Activities
from activity.forms import ActivityForm
from event.classes import CoefficientsList, DistancesTable
from event.functions import giveUserEvents

from .strava import addStravaActivitiesToDB, getActivitiesFromStrava, getLastStravaActivityDate, getStravaAccessToken, convertStravaData

import json
import requests

import pandas as pd
from pandas import json_normalize

import pygal
from pygal.style import Style
import datetime as dt
import math

import urllib3

from urllib.parse import urlparse, parse_qs

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

    if 'eventCount' in request.args:
        try:
            eventCount = int(request.args['eventCount'])
        except:
            eventCount = 0
    
    else:
        eventCount = 0

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

        newActivity=Activities(date=form.date.data, activity=form.activity.data, distance=form.distance.data, 
                         time=form.time.data, userName=current_user.id)

        #adding new activity to datebase
        db.session.add(newActivity)
        db.session.commit()
        flash("Poprawnie dodano nową aktywność")
        return  redirect(url_for('activity.addActivity'))


    if userEvents != None:

        for event in userEvents:

            #Defines present week of event
            days = abs(dt.date.today() - event.start).days
            week = math.ceil((days+1)/7) 
            weekStart = event.start + dt.timedelta(weeks=1*week-1)
            weekEnd = event.start + dt.timedelta(weeks=1*week-1, days=6)
    
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
                            today_7 = dt.date.today() + dt.timedelta(days=-7), event=userEvents[eventCount], eventsNames=eventNames, events=userEvents, eventWeek=eventWeek, eventWeekDistance=eventWeekDistance, eventWeekTarget=eventWeekTarget, menuMode="mainApp")
    
    else:
        return render_template('/pages/addActivity.html', form=form, mode="create", title_prefix = "Dodaj aktywność")



@activity.route("/myActivities")
@login_required #This page needs to be login
def myActivities():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    activities=Activities.query.filter(Activities.userName == current_user.id).all()

    if activities:
        sumDistance=0
        sumTime = dt.timedelta()
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
            d = dt.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            sumTime += d


        #Calculation of basic data about the user's activities
        averageDistance=round(sumDistance/amount,2)
        averageTime=(sumTime/amount)

        try:
            (h, m, s) = str(averageTime).split(':')
            (s1, s2)=s.split(".") #s1-seconds, s2-miliseconds
            averageTime= dt.timedelta(hours=int(h), minutes=int(m), seconds=int(s1))
        except:
            print("Something went wrong")

        sumDistance=round(sumDistance,2)

        checkTable=[]

        kindOfActivities=[]
        percentsOfActivities=[]

        #calculation of the percentage of activity
        for activityExternal in activities:
            quantity=0
            for activityInternal in activities:
                if activityExternal.activity==activityInternal.activity and not activityExternal.activity in checkTable:
                    quantity=quantity+1
            if quantity>0:
                kindOfActivities.append(activityExternal.activity)
                percentsOfActivities.append(round((quantity/amount)*100,1))
                checkTable.append(activityExternal.activity)
        

        today=dt.date.today()
        dataList=[]
        dates=[]

        for dayActivity in range(10):
            distance=0
            for no in activities:
                date=today-dt.timedelta(days=dayActivity)
                if date==no.date:
                    distance=distance+no.distance
            dataList.append(distance)
            dates.append(str(date))

        

        return render_template('/pages/NewMyActivity.html', activities=activities, title_prefix = "Moje aktywności", 
                                sumDistance=sumDistance, averageDistance=averageDistance, averageTime=averageTime, percentsOfActivities=percentsOfActivities, kindOfActivities=kindOfActivities, dates=dates, dataList=dataList, menuMode="mainApp")
        
    else:
        return redirect(url_for('other.hello'))


@activity.route("/pandasTest",methods=['POST','GET'])
@login_required
def pandasTest():

        activitiess=Activities.query.filter(Activities.userName == current_user.id)
        #actPand = json_normalize(activitiess, )

        actPand = pd.read_sql(activitiess.statement , db.engine, index_col='id')

        print(actPand)

        return redirect(url_for('other.hello'))

@activity.route("/stravaTEST")
@login_required
def stravaTEST():


    return render_template('/pages/stravaLOG.html')

@activity.route("/stravaLogin")
@login_required
def stravaLogin():

    return redirect('https://www.strava.com/oauth/authorize?client_id=87931&response_type=code&redirect_uri=http://test.sportoweswiry.atthost24.pl/strava-callback&approval_prompt=force&scope=profile:read_all,activity:read_all')

@activity.route("/strava-callback",methods=['POST','GET'])
@login_required
def stravaCallback():
    
    if request.method == "GET":

        try:
            if "error" not in request.args:
                if request.args["scope"] == 'read,activity:read_all,profile:read_all':
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                    access_token = getStravaAccessToken()
                    lastStravaActivity = getLastStravaActivityDate()
                    stravaActivities = getActivitiesFromStrava(access_token, lastStravaActivity)
                    stravaActivities = json_normalize(stravaActivities)
                    stravaActivities = convertStravaData(stravaActivities)

                    addStravaActivitiesToDB (stravaActivities)
                    message = "Zsynchronizowano aktywności ze Strava!"
                
                else:
                    message = "Zaznacz proszę wszystkie wymagane zgody i spróbuj synchronizować ze Strava jeszcze raz."

            else:
                message = "Nie udało się połączyć ze Strava. Spróbuj ponownie za chwilę, lub skontaktuj się z administratorem."

        except:
        #     try:
        #         if request.args['error'] == 'access_denied':
        #             return redirect(url_for('other.hello'))
                    
        #     except:
            message = "Nie udało się połączyć ze Strava. Spróbuj ponownie za chwilę, lub skontaktuj się z administratorem."

    flash(message)
    return redirect(url_for('other.hello'))


