
from flask_login import login_required, current_user
from flask import Blueprint, render_template, redirect, url_for, flash, request

from .classes import *
from .forms import CoeficientsForm, DistancesForm, EventForm, NewSportToEventForm, EventPassword
from activity.classes import Sport
from user.functions import account_confirmation_check
from user.classes import User

import datetime as dt

MAX_EVENTS_AS_ADMIN = 3

event = Blueprint("event", __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/event/static')



@event.route("/explore_events")
@account_confirmation_check
@login_required #This page needs to be login
def explore_events():

    password_form = EventPassword()
    events = Event.available_to_join()

    return render_template('/pages/explore_events.html',
                        events=events,
                        title_prefix = "Dostępne wyzwania",
                        menu_mode="mainApp",
                        form=password_form )


@event.route("/join_event/<int:event_id>", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def join_event(event_id):
    
    password = ''
    if request.method == 'POST':
        password = request.form['password']

    event = Event.query.filter(Event.id == event_id).first()

    if event == None:
        flash_message, status, action  = Event.join_to_not_existing()
    else:
        flash_message, status, action  = event.add_partcipant(user = current_user, provided_password = password)

    flash(flash_message, status)
    return action
    

@event.route("/leave_event/<int:event_id>")
@account_confirmation_check
@login_required
def leave_event(event_id):

    event = Event.query.filter(Event.id == event_id).first()

    if event == None:
        message, status, action  = Event.leave_not_existing()
    else:
        message, status, action = event.leave_event(current_user)

    flash(message, status)
    return action


@event.route("/your_events/<mode>")
@account_confirmation_check
@login_required #This page needs to be login
def your_events(mode):

    if mode == "all":
        user_events = current_user.all_events
    elif mode == 'ongoing':
        user_events = current_user.current_events
    elif mode == 'finished':
        user_events = current_user.finished_events
    elif mode == 'future':
        user_events = current_user.future_events

    if current_user.all_events != None:
    
        return render_template('/pages/your_events.html',
                        events = user_events,
                        title_prefix = "Twoje wyzwania",
                        mode  = mode, menu_mode="mainApp")
    
    else:
       flash ("Nie bierzesz udziału w żadnych wyzwaniach. Zapisz się już dziś!")
       return redirect(url_for('event.explore_events'))

###############################


@event.route("/event_main/<int:event_id>")
@account_confirmation_check
@login_required
def event_main(event_id):

    is_participating = Participation.query.filter(Participation.user_id == current_user.id).filter(Participation.event_id == event_id).first()

    if is_participating != None or current_user.is_admin:

        event = Event.query.filter(Event.id == event_id).first()

        event_participants = event.give_all_event_users(scope = 'Objects_Dictionary')
        event_coefficinets_set = event.give_all_event_activities_types(mode = "All")

        if event_participants == None:

            return render_template('/pages/event_view/event_main.html',
                            event = event,
                            title_prefix = event.name ,
                            usersAmount = 0,
                            coefSet = event_coefficinets_set,
                            menu_mode="mainApp",
                            mode="eventView",
                            activitiesAmount = 0,
                            to_start = (event.start - dt.date.today()).days,
                            eventUsers = event_participants)

        all_event_activities = event.give_all_event_activities(calculated_values = True)
        split_list = event.give_overall_weekly_summary(all_event_activities)
        event_users_amount = len(event_participants)
        return render_template('/pages/event_view/event_main.html',
                        event = event,
                        title_prefix = event.name,
                        usersAmount = event_users_amount,
                        coefSet =event_coefficinets_set,
                        menu_mode="mainApp",
                        mode="eventView",
                        processed_data = split_list,
                        activitiesAmount = len(all_event_activities),
                        to_start = (event.start - dt.date.today()).days,
                        eventUsers = event_participants)

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))



@event.route("/event_activities/<int:event_id>")
@account_confirmation_check
@login_required #This page needs to be login
def event_activities(event_id):

    is_participating = Participation.query.filter(Participation.user_id == current_user.id).filter(Participation.event_id == event_id).first()

    if is_participating != None or current_user.is_admin:

        event = Event.query.filter(Event.id == event_id).first()
        all_event_activities = event.give_all_event_activities(calculated_values = True)

        return render_template('/pages/event_view/event_activities.html',
                        sec_to_H_M_S = sec_to_H_M_S,
                        activities = all_event_activities,
                        event = event,
                        title_prefix = "Aktywności wyzwania",
                        menu_mode="mainApp",
                        mode="eventAvtivities")
        
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))



