import datetime as dt
import csv
from tabnanny import check


from flask_login import login_required, current_user
from start import db, app
from flask import Blueprint, render_template, redirect, url_for, flash, request

from .classes import *
from .forms import CoeficientsForm, DistancesForm, EventForm, NewSportToEventForm
from .functions import add_user_to_event, delete_user_from_event
from activity.classes import Activities, Sport
from other.functions import send_email, account_confirmation_check
from user.functions import account_confirmation_check#, send_email
from user.classes import User

from other.classes import MailboxMessage
from other.functions import sendMessgaeFromContactFormToDB


event = Blueprint("event", __name__,
    template_folder='templates')


@account_confirmation_check
@event.route("/explore_events")
@account_confirmation_check
@login_required #This page needs to be login
def explore_events():

    events=Event.query.filter(Event.status == "Zapisy otwarte").filter(Event.is_private == False).filter().all()

    return render_template('/pages/explore_events.html',
                        events=events,
                        title_prefix = "Dostępne wyzwania",
                        menuMode="mainApp" )


@account_confirmation_check
@event.route("/join_event/<int:event_id>")
@account_confirmation_check
@login_required #This page needs to be login
def join_event(event_id):
    
    event = Event.query.filter(Event.id == event_id).first()

    if event.status == "Zapisy otwarte":
        # Check is user isn't signed already
        is_participating = Participation.query.filter(Participation.user_id == current_user.id).filter(Participation.event_id == event_id).first()
        if is_participating == None:

            add_user_to_event(current_user.id, event_id)
            send_email(current_user.mail, "Witaj w wyzwaniu {}".format(event.name),'welcome', event=event)

            message = '''
            Czołem  {} {}!,

            Witaj w wyzwaniu sportowym {}!

            Data rozpoczęcia: {}
            Długość: {} tygodni

            Życzymy samych sukcesów i wielu pokonanych kilometrów.

            Ubieraj buty i zaczynaj zabawę już dziś! ;)

            Pozdrawiamy,

            Administracja Sportowych Świrów
            '''.format(current_user.name, current_user.last_name, event.name, event.start, event.length_weeks)

            # newMessage = MailboxMessage(date=datetime.date.today(), sender="Sportowe Świry", senderName="Sportowe Świry", receiver = current_user.mail,
            # receiverName = current_user.name+" "+current_user.lastName, subject = "Witaj w wyzwaniu: " + event.name, message = message, sendByApp = True,
            # sendByEmail= False, messageReaded=False, multipleMessage=True)
            # sendMessgaeFromContactFormToDB(newMessage)

            flash("Zapisano do wyzwania " + event.name + "!")
            return redirect(url_for('event.event_main', event_id = event_id))

        else:
            flash("Już jesteś zapisny/a na to wyzwanie!")

        return redirect(url_for('event.explore_events'))

    else:
        flash('Wyzwanie "{}" już się rozpoczęło, nie możesz się do niego dopisać!'.format(event.name))
        return redirect(url_for('event.explore_events'))


@event.route("/leave_event/<int:event_id>")
@login_required
def leave_event(event_id):
    event = Event.query.filter(Event.id == event_id).first()

    # Check is user isn't signed already
    is_participating = Participation.query.filter(Participation.user_id == current_user.id).filter(Participation.event_id == event_id).first()
    if is_participating != None and event.status == "Zapisy otwarte":

        delete_user_from_event(is_participating.user_id, event_id)
        flash("Wypisano się z wyzwania " + event.name + "!")

    elif is_participating != None and event.status != "Zapisy otwarte":
        flash("Nie możesz się wypisać z tego wyzwania, gdyż zapisy na nie zostały zamknięte!")
    
    elif is_participating == None:
        flash("Nie jesteś zapisany na to wyzwanie!")

    return redirect(url_for('event.explore_events'))


@event.route("/your_events/<mode>")
@login_required #This page needs to be login
def your_events(mode):

    if mode == "all":
        user_events = current_user.all_events
    elif mode == 'ongoing':
        user_events = current_user.current_events
    elif mode == 'finished':
        user_events = current_user.finished_events

    if current_user.all_events != None:
        current_user.query.filter(Event.status == mode).all()
        return render_template('/pages/your_events.html',
                        events = user_events,
                        title_prefix = "Twoje wyzwania",
                        mode  = mode, menuMode="mainApp")
    
    else:
       flash ("Nie bierzesz udziału w żadnych wyzwaniach. Zapisz się już dziś!")
       return redirect(url_for('event.explore_events'))

###############################

