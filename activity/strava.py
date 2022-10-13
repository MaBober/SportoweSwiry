from start import db
from flask import request
from flask_login import current_user
from activity.classes import Activities

import requests
import pandas as pd
import datetime as dt

def getLastStravaActivityDate():

        lastStravaActivitity = Activities.query.filter(Activities.userName == current_user.id).filter(Activities.stravaID != None).order_by(Activities.date.desc()).first()
        
        if lastStravaActivitity == None:
            lastActivitity = Activities.query.filter(Activities.userName == current_user.id).order_by(Activities.date.desc()).first()
            lastStravaActivitityDate = dt.datetime(lastActivitity.date.year, lastActivitity.date.month, lastActivitity.date.day,0,0).timestamp()
        
        else:
            lastStravaActivitity = Activities.query.filter(Activities.userName == current_user.id).filter(Activities.stravaID != None).order_by(Activities.date.desc()).first()
            lastStravaActivitityDate = dt.datetime(lastStravaActivitity.date.year, lastStravaActivitity.date.month, lastStravaActivitity.date.day,0,0).timestamp()

        return lastStravaActivitityDate

def getStravaAccessToken():

    code = request.args['code']
    auth_url = "https://www.strava.com/oauth/token"
    
    payload = {
    'client_id': "87931",
    'client_secret': 'a02f77e5eedb0784e84a5646e59072f300562e84',
    'code': code,
    'grant_type': "authorization_code",
    'f': 'json'
    }

    res = requests.post(auth_url, data=payload, verify=False)
    accessToken = res.json()['access_token']
    
    return accessToken


def getActivitiesFromStrava(access_token, afterDate):

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1, 'after':afterDate}
    activites_url = "https://www.strava.com/api/v3/athlete/activities"
    
    stravaActivities = requests.get(activites_url, headers=header, params=param).json()

    return stravaActivities

def convertStravaData(activitiesJSON):

    #Defines columns to proceed
    columns = [
        "id",
        "start_date_local",
        "type",
        "distance",
        "elapsed_time"
    ]
    
    activitiesJSON = activitiesJSON[columns]

    #Dodać wszystkie aktywności!
    #Defines names relations
    acitivitieTypesDictionary = {
        "Run":"Bieg",
        "Trail Run" : "BiegTrailowy",
        "Walk":"Spacer",
        "Hike":"Trekking",
        "Ride":"Kolarstwo",
        "Mountain Bike Ride": "Kolarstwo górskie",
        "Gravel Bike Ride":"Kolarstwo",
        "Swim":"Pływanie",
        "Alpine Ski":"Narciarstwo zjazdowe",
        "Yoga":"Joga",
        "Inline Skate":"Rolki",
        "Rock Climb":"Wspinaczka",
        "Workout":"Fitness"
        }

    #Defines columns names
    columsDictionary = {
        "id":"stravaID",
        "start_date_local":"date",
        "type":"activity",
        'elapsed_time':"time"
        }

    activitiesJSON.rename(columns=columsDictionary, inplace=True)
    
    #Prepare data to match APP tables
    activitiesJSON["activity"].replace(acitivitieTypesDictionary, inplace=True)
    activitiesJSON['date'] = pd.to_datetime(activitiesJSON['date']).dt.date
    activitiesJSON['distance'] = round(activitiesJSON['distance']/1000, 1)
    activitiesJSON['time'] = activitiesJSON['time'].apply(format_time)
    activitiesJSON['userName'] = current_user.id
    
    return activitiesJSON

def format_time(x):

    return str(dt.timedelta(seconds = x))


def addStravaActivitiesToDB (activitiesFrame):

    for index, singleActivity in activitiesFrame.iterrows() :

        #Check if activity with this stravaID doesn't already exists
        if Activities.query.filter(Activities.stravaID == singleActivity['stravaID']).first() == None:

            #Check if simlat activity wasn't addded manualy
            if Activities.query.\
                filter(Activities.date == singleActivity['date']).\
                filter(Activities.stravaID == None).\
                filter(Activities.userName == current_user.id).\
                filter(Activities.activity == singleActivity['activity'] ).\
                filter(Activities.distance > singleActivity['distance'] -0.5).\
                filter(Activities.distance < singleActivity['distance'] +0.5).first() == None:

                newActivity=Activities(date=singleActivity['date'], activity=singleActivity['activity'], distance=singleActivity['distance'], 
                                    time=singleActivity['time'], userName=current_user.id, stravaID = singleActivity['stravaID'])

                # #adding new activity to datebase
                db.session.add(newActivity)

    db.session.commit()

    return None