import datetime as dt
import csv

from flask_login import login_required, current_user
from start import db, app
from flask import Blueprint, render_template, redirect, url_for, flash, request


cron = Blueprint("cron", __name__,
    template_folder='templates')

@cron.route("/cron/test", methods = ['POST'])
def cron_test_post():

    with open("cron_users.txt", "a") as file:
        file.write('dad' +"\n")

    return "crom"

@cron.route("/cron/update_events_statuses", methods = ['POST'])
def cron_update_event_statuses():

    from event.classes import Event

    events = Event.query.all()
    log =[]

    for event in events:

        event.update_status()

    return str(log)


@cron.route("/cron/send_weekly_summary", methods = ['POST'])
def cron_send_weekly_summary():

    from user.classes import User
    from other.functions import send_email
    
    summary = StatisticalSummary(7)
    admins = User.all_application_admins()
    user = User.query.filter(User.id == "MaBober").first()

    # send_email(user.mail, f"Podsumowanie ostatnich {summary.days} dni",'emails/app_summary', summary = summary, admin = user)

    for admin in admins:
        send_email(admin.mail, f"Podsumowanie ostatnich {summary.days} dni",'emails/app_summary', summary = summary, admin = admin)

    return f'''New activities: {str(summary.new_activities)}
              New users: {str(summary.new_users)}
              New events: {str(summary.new_events)}
              Sumary for : {str(summary.start_date)} - {str(summary.end_date)}
              Admins: {str(admins)}'''
              


class StatisticalSummary():

    def __init__(self, number_of_days) -> None:

        from user.classes import User
        from activity.classes import Activities
        from event.classes import Event

        self.days = number_of_days
        self.start_date = dt.date.today() - dt.timedelta(days=number_of_days)
        self.end_date = dt.date.today() - dt.timedelta(days=1)
        self.new_activities = Activities.added_in_last_days(self.days)
        self.new_users = User.added_in_last_days(self.days)
        self.new_events = Event.added_in_last_days(self.days)