@event.route("/event_preview/<int:event_id>")
@account_confirmation_check
@login_required #This page needs to be login
def event_preview(event_id):

    event = Event.query.filter(Event.id == event_id).first()
    password_form = EventPassword()
    
    event_coefficinets_set = event.give_all_event_activities_types(mode = "All")

    return render_template('/pages/event_view/event_preview.html',
                    event = event,
                    title_prefix = event.name,
                    coefSet = event_coefficinets_set,
                    menu_mode="mainApp",
                    form=password_form) 



@event.route("/event_statistics/<int:event_id>")
@account_confirmation_check
@login_required #This page needs to be login
def event_statistics(event_id):

    is_participating = Participation.query.filter(Participation.user_id == current_user.id).filter(Participation.event_id == event_id).first()

    if is_participating != None or current_user.is_admin:

        event = Event.query.filter(Event.id == event_id).first()
        all_event_activities = event.give_all_event_activities(calculated_values = True)
      
        highest_distance_sum = all_event_activities.groupby(by=['user_id','name','last_name']).sum().sort_values('calculated_distance', ascending = False)
        highest_activity_amount = all_event_activities.groupby(by=['user_id','name','last_name']).count().sort_values('calculated_distance', ascending = False)

        event_participants_amounnt = len(highest_activity_amount)

        return render_template('/pages/event_view/event_statistics.html',
                        event = event,
                        title_prefix = event.name,
                        users_amount = event_participants_amounnt,
                        menu_mode = "mainApp",
                        mode = "eventStatistics",
                        highest_distance = highest_distance_sum,
                        most_activites = highest_activity_amount)
                        
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))



@event.route("/event_contestants/<int:event_id>")
@account_confirmation_check
@login_required
def event_contestants(event_id):

    is_participating = Participation.query.filter(Participation.user_id == current_user.id).filter(Participation.event_id == event_id).first()

    if is_participating != None or current_user.is_admin:
    
        event = Event.query.filter(Event.id == event_id).first()
        event_participants = event.give_all_event_users(scope = 'Objects_Dictionary')

        return render_template('/pages/event_view/event_contestants.html',
                        event = event,
                        eventUsers = event_participants,
                        title_prefix = event.name,
                        current_user = current_user,
                        menu_mode="mainApp",
                        mode="eventContestants" )

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))



@event.route("/event_beers/<int:event_id>")
@account_confirmation_check
@login_required
def event_beers(event_id):

    is_participating = Participation.query.filter(Participation.user_id == current_user.id).filter(Participation.event_id == event_id).first()

    if is_participating != None or current_user.is_admin:

        event = Event.query.filter(Event.id == event_id).first()

        event_participants = event.give_all_event_users(scope = 'Objects_Dictionary')
        all_event_activities = event.give_all_event_activities(calculated_values = True)

        split_list = event.give_overall_weekly_summary(all_event_activities)

        beers_summary = event.give_beers_summary(split_list)
        beers_to_buy = beers_summary['beers_to_buy']
        beers_to_recive = beers_summary['beers_to_recive']

        return render_template('/pages/event_view/event_beers.html',
                        event=event,
                        eventUsers=event_participants,
                        title_prefix = event.name,
                        current_user=current_user,
                        beerToBuy=beers_to_buy,
                        beers_to_recive = beers_to_recive,
                        menu_mode="mainApp",
                        mode="eventBeers")

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))


###############################



@event.route("/new_event", methods=['POST','GET'])
@account_confirmation_check
@login_required
def create_event():

    event_form = EventForm()

    if len(Event.query.filter(Event.status.in_(['0','1','2','3'])).filter(Event.admin_id == current_user.id).all()) < MAX_EVENTS_AS_ADMIN:

        if event_form.validate_on_submit():

            new_event = Event()
            message, status, action = new_event.add_to_db(event_form)

            CoefficientsList.create_coeffciet_set_with_default_values(new_event)
        
            flash(message, status)
            return action

        return render_template("/pages/new_event.html",
                        title_prefix = "Nowe wydarzenie",
                        form = event_form,
                        menu_mode="mainApp",
                        mode = "create")
    else: 
            flash('Jesteś już organizatorem 3 trwających wyzwań. W tym momencie nie możesz stworzyć kolejnych!', 'danger')
            return redirect(url_for('other.hello'))



