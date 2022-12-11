from start import  db, app
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from activity.classes import Activities
from activity.forms import ActivityForm
from user.functions import account_confirmation_check
from other.functions import account_confirmation_check
from .strava import addStravaActivitiesToDB, getActivitiesFromStrava, getLastStravaActivityDate, getStravaAccessToken, convertStravaData, serve_strava_callback
from .classes import Activities, Sport

import datetime as dt
import csv


activity = Blueprint("activity", __name__, template_folder='templates')


@account_confirmation_check
@activity.route("/addActivity", methods=['POST','GET'])
@login_required #This page needs to be login
def add_activity():

    form = ActivityForm()
    form.fill_sports_to_select()

    if form.validate_on_submit():

        newActivity = Activities()
        message, status, url = newActivity.add_to_db(form)

        flash(message, status)
        return redirect(url_for(url))

    user_events = current_user.current_events.all()
    for event in user_events:

        all_event_activities = event.give_all_event_activities(calculated_values = True)
        split_list = event.give_overall_weekly_summary(all_event_activities)
        event.event_week_distance =  split_list[event.current_week-1].loc['total']['calculated_distance'][current_user.id][0]
    
    else:
        return render_template('/pages/addActivity.html',
                    form = form,
                    mode = "create",
                    title_prefix = "Dodaj aktywność",
                    menuMode = "mainApp",
                    events = user_events)


@account_confirmation_check
@activity.route('/deleteActivity/<int:activity_id>')
@login_required #This page needs to be login
def delete_activity(activity_id):

    activity_to_delete = Activities.query.filter(Activities.id == activity_id).first()

    message, status, url = activity_to_delete.delete()
    flash(message, status)

    return redirect(url_for(url))


@account_confirmation_check
@activity.route("/modifyActivity/<int:activity_id>", methods=['POST','GET'])
@login_required #This page needs to be login
def modify_activity(activity_id):
    
    activity_to_modify = Activities.query.filter(Activities.id == activity_id).first()
    if activity_to_modify.user_id == current_user.id :

        form = ActivityForm(date = activity_to_modify.date,
                            activity = activity_to_modify.activity_type,
                            distance = activity_to_modify.distance,
                            time = (dt.datetime(1970,1,1) + dt.timedelta(seconds=activity_to_modify.time)).time())
        form.fill_sports_to_select()
        form.activity.id = activity_to_modify.activity_type_id

        if form.validate_on_submit():
            message, status, url = activity_to_modify.modify(form)
            flash(message, status)
        
            return redirect(url_for(url))
            
        else:
            return render_template('/pages/addActivity.html',
                            form = form,
                            mode ="create",
                            title_prefix = "Dodaj aktywność",
                            menuMode = "mainApp")

    else:

        flash("Możesz edytować tylko swoje aktywności!", 'danger')
        return redirect(url_for('activity.my_activities'))


@account_confirmation_check
@activity.route("/myActivities")
@login_required #This page needs to be login
def my_activities():

    activities=Activities.query.filter(Activities.user_id == current_user.id).order_by(Activities.date.desc()).all()

    if activities:
        sumDistance=0
        sumTime = 0
        timeList = []
        amount = len(activities)
        average_distance = 0
        average_time = 0

        for activity in activities:
            sumDistance = sumDistance + activity.distance
            sumTime += activity.time

        #Calculation of basic data about the user's activities
        average_distance = round(sumDistance/amount,2)
        average_time = int((sumTime/amount))
        average_time = sec_to_H_M_S(average_time)

        sumDistance = round(sumDistance,1)

        checkTable = []

        kindOfActivities = []
        percentsOfActivities = []

        #calculation of the percentage of activity
        for activityExternal in activities:
            quantity = 0
            for activityInternal in activities:
                if activityExternal.activity_type.name == activityInternal.activity_type.name and not activityExternal.activity_type.name in checkTable:
                    quantity = quantity+1
            if quantity > 0:
                kindOfActivities.append(activityExternal.activity_type.name)
                percentsOfActivities.append(round((quantity/amount)*100,1))
                checkTable.append(activityExternal.activity_type.name)
        
        today = dt.date.today()
        dataList = []
        dates = []

        for dayActivity in range(10):
            distance  =0
            for no in activities:
                date = today - dt.timedelta(days = dayActivity)
                if date == no.date:
                    distance = distance + no.distance
            dataList.append(distance)
            dates.append(str(date))

        return render_template('/pages/myActivities.html',
                                activities = activities,
                                title_prefix = "Moje aktywności",
                                sec_to_H_M_S = sec_to_H_M_S,
                                sumDistance = sumDistance,
                                averageDistance = average_distance,
                                averageTime = average_time,
                                activitiesAmount = len(activities),
                                percentsOfActivities = percentsOfActivities,
                                kindOfActivities = kindOfActivities,
                                dates = dates,
                                dataList = dataList,
                                menuMode = "mainApp")
        
    else:
        return redirect(url_for('other.hello'))


@activity.route("/stravaLogin")
@login_required
def strava_login():
    current_app.logger.info(f'User {current_user.id} clicked "Connect with Strava" button')
    return redirect('https://www.strava.com/oauth/authorize?client_id=87931&response_type=code&redirect_uri=http://127.0.0.1:5000/strava-callback&approval_prompt=force&scope=profile:read_all,activity:read_all')


@activity.route("/strava-callback",methods=['GET'])
@login_required
def strava_callback():

    message, status, action = serve_strava_callback(request)

    flash(message, status)
    return action


def sec_to_H_M_S(seconds):
    return str(dt.timedelta(seconds = seconds))