@account_confirmation_check
@event.route("/event_main/<int:event_id>")
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
                            menuMode="mainApp",
                            mode="eventView",
                            activitiesAmount = 0,
                            eventUsers = event_participants)

        all_event_activities = event.give_all_event_activities(calculated_values = True)
        split_list = event.give_overall_weekly_summary(all_event_activities)
        event_users_amount = len(event_participants)
   
        return render_template('/pages/event_view/event_main.html',
                        event = event,
                        title_prefix = event.name,
                        usersAmount = event_users_amount,
                        coefSet =event_coefficinets_set,
                        menuMode="mainApp",
                        mode="eventView",
                        processed_data = split_list,
                        activitiesAmount = len(all_event_activities),
                        eventUsers = event_participants)

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))


@account_confirmation_check
@event.route("/event_activities/<int:event_id>")
@login_required #This page needs to be login
def event_activities(event_id):

    is_participating = Participation.query.filter(Participation.user_id == current_user.id).filter(Participation.event_id == event_id).first()

    if is_participating != None or current_user.is_admin:

        event = Event.query.filter(Event.id == event_id).first()
        all_event_activities = event.give_all_event_activities(calculated_values = True)

        return render_template('/pages/event_view/event_activities.html',
                        activities = all_event_activities,
                        event = event,
                        title_prefix = "Aktywności wyzwania",
                        menuMode="mainApp",
                        mode="eventAvtivities")
        
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))


@account_confirmation_check
@event.route("/event_preview/<int:event_id>")
@login_required #This page needs to be login
def event_preview(event_id):

    event = Event.query.filter(Event.id == event_id).first()

    event_participants = event.give_all_event_users()
    event_coefficinets_set = event.give_all_event_activities_types(mode = "All")

    return render_template('/pages/event_view/event_preview.html',
                    event = event,
                    title_prefix = event.name,
                    usersAmount = len(event_participants),
                    coefSet = event_coefficinets_set,
                    menuMode="mainApp") 


@account_confirmation_check
@event.route("/event_statistics/<int:event_id>")
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
                        menuMode = "mainApp",
                        mode = "eventStatistics",
                        highest_distance = highest_distance_sum,
                        most_activites = highest_activity_amount)
                        
    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))


@account_confirmation_check
@event.route("/event_contestants/<int:event_id>")
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
                        menuMode="mainApp",
                        mode="eventContestants" )

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))


@account_confirmation_check
@event.route("/event_beers/<int:event_id>")
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
                        menuMode="mainApp",
                        mode="eventBeers")

    else:
        flash("Nie bierzesz udziału w tym wyzwaniu!")
        return redirect(url_for('event.explore_events'))


###############################


@account_confirmation_check
@event.route("/new_event", methods=['POST','GET'])
@account_confirmation_check
@login_required
def create_event():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    event_form = EventForm()
    distances_form = DistancesForm()

    del event_form.status

    #Creating list of available admins (for form)
    admins = User.query.filter(User.is_admin == True).all()
    adminIDs = [(a.id, a.name) for a in admins]
    event_form.adminID.choices=adminIDs

    if event_form.validate_on_submit and distances_form.validate_on_submit():

        new_event = Event()
        new_event.add_to_db(event_form, distances_form)

        CoefficientsList.create_coeffciet_set_with_default_values(new_event)
    
        flash('Stworzono wydarzenie "{}"!'.format(new_event.name))
        return redirect(url_for('other.hello'))

    return render_template("/pages/new_event.html",
                    title_prefix = "Nowe wydarzenie",
                    form = event_form,
                    formDist = distances_form,
                    mode = "create")


@account_confirmation_check
@event.route("/admin_event_list")
@account_confirmation_check
@login_required #This page needs to be login
def admin_list_of_events():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    events=Event.query.all()
    return render_template('/pages/admin_events.html',
                    events=events,
                    title_prefix = "Lista wyzwań")


@account_confirmation_check
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
                    title_prefix = "Lista sportów")
    

# TODO Move deleting to class
@event.route("/admin_delete_contestant/<int:event_id>/<user_id>")
@login_required
def admin_delete_contestant(event_id, user_id):
    event = Event.query.filter(Event.id == event_id).first()

    # Check is user isn't signed already
    is_participating = Participation.query.filter(Participation.user_name == user_id).filter(Participation.event_id == event_id).first()

    if is_participating != None:
        delete_user_from_event(is_participating.id, event_id)
        flash("Usunięto użytkownika {} z wyzwania {}".format(is_participating.user_name, event.name))
    
    elif is_participating == None:
        flash("Użytkownik {} nie jest zapisany na wyzwanie {}!".format(user_id, event.name))

    return redirect(url_for('event_contestants', event_id = event_id))


