from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from .classes import Activities
from .forms import ActivityForm
from .strava import serve_strava_callback
from user.functions import account_confirmation_check

import datetime as dt



activity = Blueprint("activity", __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/activity/static')


@account_confirmation_check
@activity.route("/add_activity", methods=['POST','GET'])
@login_required #This page needs to be login
def add_activity():

    form = ActivityForm()
    form.fill_sports_to_select()

    if form.validate_on_submit():

        newActivity = Activities()
        all_events_weeks = current_user.events_weeks_status()
        message, status, url = newActivity.add_to_db(form)
        current_user.show_events_weeks_changes(all_events_weeks)

        flash(message, status)
        return redirect(url_for(url))

    
    user_events = current_user.current_events

    for event in user_events:

        all_event_activities = event.give_all_event_activities(calculated_values = True)
        split_list = event.give_overall_weekly_summary(all_event_activities)
        event.event_week_distance =  split_list[event.current_week-1].loc['total']['calculated_distance'][current_user.id][0]
    
    else:
        return render_template('/pages/add_activity.html',
                    form = form,
                    mode = "create",
                    title_prefix = "Dodaj aktywność",
                    menu_mode = "mainApp",
                    events = user_events)


@account_confirmation_check
@activity.route('/delete_activity/<int:activity_id>')
@login_required #This page needs to be login
def delete_activity(activity_id):

    activity_to_delete = Activities.query.filter(Activities.id == activity_id).first()

    message, status, url = activity_to_delete.delete()
    flash(message, status)

    return redirect(url_for(url))


@account_confirmation_check
@activity.route("/modify_activity/<int:activity_id>", methods=['POST','GET'])
@login_required #This page needs to be login
def modify_activity(activity_id):
    
    activity_to_modify = Activities.query.filter(Activities.id == activity_id).first()
    if activity_to_modify.user_id == current_user.id :

        #form = ActivityForm(request.form, activity_id)
        form = ActivityForm(date = activity_to_modify.date,
                            activity = activity_to_modify.activity_type.id,
                            distance = activity_to_modify.distance,
                            time = (dt.datetime(1970,1,1) + dt.timedelta(seconds=activity_to_modify.time)).time())

        if form.validate_on_submit():

            all_events_weeks = current_user.events_weeks_status()
            message, status, url = activity_to_modify.modify(form)
            current_user.show_events_weeks_changes(all_events_weeks)
            flash(message, status)
        
            return redirect(url_for(url))

        form.fill_sports_to_select()
        user_events = current_user.current_events

        for event in user_events:

            all_event_activities = event.give_all_event_activities(calculated_values = True)
            split_list = event.give_overall_weekly_summary(all_event_activities)
            event.event_week_distance =  split_list[event.current_week-1].loc['total']['calculated_distance'][current_user.id][0]
            
        else:
            return render_template('/pages/add_activity.html',
                            form = form,
                            mode ="edit",
                            activity_id = activity_id,
                            title_prefix = "Edytuj aktywność",
                            menu_mode = "mainApp",
                            events = user_events)

    else:

        flash("Możesz edytować tylko swoje aktywności!", 'danger')
        return redirect(url_for('activity.my_activities'))


@account_confirmation_check
@activity.route("/my_activities")
@login_required #This page needs to be login
def my_activities():

    activities=Activities.query.filter(Activities.user_id == current_user.id).order_by(Activities.date.desc()).all()

    if activities:
        sum_distance=0
        sumTime = 0
        amount = len(activities)
        average_distance = 0
        average_time = 0

        for activity in activities:
            sum_distance = sum_distance + activity.distance
            sumTime += activity.time

        #Calculation of basic data about the user's activities
        average_distance = round(sum_distance/amount,2)
        average_time = int((sumTime/amount))
        average_time = sec_to_H_M_S(average_time)

        sum_distance = round(sum_distance,1)

        check_table = []

        kind_of_activities = []
        percents_of_activities = []

        #calculation of the percentage of activity
        for activity_external in activities:
            quantity = 0
            for activityInternal in activities:
                if activity_external.activity_type.name == activityInternal.activity_type.name and not activity_external.activity_type.name in check_table:
                    quantity = quantity+1
            if quantity > 0:
                kind_of_activities.append(activity_external.activity_type.name)
                percents_of_activities.append(round((quantity/amount)*100,1))
                check_table.append(activity_external.activity_type.name)
        
        today = dt.date.today()
        data_list = []
        dates = []

        for day_activity in range(10):
            distance  =0
            for no in activities:
                date = today - dt.timedelta(days = day_activity)
                if date == no.date:
                    distance = distance + no.distance
            data_list.append(distance)
            dates.append(str(date))

        return render_template('/pages/my_activities.html',
                                activities = activities,
                                title_prefix = "Moje aktywności",
                                sec_to_H_M_S = sec_to_H_M_S,
                                sum_distance = sum_distance,
                                average_distance = average_distance,
                                average_time = average_time,
                                percents_of_activities = percents_of_activities,
                                kind_of_activities = kind_of_activities,
                                dates = dates,
                                data_list = data_list,
                                menu_mode = "mainApp")
        
    else:
        return render_template('/pages/my_activities.html',
                        activities = activities,
                        title_prefix = "Moje aktywności",
                        sec_to_H_M_S = sec_to_H_M_S,
                        sum_distance = " --- ",
                        average_distance = " --- ",
                        average_time = " --- ",
                        menu_mode = "mainApp")


@activity.route("/strava_login")
@login_required
def strava_login():

    current_app.logger.info(f'User {current_user.id} clicked "Connect with Strava" button')
    url = 'https://www.strava.com/oauth/authorize?client_id=87931&response_type=code&redirect_uri=' + request.base_url.replace('/strava_login', '') + '/strava-callback&approval_prompt=force&scope=profile:read_all,activity:read_all'
    return redirect(url) 


@activity.route("/strava-callback",methods=['GET'])
@login_required
def strava_callback():

    message, status, action = serve_strava_callback(request)

    flash(message, status)
    return action


def sec_to_H_M_S(seconds):
    return str(dt.timedelta(seconds = seconds))
