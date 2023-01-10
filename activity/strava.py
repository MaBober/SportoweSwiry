from start import db
from flask import redirect, url_for, current_app
from flask_login import current_user
from config import Config

from activity.classes import Activities, Sport

import requests
import pandas as pd
import datetime as dt
import urllib3

def serve_strava_callback(request):
    try:
        if "error" not in request.args:
            if request.args["scope"] == 'read,activity:read_all,profile:read_all':
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                code = request.args['code']
                access_token = get_strava_access_token(code)
                activities_since = (dt.datetime.today() - dt.timedelta(days = Config.DAYS_TO_ADD_ACTIVITY)).timestamp()
                strava_activities = get_activities_from_strava(access_token, activities_since)
                strava_activities = pd.json_normalize(strava_activities)
                strava_activities = convert_strava_data(strava_activities)

                add_strava_activities_to_db (strava_activities)
                message = "Zsynchronizowano aktywności ze Strava!"
                current_app.logger.info(f"User {current_user.id} added activity with Strava")
                return message, 'success', redirect(url_for('other.hello'))
            
            else:
                message = "Zaznacz proszę wszystkie wymagane zgody i spróbuj synchronizować ze Strava jeszcze raz."
                current_app.logger.warning(f"User {current_user.id} failed to add activity with Strava. Not all agree chekboxes cheked.")
                return message, 'danger', redirect(url_for('activity.add_activity'))

        else:
            message = "Nie udało się połączyć ze Strava. Spróbuj ponownie za chwilę, lub skontaktuj się z administratorem."
            current_app.logger.warning(f"User {current_user.id} failed to add activity with Strava")
            return message, 'danger', redirect(url_for('activity.add_activity'))

    except:
        message = "W czasie synchronizacji ze Strava pojawił się nieoczekiwany błąd. Spróbuj ponownie za chwilę, lub skontaktuj się z administratorem."
        current_app.logger.exception(f"User {current_user.id} failed to add activity with Strava")
        return message, 'danger', redirect(url_for('activity.add_activity'))


def get_strava_access_token(code):

    auth_url = "https://www.strava.com/oauth/token"
    
    payload = {
    'client_id': Config.STRAVA_CLIENT_ID,
    'client_secret': Config.STRAVA_CLIENT_SECRET,
    'code': code,
    'grant_type': "authorization_code",
    'f': 'json'
    }

    res = requests.post(auth_url, data = payload, verify = False)
    accessToken = res.json()['access_token']
    
    return accessToken


def get_activities_from_strava(access_token, afterDate):

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1, 'after':afterDate}
    activites_url = "https://www.strava.com/api/v3/athlete/activities"
    
    strava_activities = requests.get(activites_url, headers = header, params = param).json()

    return strava_activities


def convert_strava_data(activitiesJSON):

    #Defines columns to proceed
    columns = [
        "id",
        "start_date_local",
        "type",
        "distance",
        "sport_type",
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

    activitiesJSON = activitiesJSON.rename(columns=columsDictionary)
    #Prepare data to match APP tables
    activitiesJSON['date'] = pd.to_datetime(activitiesJSON['date']).dt.date
    activitiesJSON['distance'] = round(activitiesJSON['distance']/1000, 1)
    activitiesJSON['userName'] = current_user.id
    
    return activitiesJSON


def add_strava_activities_to_db (activities_frame):

    for index, single_activity in activities_frame.iterrows() :

        new_activity_sport = Sport.query.filter(Sport.strava_name == single_activity["sport_type"]).first()
        if new_activity_sport == None:
            new_activity_sport = Sport.query.filter(Sport.strava_name == single_activity["activity_type_id"]).first()
            if new_activity_sport == None:
                new_activity_sport_id = Sport.query.filter(Sport.name == 'Inny').first().id
            else:
                new_activity_sport_id = new_activity_sport.id
        else:
            new_activity_sport_id = new_activity_sport.id

        #Check if activity with this strava_id doesn't already exists
        if Activities.query.filter(Activities.strava_id == single_activity['strava_id']).first() == None:

            #Check if simlat activity wasn't addded manualy
            if Activities.query.\
                filter(Activities.date == single_activity['date']).\
                filter(Activities.strava_id == None).\
                filter(Activities.id == current_user.id).\
                filter(Activities.activity_type_id == new_activity_sport_id ).\
                filter(Activities.distance > single_activity['distance'] -0.5).\
                filter(Activities.distance < single_activity['distance'] +0.5).first() == None:

                new_activity=Activities(
                    date = single_activity['date'],
                    activity_type_id = new_activity_sport_id,
                    distance = single_activity['distance'], 
                    time = single_activity['time'],
                    user_id = current_user.id,
                    strava_id = single_activity['strava_id'])

                # #adding new activity to datebase
                db.session.add(new_activity)

    db.session.commit()

    return None