@event.route("/new_event_targets/<int:event_id>", methods=['POST','GET'])
@account_confirmation_check
@login_required
def define_event_targets(event_id):

    new_event = Event.query.filter(Event.id == event_id).first()
    if not current_user.is_admin and new_event.admin_id != current_user.id:
        flash("Nie masz uprawnień do tej zawartości!")
        return redirect(url_for('other.hello'))

    distance_set = DistancesTable.query.filter(DistancesTable.event_id == new_event.id).all()
    distance_form = DistancesForm(w1 = distance_set[0].target,
    w2 = distance_set[1].target,
    w3 = distance_set[2].target,
    w4 = distance_set[3].target,
    w5 = distance_set[4].target,
    w6 = distance_set[5].target,
    w7 = distance_set[6].target,
    w8 = distance_set[7].target,
    w9 = distance_set[8].target,
    w10 = distance_set[9].target,
    w11 = distance_set[10].target,
    w12 = distance_set[11].target,
    w13 = distance_set[12].target,
    w14 = distance_set[13].target,
    w15 = distance_set[14].target)

    if distance_form.validate_on_submit():

            message, status, action = message, status, action = new_event.modify_targets(distance_form)
        
            flash(message, status)
            return action

    return render_template("/pages/new_event_targets.html",
                    event = new_event,
                    title_prefix = "Nowe wydarzenie",
                    distance_form = distance_form,
                    menu_mode="mainApp",
                    mode = "create")




