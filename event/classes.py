from flask_login import current_user
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

    participants = db.relationship('Participation', backref='event', lazy='dynamic')
    distance_set = db.relationship('DistancesTable', backref='event', lazy='dynamic')
    coefficients_list = db.relationship('CoefficientsList', backref='event', lazy='dynamic')

    status_options = ['Zapisy otwarte', 'W trakcie', 'Zakończone']

    def __repr__(self):
        return self.name


    def add_to_db(self, form, distances_form):

        self.name = form.name.data
        self.start = form.start.data
        self.length_weeks = form.length.data
        self.admin_id = current_user.id
        self.is_private = form.isPrivate.data
        self.is_secret = form.isSecret.data
        self.max_user_amount = form.max_users.data
        self.password = form.password.data
        self.password = self.hash_password()
        self.description = form.description.data
        self.status = 1

        db.session.add(self)
        db.session.commit()
        
        DistancesTable.pass_distances_to_db(distances_form, self.id)

        self.add_partcipant(current_user)

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
        return self.start + dt.timedelta(weeks = self.length_weeks)

    @property
    def status_description(self):

        statuses = {"1" : "Zapisy otwarte",
                    "2" : "Pierwszy tydzień",
                    "3" : "W trakcie",
                    "4" : "Ostatni tydzień",
                    "5" : "Wyzwanie zakończone"}

        return statuses[self.status]

    def give_all_event_activities(self, calculated_values = False, user = 'all'):

        event_particitpants_ids = self.give_all_event_users_ids()
        event_activity_types_ids = self.give_all_event_activities_types()

        if user == "all":
            event_activities_sql = Activities.query.filter(Activities.date >= self.start) \
                .filter(Activities.date <= self.start + dt.timedelta(weeks = self.length_weeks)) \
                .filter(Activities.activity_type_id.in_(event_activity_types_ids)) \
                .filter(Activities.user_id.in_(event_particitpants_ids)) \
                .order_by(Activities.date.desc())
        
        else:
            event_activities_sql = Activities.query.filter(Activities.date >= self.start) \
                .filter(Activities.date <= self.start + dt.timedelta(weeks = self.length_weeks)) \
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

        current_event_week_target = self.week_targets[self.week_targets['week'] == self.current_week]['target'].values[0]

        return current_event_week_target

    @property
    def is_full(self):

        if len(self.participants.all()) >= self.max_user_amount:
            return True
        
        else:
            return False

    def give_overall_weekly_summary(self, activites_list):

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
        split_list =  np.array_split(activities_pivot, 10)

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

                if self.status != '1':
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
                if True:
                    if beer_summray.iloc[week]['calculated_distance',user][0]:
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
                print("Błąd w: average_time=user_time_sum/user_activites_amount")
                user_overall_summary['average_time'] = '---'
            
            try:
                average_distance_for_event = user_distance_sum/user_activites_amount
                average_distance_for_event = round(average_distance_for_event, 2)
                user_overall_summary['average_distance_for_event'] = average_distance_for_event

            except:
                print("Błąd w: average_distance_for_event = user_distance_sum/user_activites_amount")
                user_overall_summary['average_distance_for_event'] = '---'

        else:
            user_overall_summary['user_distance_sum'] = '---'
            user_overall_summary['average_time'] = '---'
            user_overall_summary['average_distance_for_event'] = '---'

        return user_overall_summary
    
    def modify(self, form, formDist):

        oldDistances =  DistancesTable.query.filter(DistancesTable.event_id == self.id).all()
        for position in oldDistances:
            db.session.delete(position)
            db.session.commit()

        DistancesTable.pass_distances_to_db(formDist, self.id)

        self.name = form.name.data
        self.start = form.start.data
        self.length_weeks = form.length.data
        self.admin_id = form.adminID.data
        self.is_private = form.isPrivate.data
        self.is_secret = form.isSecret.data
        self.status = form.status.data

        db.session.commit()

        return self.id

    def delete(self):
        
        distances = DistancesTable.query.filter(DistancesTable.event_id == self.id).all()

        for distance in distances:
            db.session.delete(distance)
            db.session.commit()

        coefficients = CoefficientsList.query.filter(CoefficientsList.event_id == self.id).all()

        for coefficient in coefficients:
            db.session.delete(coefficient)
            db.session.commit()

        partcipants = Participation.query.filter(Participation.event_id == self.id).all()

        for participant in partcipants:
            db.session.delete(participant)
            db.session.commit()

        db.session.delete(self)
        db.session.commit()

        return None


    def add_partcipant(self, user, provided_password = ''):

        is_participating = Participation.query.filter(Participation.user_id == user.id).filter(Participation.event_id == self.id).first()

        if self.status not in ['1','2']:
            message == "Wyzwanie {self.name} już się rozpoczęło, nie możesz się do niego dopisać!"
            return False, message

        event_password = self.password
        verify = Event.verify_password(event_password, provided_password)

        if self.is_private and verify is not True:
            message = "Podałeś/aś złe hasło do wyzwania. Spróbuj jeszcze raz!"
            return False, message

        if is_participating is not None:
            message = "Już jesteś zapisny/a na to wyzwanie!"
            return False , message


        if self.is_full:
            message = "Do tego wyzwania zapisała się już maksymalna ilość uczestników!"
            return False, message

        from other.functions import send_email

        send_email(current_user.mail, "Witaj w wyzwaniu {}".format(self.name),'welcome', event=self)

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


        participation = Participation(user_id = user.id, event_id = self.id)
        db.session.add(participation)
        db.session.commit()

        message = "Zapisano do wyzwania " + self.name + "!"

        return True, message
        
    def is_participant(self, user):

        if Participation.query.filter(Participation.event_id == self.id).filter(Participation.user_id == user.id).first() is None:
            return False
            
        else:
            return True
  

    

        
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

        for sport in all_sports:
            new_coffcient = CoefficientsList(event_id = new_event.id,
            activity_type_id = sport.id,
            value = sport.default_coefficient,
            is_constant = sport.default_is_constant)
            db.session.add(new_coffcient)
            
        db.session.commit()

        return None


class DistancesTable(db.Model):

    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    week = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.Float, nullable = False)

    @staticmethod
    def pass_distances_to_db(formDist, event_id):

        newDistance = DistancesTable(event_id = event_id, week = 1, target = formDist.w1.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 2, target = formDist.w2.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 3, target = formDist.w3.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 4, target = formDist.w4.data )
        db.session.add(newDistance)
        db.session.commit()
        
        newDistance = DistancesTable(event_id = event_id, week = 5, target = formDist.w5.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 6, target = formDist.w6.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 7, target = formDist.w7.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 8, target = formDist.w8.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 9, target = formDist.w9.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 10, target = formDist.w10.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 11, target = formDist.w11.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 12, target = formDist.w12.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 13, target = formDist.w13.data )
        db.session.add(newDistance)
        db.session.commit()

        newDistance = DistancesTable(event_id = event_id, week = 14, target = formDist.w14.data )
        db.session.add(newDistance)
        db.session.commit()
        
        newDistance = DistancesTable(event_id = event_id, week = 15, target = formDist.w15.data )
        db.session.add(newDistance)
        db.session.commit()

def calculate_distance(row):
    if row['is_constant']:
        return round(row['value'],2)
    else:
        return round(row['value'] * row['distance'],2)