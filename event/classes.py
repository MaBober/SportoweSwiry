from flask_login import current_user
from flask import redirect, url_for, current_app
import hashlib
import binascii
from start import db
import datetime as dt
import pandas as pd
from activity.classes import Activities
import numpy as np


from activity.classes import Sport
import math

#Defines event table
class Event(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start = db.Column(db.Date, nullable=False)
    length_weeks = db.Column(db.Integer,nullable=False)
    admin_id = db.Column(db.String(50), db.ForeignKey('user.id')) 
    status = db.Column(db.String(50), nullable=False)
    is_private = db.Column(db.Boolean, nullable=False)
    is_secret = db.Column(db.Boolean, nullable=False)
    password = db.Column(db.String(500))
    max_user_amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(300))
    added_on = db.Column(db.DateTime, default = dt.datetime.now())

    participants = db.relationship('Participation', backref='event', lazy='dynamic')
    distance_set = db.relationship('DistancesTable', backref='event', lazy='dynamic')
    coefficients_list = db.relationship('CoefficientsList', backref='event', lazy='dynamic')

    status_options = ['Zapisy otwarte', 'W trakcie', 'Zakończone']

    def __repr__(self):
        return self.name


    def add_to_db(self, form):

        from .forms import DistancesForm

        current_app.logger.info(f"User {current_user.id} submited new event form")

        self.name = form.name.data
        self.start = form.start.data
        self.length_weeks = form.length.data
        self.admin_id = current_user.id
        self.is_private = form.isPrivate.data
        self.is_secret = False
        self.max_user_amount = form.max_users.data
        self.password = form.password.data
        self.password = self.hash_password()
        self.description = form.description.data
        self.status = 0

        distances_form = DistancesForm(w1 = 10,
            w2 = 10,
            w3 = 10,
            w4 = 10,
            w5 = 10,
            w6 = 10,
            w7 = 10,
            w8 = 10,
            w9 = 10,
            w10 = 10,
            w11 = 10,
            w12 = 10,
            w13 = 10,
            w14 = 10,
            w15 = 10)

        try:
            db.session.add(self)
            db.session.commit()
            
            DistancesTable.pass_distances_to_db(distances_form, self.id) 
            current_app.logger.info(f"User {current_user.id} created targets table for event {self.id}")
            self.add_partcipant(current_user, form.password.data)

            current_app.logger.info(f"User {current_user.id} created event {self.id}")
            message = 'Stworzono wydarzenie "{}"!'.format(self.name)
            return message, 'success', redirect(url_for('event.define_event_targets', event_id = self.id))

        except:
            current_app.logger.exception(f"User {current_user.id} failed to add new event")
            return 'Wyzwanie NIE UTWORZONE! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem', 'danger', 'event.new_event'

    def modify_targets(self, distance_form):
        current_app.logger.info(f"User {current_user.id} submited modify targets form for event {self.id}")

        try:
            oldDistances =  DistancesTable.query.filter(DistancesTable.event_id == self.id).all()

            for position in oldDistances:
                db.session.delete(position)
                db.session.commit()

            DistancesTable.pass_distances_to_db(distance_form, self.id)

            current_app.logger.info(f"User {current_user.id} modified event {self.id} targets")
            message = f"Zmodyfikowano cele tygodniowe wyzwania {self.name}"
            return message, 'success', redirect(url_for('event.modify_event', event_id = self.id))

        except:
            current_app.logger.exception(f"User {current_user.id} failed to modify event {self.name} targets.")
            message = f'Cele tygodniowe {self.name} NIE ZDMODYFIKOWANE!'
            return message, 'danger', redirect(url_for('event.modify_event', event_id = self.id))

    def modify(self, form, distance_form):

        current_app.logger.info(f"User {current_user.id} submited modify form for event {self.id}")

        try:

            self.name = form.name.data
            self.start = form.start.data
            self.length_weeks = form.length.data
            self.is_private = form.isPrivate.data
            self.description = form.description.data
            self.password = form.password.data
            self.password = self.hash_password()
            self.max_user_amount  = form.max_users.data

            self.update_status()
            db.session.commit()

            current_app.logger.info(f"User {current_user.id} modified event {self.id}")
            message = f"Zmodyfikowano wyzwanie {self.name}"
            return message, 'success', redirect(url_for('event.modify_event', event_id = self.id))

        except:
            current_app.logger.exception(f"User {current_user.id} failed to modify event {self.name}.")
            message = f'Wyzwanie {self.name} NIE ZDMODYFIKOWANE!'
            return message, 'danger', redirect(url_for('event.modify_event', event_id = self.id))


    def delete(self):

        event_name = self.name

        if not current_user.is_admin:
            current_app.logger.warning(f"User {current_user.id} tries to delete event {self.id}. He is not an admin!")
            message = "Nie masz uprawnień do tej zawartości!"
            return message, 'danger', redirect(url_for('other.hello'))
        
        current_app.logger.info(f"Admin {current_user.id} tries to delete event {self.id}.")
        try:
            distances = DistancesTable.query.filter(DistancesTable.event_id == self.id).all()

            for distance in distances:
                db.session.delete(distance)
                db.session.commit()
            current_app.logger.info(f"Admin {current_user.id} deleted distances table in event {event_name}.")

            coefficients = CoefficientsList.query.filter(CoefficientsList.event_id == self.id).all()

            for coefficient in coefficients:
                db.session.delete(coefficient)
                db.session.commit()
            current_app.logger.info(f"Admin {current_user.id} deleted coeficients table in event {event_name}.")

            partcipants = Participation.query.filter(Participation.event_id == self.id).all()

            for participant in partcipants:
                db.session.delete(participant)
                db.session.commit()
            current_app.logger.info(f"Admin {current_user.id} deleted all participants from event {event_name}.")

            db.session.delete(self)
            db.session.commit()

            message = f"Usunięto wyzwanie {event_name}"
            current_app.logger.info(f"Admin {current_user.id} deleted event {event_name}.")
            return message, 'success', redirect(url_for('event.admin_list_of_events'))

        except:
            current_app.logger.exception(f"Admin {current_user.id} failed to delet event {event_name}.")
            message = f'Wyzwanie {event_name} NIE USUNIĘTE!'
            return message, 'danger', redirect(url_for('event.admin_list_of_events'))


    def add_partcipant(self, user, provided_password = '') :

        current_app.logger.info(f"User {current_user.id} tries to join event {self.id}")

        is_participating = Participation.query.filter(Participation.user_id == user.id).filter(Participation.event_id == self.id).first()

        if self.status not in ['0','1']:
            message = f"Wyzwanie {self.name} już się rozpoczęło, nie możesz się do niego dopisać!"
            current_app.logger.warning(f"User {current_user.id} tries to join event {self.id}. Event is on going!")
            return message, 'danger', redirect(url_for('event.explore_events'))

        event_password = self.password
        verify = Event.verify_password(event_password, provided_password)

        if self.is_private and verify is not True:
            message = "Podałeś/aś złe hasło do wyzwania. Spróbuj jeszcze raz!"
            current_app.logger.info(f"User {current_user.id} give wrong password for event {self.id}")
            return message, 'danger', redirect(url_for('event.explore_events'))

        if is_participating is not None:
            message = "Już jesteś zapisny/a na to wyzwanie!"
            current_app.logger.info(f"User {current_user.id} tries to join event {self.id}. Already takes part in it!")
            return message, 'danger', redirect(url_for('event.explore_events'))

        if self.is_full:
            message = "Do tego wyzwania zapisała się już maksymalna ilość uczestników!"
            current_app.logger.info(f"User {current_user.id} tries to join event {self.id}. Event is full!")
            return message, 'danger', redirect(url_for('event.explore_events'))

        from other.functions import send_email

        send_email(current_user.mail, "Witaj w wyzwaniu {}".format(self.name),'welcome', event = self, user = current_user)

        message = '''
        Czołem  {} {}!,

        Witaj w wyzwaniu sportowym {}!

        Data rozpoczęcia: {}
        Długość: {} tygodni

        Życzymy samych sukcesów i wielu pokonanych kilometrów.

        Ubieraj buty i zaczynaj zabawę już dziś! ;)

        Pozdrawiamy,

        Administracja Sportowych Świrów
        '''.format(current_user.name, current_user.last_name, self.name, self.start, self.length_weeks)

        # newMessage = MailboxMessage(date=datetime.date.today(), sender="Sportowe Świry", senderName="Sportowe Świry", receiver = current_user.mail,
        # receiverName = current_user.name+" "+current_user.lastName, subject = "Witaj w wyzwaniu: " + event.name, message = message, sendByApp = True,
        # sendByEmail= False, messageReaded=False, multipleMessage=True)
        # sendMessgaeFromContactFormToDB(newMessage)

        try:
            participation = Participation(user_id = user.id, event_id = self.id)
            db.session.add(participation)
            db.session.commit()

            message = "Zapisano do wyzwania " + self.name + "!"
            current_app.logger.info(f"User {current_user.id} joined event {self.id}")
            return message, 'success', redirect(url_for('event.event_main', event_id = self.id))

        except:
            message = "NIE DODANO DO WYZWANIA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
            current_app.logger.exception(f"User {current_user.id} failed to join event {self.id}")
            return message, 'danger', redirect(url_for('event.explore_events'))

    
    def leave_event(self, user):

        current_app.logger.info(f"User {current_user.id} tries to erase {user.id} from event {self.id}.")
        is_participating = Participation.query.filter(Participation.user_id == user.id).filter(Participation.event_id == self.id).first()

        if self.admin_id == user.id:
            message = "Administrator nie może opuścić swojego wyzwania!"
            current_app.logger.info(f"User {current_user.id} tries to leave event {self.id}. He is admin of that event!")
            return message, "danger", redirect(url_for('event.event_contestants', event_id = self.id))

        if current_user.is_admin != True:
            
            if current_user.id != user.id:
                message = "Nie można usunąć innego użytkownika z wyzwania!"
                current_app.logger.warning(f"User {current_user.id} tries to delete other user from event {self.id}!")
                return message, "danger", redirect(url_for('event.explore_events', event_id = self.id))

            if is_participating != None and self.status != "0":
                message = "Nie możesz się wypisać z rozpoczętego wyzwania!"
                current_app.logger.warning(f"User {current_user.id} tries to leave event {self.id}. Event is on going!")
                return message, "danger", redirect(url_for('event.explore_events', event_id = self.id))
            
            if is_participating == None:
                message = "Nie jesteś zapisany na to wyzwanie!"
                current_app.logger.warning(f"User {current_user.id} tries to leave event {self.id}. Does not take part in it!")
                return message, "danger", redirect(url_for('event.explore_events', event_id = self.id))

            try:
                db.session.delete(is_participating)
                db.session.commit()
            
                message = f"Wypisano z wyzwania {self.name}!"
                current_app.logger.info(f"User {current_user.id} left event {self.id}")
                return message, "success", redirect(url_for('event.explore_events'))

            except:
                message = "NIE WYPISANO Z WYDARZENIA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
                current_app.logger.exception(f"User {current_user.id} failed to leave event {self.id}")
                return message, "danger", redirect(url_for('event.explore_events', event_id = self.id))

        else:

            if is_participating == None:
                message = f"Użytkownik {user.name} nie jest zapisany wyzwanie {self.name}!"
                current_app.logger.warning(f"Admin {current_user.id} tries to erase user {user.id} from event {self.id}. He does not take part in it!")
                return message, "danger", redirect(url_for('event.event_contestants', event_id = self.id))

            try:
                db.session.delete(is_participating)
                db.session.commit()
            
                message = f"Użytkownik {user.name} wypisany z wyzwania {self.name}!"
                current_app.logger.info(f"Admin {current_user.id} deleted user {user.name} from event {self.id}")
                return message, "success", redirect(url_for('event.event_contestants', event_id = self.id))

            except:
                message = "NIE WYPISANO Z WYDARZENIA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
                current_app.logger.exception(f"Admin {current_user.id} failed to erase user {user.id} from event {self.id}")
                return message, "danger", redirect(url_for('event.event_contestants', event_id = self.id))
            
        
    def is_participant(self, user):

        if Participation.query.filter(Participation.event_id == self.id).filter(Participation.user_id == user.id).first() is None:
            return False
            
        else:
            return True

        
    def hash_password(self):
        """Hash a password for storing."""
        # the value generated using os.urandom(60)
        os_urandom_static = b"ID_\x12p:\x8d\xe7&\xcb\xf0=H1\xc1\x16\xac\xe5BX\xd7\xd6j\xe3i\x11\xbe\xaa\x05\xccc\xc2\xe8K\xcf\xf1\xac\x9bFy(\xfbn.`\xe9\xcd\xdd'\xdf`~vm\xae\xf2\x93WD\x04"
        #os_urandom_static = b"ID_\x12p:\x8d\xe7&\xcb\xf0=H1"
        salt = hashlib.sha256(os_urandom_static).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', self.password.encode('utf-8'), salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii') 


    def verify_password(stored_password, provided_password):
        """Verify a stored password against one provided by user"""
        salt = stored_password[:64]
        stored_password = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'),
        salt.encode('ascii'), 100000)
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        return pwdhash == stored_password


    @property
    def end(self):
        return self.start + dt.timedelta(weeks = self.length_weeks, days=-1)


    @property
    def status_description(self):

        statuses = {"0" : "Zapisy otwarte",
                    "1" : "Pierwszy tydzień",
                    "2" : "W trakcie",
                    "3" : "Ostatni tydzień",
                    "4" : "Wyzwanie zakończone",
                    "5" : "Wyzwanie archiwalne"}

        return statuses[self.status]


    def update_status(self):

        if self.start > dt.date.today():
            #log.append((self.name, "Nie rozpoczęło się 0"))
            self.status = '0'

        elif self.start <= dt.date.today() and self.start + dt.timedelta(7) > dt.date.today():
            #log.append((self.name, "Pierwszy tydzień 1"))
            self.status = '1'

        elif self.start + dt.timedelta(7) <= dt.date.today() and self.end + dt.timedelta(-6) > dt.date.today():
            #self.append((self.name, "W trakcie 2"))
            self.status = '2'

        elif self.end + dt.timedelta(-6) <= dt.date.today() and dt.date.today() <= self.end:
            #log.append((self.name, "Ostatni tydzień 3"))
            self.status = '3'

        elif self.end < dt.date.today() and dt.date.today() <= self.end + dt.timedelta(7):
            #log.append((event.name, "Tydzień po 4"))
            self.status = '4'

        else:
           # log.append((event.name, "zakończone! 5"))
            self.status = '5'

        db.session.commit()

        return None

    def add_sport(self, sport_to_add):
        current_app.logger.info(f"User {current_user.id} tries to add {sport_to_add.name} to event {self.id}.")
        if CoefficientsList.query.filter(CoefficientsList.activity_type_id == sport_to_add.id).filter(CoefficientsList.event_id == self.id).first() == None:
            try:
                new_coefficient = CoefficientsList(
                                    event_id = self.id,
                                    activity_type_id = sport_to_add.id,
                                    value = sport_to_add.default_coefficient,
                                    is_constant = sport_to_add.default_is_constant)

                db.session.add(new_coefficient)
                db.session.commit()

                message = f"Dodano {sport_to_add.name} do wyzwania!"
                current_app.logger.info(f"User {current_user.id} added {sport_to_add.name} to event {self.id}.")
                return message, "success", redirect(url_for('event.modify_event', event_id = self.id))

            except:
                message = "NIE DODANO SPORTU! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
                current_app.logger.exception(f"User {current_user.id} failed to add {sport_to_add.name} to event {self.id}")
                return message, "danger", redirect(url_for('event.event_contestants', event_id = self.id))

        else:
            message = "Ten sport już znajduje się w wyzwaniu!"
            current_app.logger.info(f"User {current_user.id} added {sport_to_add.name} to event {self.id}. It is already in it!")
            return message, 'message', redirect(url_for('event.modify_event', event_id = self.id))

    
    def delete_sport(self, sport_to_delete):

        current_app.logger.info(f"User {current_user.id} tries to delete {sport_to_delete} from event {self.id}.")
        position_to_delete = CoefficientsList.query.filter(CoefficientsList.event_id == self.id).filter(CoefficientsList.activity_type_id == sport_to_delete).first()

        if position_to_delete != None:

            try:
                db.session.delete(position_to_delete)
                db.session.commit()

                message = f'Usunięto sport z wyzwania!'
                current_app.logger.info(f"User {current_user.id} deleted {sport_to_delete} from event {self.id}.")
                return message, 'success', redirect(url_for('event.modify_event', event_id = self.id))


            except:
                message = "NIE USUNIĘTO SPORTU! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
                current_app.logger.exception(f"User {current_user.id} failed to delete {sport_to_delete} from event {self.id}")
                return message, "danger", redirect(url_for('event.modify_event', event_id = self.id))

        else:
            message = f'Sport nie znajduje się w wyzwaniu!'
            current_app.logger.warning(f"User {current_user.id} tried delete {sport_to_delete} from event {self.id}. There is no such sport in this event!")
            return message, 'danger', redirect(url_for('event.modify_event', event_id = self.id))


    def modifiy_sport_coefficient(self, sport_to_modify, coefficient_form):
        current_app.logger.info(f"User {current_user.id} tries to modify {sport_to_modify} in event {self.id}.")

        if sport_to_modify != None:
            try:
                sport_to_modify.value = coefficient_form.value.data
                sport_to_modify.is_constant= coefficient_form.is_constant.data
                db.session.commit()

                message = f'Zmodyfikowano współczynnik wyzwania!'
                current_app.logger.info(f"User {current_user.id} modified {sport_to_modify.activity_type_id} in event {self.id}.")
                return message, 'success', redirect(url_for('event.modify_event', event_id = self.id))

            except:
                message = "NIE ZMIENIONO WSPÓŁCZYNNIKA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
                current_app.logger.exception(f"User {current_user.id} failed to modifiy {sport_to_modify.activity_type_id} in event {self.id}")
                return message, "danger", redirect(url_for('event.modify_event', event_id = self.id))
        
        else:
            message = f'Sport nie znajduje się w wyzwaniu!'
            current_app.logger.warning(f"User {current_user.id} tried delete {sport_to_modify.activity_type_id} in event {self.id}. There is no such sport in this event!")
            return message, 'danger', redirect(url_for('event.modify_event', event_id = self.id))

        

    def give_all_event_activities(self, calculated_values = False, user = 'all'):

        event_particitpants_ids = self.give_all_event_users_ids()
        event_activity_types_ids = self.give_all_event_activities_types()

        if user == "all":
            event_activities_sql = Activities.query.filter(Activities.date >= self.start) \
                .filter(Activities.date <= self.end) \
                .filter(Activities.activity_type_id.in_(event_activity_types_ids)) \
                .filter(Activities.user_id.in_(event_particitpants_ids)) \
                .order_by(Activities.date.desc())
        
        else:
            event_activities_sql = Activities.query.filter(Activities.date >= self.start) \
                .filter(Activities.date <= self.end) \
                .filter(Activities.activity_type_id.in_(event_activity_types_ids)) \
                .filter(Activities.user_id == user) \
                .order_by(Activities.date.desc())

        all_event_activities = pd.read_sql(event_activities_sql.statement, db.engine, index_col='id')

        if calculated_values:
            
            all_sports = pd.read_sql('SELECT id, name FROM sport', db.engine)
            event_participants = self.give_all_event_users(scope = "Names")

            event_coefficients_set = CoefficientsList.query.filter(CoefficientsList.event_id == self.id)
            event_coefficients_set = pd.read_sql(event_coefficients_set.statement, db.engine, index_col = 'event_id') 
  

            event_activities_calculated_values = all_event_activities.merge(event_coefficients_set, on = ['activity_type_id'])

            if event_activities_calculated_values.empty:
                event_activities_calculated_values = event_activities_calculated_values.append({'user_id' : '---', 'date' : '---', 'distance' : 0, 'time' : 0, 'strava_id' : '---', 'activity_type_id' : '---', 'value' : 0, 'is_constant' : False } ,ignore_index=True)
                event_activities_calculated_values['calculated_distance'] = 0

            else:
                event_activities_calculated_values['calculated_distance'] = event_activities_calculated_values.apply(calculate_distance, axis=1)

            
            event_activities_calculated_values = event_activities_calculated_values.merge(event_participants, left_on = 'user_id', right_on = 'id')
            event_activities_calculated_values = event_activities_calculated_values.merge(all_sports, left_on = 'activity_type_id', right_on = 'id', suffixes =['','_sport'])

            event_activities_calculated_values = event_activities_calculated_values.sort_values('date', ascending = False)

            return event_activities_calculated_values

        return all_event_activities


    def give_all_event_users(self, scope = "Names"):
        from user.classes import User
        if scope == 'Names':
            if len(self.give_all_event_users_ids()) > 1:
                event_participants = pd.read_sql(f'SELECT id, name, last_name FROM user WHERE id in {tuple(self.give_all_event_users_ids())} ', db.engine, index_col = 'id' ) 
            elif len(self.give_all_event_users_ids()) == 1:
                event_participants = pd.read_sql(f"SELECT id, name, last_name FROM user WHERE id = '{self.give_all_event_users_ids()[0]}' ", db.engine, index_col = 'id' )
            else:
                event_participants = []
            
            return event_participants
        
        elif scope == "Full":
            event_participants = pd.read_sql(f'SELECT * FROM user WHERE id in {tuple(self.give_all_event_users_ids())} ', db.engine, index_col = 'id' ) 

        elif scope == "Objects":

            event_participants = self.give_all_event_users_ids()
            event_participants = User.query.filter(User.id.in_(event_participants)).all()

        elif scope == "Objects_Dictionary":

            if len(self.give_all_event_users_ids()) == 0:
                event_participants = None

            else: 
                event_participants_query = self.give_all_event_users_ids()
                event_participants_query  = User.query.filter(User.id.in_(event_participants_query)).all()

                event_participants = {}

                for user in event_participants_query:
                    event_participants[user.id] = user

        return event_participants


    def give_all_event_users_ids(self):

        event_participations = Participation.query.filter(Participation.event_id==self.id)
        event_participations = pd.read_sql(event_participations.statement, db.engine, index_col='user_id')

        event_participations = event_participations.index.values.tolist()
        
        return event_participations


    def give_all_event_activities_types(self, mode = "id"):

        event_activity_types = CoefficientsList.query.filter(CoefficientsList.event_id==self.id)

        if mode == "id":
            event_activity_types = pd.read_sql(event_activity_types.statement, db.engine, index_col = 'activity_type_id')
            event_activity_ids = event_activity_types.index.values.tolist()
            return event_activity_ids
        
        else:
            all_sports = pd.read_sql(Sport.query.statement, db.engine)
            event_activity_types = pd.read_sql(event_activity_types.statement, db.engine, index_col = 'activity_type_id')
  
            event_activity_types = event_activity_types.merge(all_sports,left_index = True, right_on='id')
            
            return event_activity_types

    @property
    def current_week(self):

        if dt.date.today() >= self.start:
            days = abs(dt.date.today() - self.start).days
            presentWeek = math.ceil((days+1)/7) 
        else:
            presentWeek = 0

        if dt.date.today() > self.start + dt.timedelta(weeks=self.length_weeks, days = -1):
                presentWeek = self.length_weeks

        return presentWeek
    
    @property
    def week_targets(self):

        event_week_targets = pd.read_sql(f"SELECT * FROM distances_table WHERE event_id = {self.id}", db.engine)
        event_week_targets['week'] = event_week_targets['week'].astype(int)

        return event_week_targets
    
    @property
    def current_week_target(self):

        if self.status in ['1','2','3']:
            current_event_week_target = self.week_targets[self.week_targets['week'] == self.current_week]['target'].values[0]
        else:
            return 0

        return current_event_week_target

    @property
    def is_full(self):

        if len(self.participants.all()) >= self.max_user_amount:
            return True
        
        else:
            return False

    def give_overall_weekly_summary(self, activites_list):

        #CREATE EMPTY ACTIVITIES FOR ALL USERS

        users = self.give_all_event_users(scope = 'Objects')
        for user in users:
            activites_list = activites_list.append({'user_id': user.id, 'activity_type_id':1, 'date':self.start, 'distance':1, 'time':0, 'calculated_distance':0, 'name':user.name, 'last_name':user.last_name}, ignore_index=True)

        # CREATE PIVOT TABLE FOR WHOLE EVENT
        activities_pivot = activites_list.pivot_table(index="date", columns =['user_id','name','last_name'], values=['calculated_distance'], aggfunc='sum')
        activities_pivot = activities_pivot.fillna(value=0)
        activities_pivot = activities_pivot.round(decimals = 2)

        # CREATE LIST OF ALL DATES IN EVENT, TO PUT EMPTY DATES TO PIVOT TABLE
        event_days_timestamps = []

        for i in range(0, self.length_weeks*7):
            event_days_timestamps.append(self.start + dt.timedelta(days=i))

        event_days = {"date" : event_days_timestamps}
        event_days = pd.DataFrame(event_days)

        tt = activites_list['date'].append(event_days['date']).unique()
        
        activities_pivot = activities_pivot.reindex(tt, fill_value=0)
        activities_pivot = activities_pivot.sort_values('date')

        # SPLIT PIVOT TABLES FOR WEEK SUB-TABLES
        split_list =  np.array_split(activities_pivot, self.length_weeks)

        # ADD TOTAL WEEK AND TARGET ROWS
        def check_target(row, week_number):
            
   
            if row == 0 and self.week_targets['target'][week_number-1] !=0 :
                return False
            elif row == 0 and self.week_targets['target'][week_number-1] == 0:
                 return True               
            elif row >= self.week_targets['target'][week_number-1]:
                return True
            else:
                return False

        
        for index, single_week in enumerate(split_list,start=1):
            if single_week.empty:
                for user in self.give_all_event_users("Objects"):
                    single_week['calculated_distance', user.id, user.name, user.last_name ] = 0
                single_week.loc['total'] = 0

                if self.status != '0':
                    single_week.loc['target_done'] = single_week.loc['total'].apply(check_target,  week_number=(index))
                else:
                    single_week.loc['target_done'] = False
                
            else:
                single_week.loc['total'] = single_week.sum()
                single_week.loc['total'] = single_week.loc['total'].round(decimals = 2)
                single_week.loc['target_done'] = single_week.loc['total'].apply(check_target,  week_number=(index))

        return split_list

    def give_beers_summary(self, activites_list):

        event_participants = self.give_all_event_users(scope = 'Objects_Dictionary')

        ### Create SUM table
        beer_summray = pd.DataFrame()
        for week in activites_list:
            beer_summray = pd.concat([beer_summray, week])

        beer_summray = beer_summray.loc['target_done']

        beers_to_buy = { i : 0 for i in event_participants.keys() }
        beers_to_recive = {i : 0 for i in event_participants.keys() }

        for week in range(1, self.length_weeks):
            for user in event_participants:
                if beer_summray.iloc[week]['calculated_distance',user][0] == 1:
                    try:
                        beers_to_recive[user] += beer_summray.iloc[week]['calculated_distance'].value_counts()[0]
                    except:
                        pass
                else:
                    try:
                        beers_to_buy[user] += beer_summray.iloc[week]['calculated_distance'].value_counts()[1]
                    except:
                        pass

        return {'beers_to_buy': beers_to_buy, 'beers_to_recive' : beers_to_recive}

    def give_user_overall_summary(self, user_id):

        user_overall_summary = {}

        #Return event data to present
        user_activites =  self.give_all_event_activities(calculated_values = True, user = user_id)

        if not user_activites.empty:

            user_distance_sum = user_activites['calculated_distance'].sum()
            user_distance_sum = round(user_distance_sum,0)
            user_overall_summary['user_distance_sum'] = user_distance_sum
            
            user_time_sum = user_activites['time'].sum()
            user_activites_amount = len(user_activites)

            try:
                average_time = (user_time_sum/user_activites_amount)
                average_time = round(average_time, 0)
                average_time = str(dt.timedelta(seconds = average_time))
                user_overall_summary['average_time'] = average_time
            except:
                current_app.logger.warning(f"Error in: average_time=user_time_sum/user_activites_amount")
                user_overall_summary['average_time'] = '---'
            
            try:
                average_distance_for_event = user_distance_sum/user_activites_amount
                average_distance_for_event = round(average_distance_for_event, 2)
                user_overall_summary['average_distance_for_event'] = average_distance_for_event

            except:
                current_app.logger.warning(f"Erroe in: average_distance_for_event = user_distance_sum/user_activites_amount")
                user_overall_summary['average_distance_for_event'] = '---'

        else:
            user_overall_summary['user_distance_sum'] = '---'
            user_overall_summary['average_time'] = '---'
            user_overall_summary['average_distance_for_event'] = '---'

        return user_overall_summary
    
    @classmethod
    def available_to_join(cls):
        return cls.query.filter(cls.status.in_(['0','1'])).all()

    
    @classmethod
    def added_in_last_days(cls, days):

        inserts = cls.query.filter(cls.added_on < dt.date.today()).filter(cls.added_on > dt.date.today() - dt.timedelta(days=days)).all()

        return len(inserts)
        
