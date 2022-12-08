from start import db
from flask import request
from flask_login import current_user
from activity.classes import Activities, Sport

import requests
import pandas as pd
import datetime as dt

def getLastStravaActivityDate():

        lastStravaActivitity = Activities.query.filter(Activities.user_id == current_user.id).filter(Activities.strava_id != None).order_by(Activities.date.desc()).first()
        
        if lastStravaActivitity == None:
            lastActivitity = Activities.query.filter(Activities.user_id == current_user.id).order_by(Activities.date.desc()).first()
            lastStravaActivitityDate = dt.datetime(lastActivitity.date.year, lastActivitity.date.month, lastActivitity.date.day,0,0).timestamp()
        
        else:
            lastStravaActivitity = Activities.query.filter(Activities.user_id == current_user.id).filter(Activities.strava_id != None).order_by(Activities.date.desc()).first()
            lastStravaActivitityDate = dt.datetime(lastStravaActivitity.date.year, lastStravaActivitity.date.month, lastStravaActivitity.date.day,0,0).timestamp()

        return lastStravaActivitityDate

def getStravaAccessToken(code):

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

#TODO rebuild activities dictionary
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

    #Defines columns names
    columsDictionary = {
        "id":"strava_id",
        "start_date_local":"date",
        "type":"activity_type_id",
        'elapsed_time':"time"
        }

    activitiesJSON.rename(columns=columsDictionary, inplace=True)
    #Prepare data to match APP tables
    activitiesJSON['date'] = pd.to_datetime(activitiesJSON['date']).dt.date
    activitiesJSON['distance'] = round(activitiesJSON['distance']/1000, 1)
    activitiesJSON['time'] = activitiesJSON['time'].apply(format_time)
    activitiesJSON['userName'] = current_user.id
    
    return activitiesJSON

def format_time(x):

    return str(dt.timedelta(seconds = x))


def addStravaActivitiesToDB (activitiesFrame):

    for index, single_activity in activitiesFrame.iterrows() :

        #Check if activity with this strava_id doesn't already exists
        if Activities.query.filter(Activities.strava_id == single_activity['strava_id']).first() == None:

            #Check if simlat activity wasn't addded manualy
            if Activities.query.\
                filter(Activities.date == single_activity['date']).\
                filter(Activities.strava_id == None).\
                filter(Activities.id == current_user.id).\
                filter(Activities.activity_type_id == Sport.query.filter(Sport.strava_name == single_activity["activity_type_id"]).first().id ).\
                filter(Activities.distance > single_activity['distance'] -0.5).\
                filter(Activities.distance < single_activity['distance'] +0.5).first() == None:

                print(single_activity)
                newActivity=Activities(
                    date = single_activity['date'],
                    activity_type_id = Sport.query.filter(Sport.strava_name == single_activity["activity_type_id"]).first().id,
                    distance = single_activity['distance'], 
                    time = single_activity['time'],
                    user_id = current_user.id,
                    strava_id = single_activity['strava_id'])

                # #adding new activity to datebase
                db.session.add(newActivity)

    db.session.commit()

    return None