@account_confirmation_check
@event.route("/delete_event/<int:event_id>")
@login_required #This page needs to be login
def admin_delete_event(event_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))
    
    event = Event.query.filter(Event.id == event_id).first()
    event.delete()

    flash("Usunięto wyzwanie {}!".format(event.name))

    return redirect(url_for('event.admin_list_of_events'))


@event.route("/modify_event/<int:event_id>", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def admin_modify_event(event_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))
    
    event = Event.query.filter(Event.id == event_id).first()
    
    distance_set = DistancesTable.query.filter(DistancesTable.event_id == event.id).all()

    form = EventForm(name = event.name,
            start = event.start,
            length = event.length_weeks,
            status = event.status,
            coefficientsSetName = "---")

    formDist = DistancesForm(w1 = distance_set[0].target,
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
    new_sport_form.activity_type.choices = Sport.all_sports()

    #Creating list of available admins (for form)
    admins=User.query.filter(User.is_admin == True).all()
    admin_ids = [(a.id, a.name) for a in admins]
    form.adminID.choices=admin_ids

    form.status.choices = Event.status_options

    coefficientsSet = CoefficientsList.query.filter(CoefficientsList.event_id == event.id).all()

    if form.validate_on_submit and formDist.validate_on_submit():

        #changeEvent(event.id, form, formDist)
        event.modify(form, formDist)
    
        flash('Zmodyfikowano wydarzenie form"{}"!'.format(form.name.data))
        return redirect(url_for('event.admin_list_of_events'))

    return render_template("/pages/modify_event.html",
                    title_prefix = "Modfyfikuj wydarzenie",
                    form = form,
                    formDist = formDist,
                    new_sport_form = new_sport_form,
                    mode = "edit",
                    event_id = event.id,
                    CoefficientsSet = coefficientsSet)


@event.route('/addNewSportToEvent/<int:event_id>', methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def add_new_sport_to_event(event_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))
    
    sport_to_add = Sport.query.filter(Sport.id == request.form['activity_type']).first()

    if CoefficientsList.query.filter(CoefficientsList.activity_type_id == sport_to_add.id).filter(CoefficientsList.event_id == event_id).first() == None:

        new_coefficient = CoefficientsList(
                            event_id = event_id,
                            activity_type_id = sport_to_add.id,
                            value = sport_to_add.default_coefficient,
                            is_constant = sport_to_add.default_is_constant)

        db.session.add(new_coefficient)
        db.session.commit()
        flash(f"Dodano {sport_to_add.name} do wyzwania!", "success")
    
    else:
        flash("Ten sport już znajduje się w wyzwaniu!")
    
    return redirect(url_for('event.admin_modify_event', event_id = event_id))


@event.route("/deleteCoeficientSport/<int:event_id>/<int:activity_type_id>")
@account_confirmation_check
@login_required #This page needs to be login
def delete_coefficient(event_id, activity_type_id):


    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    positionToDelete = CoefficientsList.query.filter(CoefficientsList.event_id == event_id).filter(CoefficientsList.activity_type_id == activity_type_id).first()
    if positionToDelete != None:
        db.session.delete(positionToDelete)
        db.session.commit()

    return redirect(url_for('event.admin_modify_event', event_id = event_id))


@event.route("/modifyCoeficientSport/<int:event_id>/<int:activity_type_id>", methods=['POST', 'GET'])
@account_confirmation_check
@login_required #This page needs to be login
def modify_coefficient(event_id, activity_type_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    coefficient_to_modify = CoefficientsList.query.filter(CoefficientsList.event_id==event_id).filter(CoefficientsList.activity_type_id==activity_type_id).first()

    form = CoeficientsForm(event_name = coefficient_to_modify.event,
        activity_name = coefficient_to_modify.sport,
        value = coefficient_to_modify.value,
        is_constant = coefficient_to_modify.is_constant )

    if form.validate_on_submit():

        coefficient_to_modify.value = form.value.data
        coefficient_to_modify.is_constant= form.is_constant.data
        db.session.commit()
    
        return redirect(url_for('event.admin_modify_event', event_id = event_id))

    return render_template("/pages/modify_coeficients.html",
                    title_prefix = "Nowa tabela współczynników",
                    form = form,
                    event_id = event_id,
                    activity_type_id = activity_type_id)


@event.route('/addNewSport/', methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def add_new_sport_to_base():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    form = CoeficientsForm()
    del form.event_name

    if form.validate_on_submit():
        new_sport = Sport(
            name = form.activity_name.data,
            default_coefficient = form.value.data,
            default_is_constant = form.is_constant.data)

        db.session.add(new_sport)
        db.session.commit()
        return redirect(url_for('event.admin_list_of_sports'))

    return render_template("/pages/new_sport_to_db.html",
                    title_prefix = "Nowy sport",
                    form = form) 


@event.route('/deleteSport/<int:sport_id>', methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def delete_sport_from_base(sport_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    sport_to_delete = Sport.query.filter(Sport.id == sport_id).first()
    db.session.delete(sport_to_delete)
    db.session.commit()

    return redirect(url_for('event.admin_list_of_sports'))


@event.route('/modifySport/<int:sport_id>', methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def modify_sport_in_base(sport_id):

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej akcji")
        return redirect(url_for('other.hello'))

    sport_to_modify = Sport.query.filter(Sport.id == sport_id).first()

    form = CoeficientsForm(activity_name = sport_to_modify.name,
                        value = sport_to_modify.default_coefficient,
                        is_constant = sport_to_modify.default_is_constant)
    del form.event_name

    if form.validate_on_submit():

        sport_to_modify.name = form.activity_name.data
        sport_to_modify.default_coefficient = form.value.data
        sport_to_modify.default_is_constant = form.is_constant.data

        db.session.commit()

        return redirect(url_for('event.admin_list_of_sports'))

    return render_template("/pages/modify_sport_in_db.html",
                    title_prefix = "Nowy sport",
                    form = form,
                    mode = 'edit',
                    sport_id = sport_id) 








###############################################


def copy_participation_from_csv(file_path):

    with open(file_path, encoding="utf8") as participation_file:
        a = csv.DictReader(participation_file)
        for row in a:
            new_participatoin = Participation(user_id = row["user_name"], event_id = row["event_id"] )

            try:
                db.session.add(new_participatoin)
                db.session.commit()
            except:
                print('error', row['event_ID'])

    return True


def copy_distances_from_csv(file_path):

    with open(file_path, encoding="utf8") as distances_file:
        a = csv.DictReader(distances_file)
        for row in a:

            if row["event_ID"] == '2' or row["event_ID"] == '3' or row["event_ID"] == '4' or row["event_ID"] == '5':
                new_distance = DistancesTable(event_id = row["event_ID"], week = row["week"], target=row['value'] )

                try:
                    db.session.add(new_distance)
                    db.session.commit()
                except:
                    print('error', row['event_ID'])

    return True


from activity.classes import Sport
def copy_coefficients_from_csv(file_path):

    with open(file_path, encoding="utf8") as coefficients_file:
        a = csv.DictReader(coefficients_file)
        for row in a:
            if row["activityName"] == "Narciarstwo zjadowe":
                row["activityName"] = "Narciarstwo zjazdowe"

            if row['activityName'] == "Wspinaczka ":
                row['activityName'] = "Wspinaczka"

            if row["constant"] == '0':
                row["constant"] = False
            
            else:
                row["constant"] = True

            full_name = row["activityName"]
    
            activity_id = Sport.query.filter(Sport.name == full_name).first()

            if row['setName'] == '1':
                new_coefficient = CoefficientsList(event_id = 2, activity_type_id = activity_id.id , value = row['value'], is_constant = row['constant'] )
                db.session.add(new_coefficient)

            elif row['setName'] == 'DlaKsiegowych2':
                new_coefficient = CoefficientsList(event_id = 3, activity_type_id = activity_id.id , value = row['value'], is_constant = row['constant'] )
                db.session.add(new_coefficient)
            
            elif row['setName'] == 'Biegowe Świry 8':
                new_coefficient = CoefficientsList(event_id = 5, activity_type_id = activity_id.id , value = row['value'], is_constant = row['constant'] )
                new_coefficient2 = CoefficientsList(event_id = 4, activity_type_id = activity_id.id , value = row['value'], is_constant = row['constant'] )
                db.session.add(new_coefficient)
                db.session.add(new_coefficient2)

    db.session.commit()
    return True


def copy_events_from_csv(file_path):

    with open(file_path, encoding="utf8") as events_file:
        a = csv.DictReader(events_file)
        for row in a:

            if row["isPrivate"] == 'NULL' or row["isPrivate"] == '0':
                row["isPrivate"] = False
            else:
                row["isPrivate"] = True

            if row["isSecret"] == 'NULL' or row["isSecret"] == '0':
                row["isSecret"] = False
            else:
                row["isSecret"] = True

            (y1, m1, d1) = row['start'].split('-')
            start = dt.date(int(y1),int(m1),int(d1))

            new_event = Event(id = row["id"], name = row["name"], start = start, length_weeks = row["lengthWeeks"], 
            password = row["password"], admin_id = row["adminID"], status = row["status"], is_private = row["isPrivate"], is_secret = row["isSecret"], max_user_amount = row['maxUserAmount'] )

            db.session.add(new_event)
            db.session.commit()

    return True