@event.route("/modify_event/<int:event_id>", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def modify_event(event_id):

    event = Event.query.filter(Event.id == event_id).first()

    if not current_user.is_admin and event.admin_id != current_user.id:
        flash("Nie masz uprawnień do tej zawartości!")
        return redirect(url_for('other.hello'))

    if not current_user.is_admin and event.status != '0':
        flash("Nie możesz modyfikować wyzwania, które już się rozpoczęło!")
        return redirect(url_for('event.event_main', event_id = event_id))
    
    distance_set = DistancesTable.query.filter(DistancesTable.event_id == event.id).all()

    form = EventForm(name = event.name,
            start = event.start,
            length = event.length_weeks,
            isPrivate = event.is_private,
            description = event.description,
            password = event.password,
            max_users = event.max_user_amount,
            old_name = event.name,
            participatns = len(event.give_all_event_users('Objects')))


    distance_form = DistancesForm(w1 = distance_set[0].target,
    w2 = distance_set[1].target,
    w3 = distance_set[2].target,
    w4 = distance_set[3].target,
    w5 = distance_set[4].target,
    w6 = distance_set[5].target,
    w7 = distance_set[6].target,
    w8 = distance_set[7].target,
    w9 = distance_set[8].target,
    w10 = distance_set[9].target,
    w11 = distance_set[10].target,
    w12 = distance_set[11].target,
    w13 = distance_set[12].target,
    w14 = distance_set[13].target,
    w15 = distance_set[14].target)

    new_sport_form = NewSportToEventForm()
    available_sports = Sport.all_sports()
    

    for sport in Sport.all_sports():
        if sport[0] in event.give_all_event_activities_types():
            available_sports.remove((sport[0], sport[1]))


    new_sport_form.activity_type.choices = available_sports
    coefficientsSet = CoefficientsList.query.filter(CoefficientsList.event_id == event.id).all()

    if form.validate_on_submit():

        message, status, action = event.modify(form, distance_form)
    
        flash(message, status)
        return action

    if distance_form.validate_on_submit() and form.validate_on_submit():

        message, status, action = event.modify_targets(distance_form)
    
        flash(message, status)
        return action

    return render_template("/pages/modify_event.html",
                    title_prefix = "Modfyfikuj wydarzenie",
                    form = form,
                    distance_form = distance_form,
                    new_sport_form = new_sport_form,
                    mode = "edit",
                    event = event,
                    menu_mode="mainApp",
                    CoefficientsSet = coefficientsSet)


@event.route('/add_new_sport_event/<int:event_id>', methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def add_new_sport_to_event(event_id):

    event = Event.query.filter(Event.id == event_id).first()

    if not current_user.is_admin and event.admin_id != current_user.id:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    if not current_user.is_admin and event.status != '0':
        flash("Nie możesz modyfikować wyzwania, które już się rozpoczęło!")
        return redirect(url_for('event.event_main', event_id = event_id))

    if not 'activity_type' in request.form:
        flash("Błędne wywołanie funkcji!")
        return redirect(url_for('other.hello'))
    
    sport_to_add = Sport.query.filter(Sport.id == request.form['activity_type']).first()
    message, status, action = event.add_sport(sport_to_add)

    flash(message, status)
    return action



@event.route("/delete_sport_event/<int:event_id>/<int:activity_type_id>")
@account_confirmation_check
@login_required #This page needs to be login
def delete_coefficient(event_id, activity_type_id):

    event = Event.query.filter(Event.id == event_id).first()
    if not current_user.is_admin and event.admin_id != current_user.id:
        flash("Nie masz uprawnień do tej zawartości!")
        return redirect(url_for('other.hello'))

    if not current_user.is_admin and event.status != '0':
        flash("Nie możesz modyfikować wyzwania, które już się rozpoczęło!")
        return redirect(url_for('event.event_main', event_id = event_id))

    event = Event.query.filter(Event.id == event_id).first()
    message, status, action = event.delete_sport(activity_type_id)

    flash(message, status)
    return action


@event.route("/modify_sport_event/<int:event_id>/<int:activity_type_id>", methods=['POST', 'GET'])
@account_confirmation_check
@login_required #This page needs to be login
def modify_coefficient(event_id, activity_type_id):

    event = Event.query.filter(Event.id == event_id).first()
    if not current_user.is_admin and event.admin_id != current_user.id:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    if not current_user.is_admin and event.status != '0':
        flash("Nie możesz modyfikować wyzwania, które już się rozpoczęło!")
        return redirect(url_for('event.event_main', event_id = event_id))

    coefficient_to_modify = CoefficientsList.query.filter(CoefficientsList.event_id==event_id).filter(CoefficientsList.activity_type_id==activity_type_id).first()


    coefficient_form = CoeficientsForm(event_name = coefficient_to_modify.event,
        activity_name = coefficient_to_modify.sport,
        value = coefficient_to_modify.value,
        is_constant = int(coefficient_to_modify.is_constant))

    del coefficient_form.strava_name
    coefficient_form.event_name.validators = []
    coefficient_form.activity_name.validators = []

    if coefficient_form.validate_on_submit():

        message, status, action = event.modifiy_sport_coefficient(coefficient_to_modify, coefficient_form)
    
        flash(message, status)
        return action

    return render_template("/pages/modify_coeficients.html",
                    title_prefix = "Nowa tabela współczynników",
                    form = coefficient_form,
                    menu_mode="mainApp",
                    event_id = event_id,
                    activity_type_id = activity_type_id)

###############################


@event.route("/admin_event_list")
@account_confirmation_check
@login_required #This page needs to be login
def admin_list_of_events():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    events=Event.query.order_by(Event.added_on.desc()).all()
    return render_template('/pages/admin_events.html',
                    events=events,
                    title_prefix = "Lista wyzwań",
                    menu_mode="mainApp")



@event.route("/admin_list_of_sports")
@account_confirmation_check
@login_required #This page needs to be login
def admin_list_of_sports():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    sports = Sport.query.all()
    return render_template('/pages/admin_sports.html',
                    sports = sports,
                    title_prefix = "Lista sportów",
                    menu_mode="mainApp")
    

@event.route("/admin_delete_contestant/<int:event_id>/<user_id>")
@account_confirmation_check
@login_required
def admin_delete_contestant(event_id, user_id):

    event = Event.query.filter(Event.id == event_id).first()
    user_to_delete = User.query.filter(User.id == user_id).first()

    message, status, action = event.leave_event(user_to_delete)
    flash(message, status)

    return action


@event.route("/delete_event/<int:event_id>")
@account_confirmation_check
@login_required #This page needs to be login
def admin_delete_event(event_id):
    
    event = Event.query.filter(Event.id == event_id).first()
    message, status, action = event.delete()

    flash(message, status)

    return action


@event.route('/add_sport_app/', methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def add_new_sport_to_base():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    form = CoeficientsForm()
    del form.event_name

    if form.validate_on_submit():

        message, status, aciton = Sport.add_new(form)
        flash(message, status)
        return aciton

    return render_template("/pages/new_sport_to_db.html",
                    title_prefix = "Nowy sport",
                    form = form) 


@event.route('/delete_sport_app/<int:sport_id>', methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def delete_sport_from_base(sport_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    sport_to_delete = Sport.query.filter(Sport.id == sport_id).first()
    message, status, action =  sport_to_delete.delete()

    flash(message, status)
    return action


@event.route('/modify_sport_app/<int:sport_id>', methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def modify_sport_in_base(sport_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    sport_to_modify = Sport.query.filter(Sport.id == sport_id).first()

    sport_form = CoeficientsForm(activity_name = sport_to_modify.name,
                        value = sport_to_modify.default_coefficient,
                        is_constant = sport_to_modify.default_is_constant,
                        strava_name = sport_to_modify.strava_name,
                        old_name = sport_to_modify.name,
                        old_strava_name = sport_to_modify.strava_name)
    del sport_form.event_name

    if sport_form.validate_on_submit():

        message, status, action = sport_to_modify.modify(sport_form)

        flash(message, status)
        return action

    return render_template("/pages/modify_sport_in_db.html",
                    title_prefix = "Nowy sport",
                    form = sport_form,
                    mode = 'edit',
                    sport_id = sport_id) 

def sec_to_H_M_S(seconds):
    return str(dt.timedelta(seconds = seconds))