# Defines tabele, which connect users with events
class Participation(db.Model):

    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)


class CoefficientsList(db.Model):

    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    activity_type_id = db.Column(db.Integer, db.ForeignKey('sport.id'), primary_key=True)
    value = db.Column(db.Float, nullable = False, default = 0)
    is_constant = db.Column(db.Boolean, nullable = False, default = False)

    def __repr__(self):
        return self.event.name

    @staticmethod
    def create_coeffciet_set_with_default_values(new_event):
        all_sports = Sport.query.all()

        current_app.logger.info(f"User {current_user.id} tries to create default coeficients for event {new_event.id}")
        try:
            for sport in all_sports:
                new_coffcient = CoefficientsList(event_id = new_event.id,
                activity_type_id = sport.id,
                value = sport.default_coefficient,
                is_constant = sport.default_is_constant)
                db.session.add(new_coffcient)
                
            db.session.commit()
            current_app.logger.info(f"User {current_user.id} created default coeficients for event {new_event.id}")

        except:
            current_app.logger.exception(f"User {current_user.id} failed to add default coefficients")
            return 'NIE UDAŁO SIĘ STWORZYĆ TABLICY WSPÓŁCZYNNIKÓW! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem', 'danger', 'other.hello'

        return None


class DistancesTable(db.Model):

    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    week = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.Float, nullable = False)

    @staticmethod
    def pass_distances_to_db(distance_form, event_id):
        try:
            newDistance = DistancesTable(event_id = event_id, week = 1, target = distance_form.w1.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 2, target = distance_form.w2.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 3, target = distance_form.w3.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 4, target = distance_form.w4.data )
            db.session.add(newDistance)
            db.session.commit()
            
            newDistance = DistancesTable(event_id = event_id, week = 5, target = distance_form.w5.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 6, target = distance_form.w6.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 7, target = distance_form.w7.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 8, target = distance_form.w8.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 9, target = distance_form.w9.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 10, target = distance_form.w10.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 11, target = distance_form.w11.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 12, target = distance_form.w12.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 13, target = distance_form.w13.data )
            db.session.add(newDistance)
            db.session.commit()

            newDistance = DistancesTable(event_id = event_id, week = 14, target = distance_form.w14.data )
            db.session.add(newDistance)
            db.session.commit()
            
            newDistance = DistancesTable(event_id = event_id, week = 15, target = distance_form.w15.data )
            db.session.add(newDistance)
            db.session.commit()

            message = "Zapisano tabelę dystansów!"
            return message, 'success', redirect(url_for('event.modify_event', event_id = event_id))
        
        except:
            current_app.logger.exception(f"User {current_user.id}  failed to creat distance table for {event_id}")
            message = 'NIE UDAŁO SIĘ MODYFIKOWAĆ TABELI DYSTANSÓW! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem'
            return message, 'danger', redirect(url_for('event.define_event_targets', event_id = event_id))

def calculate_distance(row):
    if row['is_constant']:
        return round(row['value'],2)
    else:
        return round(row['value'] * row['distance'],2)