from start import db
import datetime as dt
from flask import current_app, redirect, url_for
from flask_login import current_user

class Sport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    default_coefficient = db.Column(db.Float, nullable = False, default = 0)
    default_is_constant = db.Column(db.Boolean, nullable = False, default = False)
    category = db.Column(db.String(50), nullable = False, default = 'Other')
    strava_name = db.Column(db.String(50))

    activities = db.relationship('Activities', backref='activity_type', lazy='dynamic')
    events = db.relationship('CoefficientsList', backref='sport', lazy='dynamic')

    def __repr__(self):
        return self.name
        

    @classmethod
    def add_new(cls, new_sport_form):

        current_app.logger.info(f"Admin {current_user.id} tries to add sport '{new_sport_form.activity_name.data}' to app.")

        if new_sport_form.is_constant.data == '1':
            new_sport_form.is_constant.data = True
        else:
            new_sport_form.is_constant.data = False

        try:
            new_sport = Sport(
                name = new_sport_form.activity_name.data,
                default_coefficient = new_sport_form.value.data,
                default_is_constant = new_sport_form.is_constant.data,
                strava_name = new_sport_form.strava_name.data )

            db.session.add(new_sport)
            db.session.commit()

            message = f"Dodano sport '{new_sport.name}' do aplikacji"
            current_app.logger.info(f"Admin {current_user.id} added sport '{new_sport.name}' to app.")
            return message, "success", redirect(url_for('event.admin_list_of_sports'))
        
        except:
            message = f"NIE UDAŁO SIĘ DODAĆ NOWEGO SPORTU"
            current_app.logger.exception(f"Admin {current_user.id} failed to add sport to app")
            return message, "danger", redirect(url_for('event.admin_list_of_sports'))

    def delete(self):

        from event.classes import CoefficientsList
        
        sport_to_delete = self.name
        current_app.logger.info(f"Admin {current_user.id} tries to delete sport '{self.name}' from app.")
 
        has_activity = Activities.query.filter(Activities.activity_type_id == self.id).first()
        used_in_event = CoefficientsList.query.filter(CoefficientsList.activity_type_id == self.id).first()

        if has_activity is not None:
            
            message = f"Nie można usunąć sportu '{self.name}' z aplikacji. Jest to on użyty w zarejstrowanych aktywnościach!"
            current_app.logger.warning(f"Admin {current_user.id} didn't delete sport '{sport_to_delete}' from app. It has been used in saved activities!")
            return message, "success", redirect(url_for('event.admin_list_of_sports'))

        if used_in_event is not None:
            
            message = f"Nie można usunąć sportu '{self.name}' z aplikacji. Jest to on użyty w wyzwaniach!"
            current_app.logger.warning(f"Admin {current_user.id} didn't delete sport '{sport_to_delete}' from app. It has been used in events!")
            return message, "success", redirect(url_for('event.admin_list_of_sports'))

        try:

            db.session.delete(self)
            db.session.commit()

            message = f"Usunięto sport '{self.name}' z aplikacji"
            current_app.logger.info(f"Admin {current_user.id} deleted sport '{sport_to_delete}' from app.")
            return message, "success", redirect(url_for('event.admin_list_of_sports'))

        except:

            message = f"NIE UDAŁO SIĘ USUNĄĆ SPORTU"
            current_app.logger.exception(f"Admin {current_user.id} failed to add sport to app")
            return message, "danger", redirect(url_for('event.admin_list_of_sports'))

    
    def modify(self, sport_form):

        if sport_form.is_constant.data == '1':
            sport_form.is_constant.data = True
        else:
            sport_form.is_constant.data = False
            

        current_app.logger.info(f"Admin {current_user.id} tries to modfiy sport '{self.name}' in app.")
        try:

            self.name = sport_form.activity_name.data
            self.default_coefficient = sport_form.value.data
            self.default_is_constant = sport_form.is_constant.data
            self.strava_name = sport_form.strava_name.data

            db.session.commit()

            message = f"Zmodyfikowano sport '{self.name}' w aplikacji"
            current_app.logger.info(f"Admin {current_user.id} modified sport '{self.name}' in app.")
            return message, "success", redirect(url_for('event.admin_list_of_sports'))

        except:

            message = f"NIE UDAŁO SIĘ MODYFIKOWAĆ SPORTU"
            current_app.logger.exception(f"Admin {current_user.id} failed to modify sport in app")
            return message, "danger", redirect(url_for('event.admin_list_of_sports'))



    @staticmethod
    def all_sports():
        sports = Sport.query.all()
        sport_types = [(a.id, a.name) for a in sports]

        return sport_types


# Defines tabele for activities for date base
class Activities(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    activity_type_id = db.Column(db.Integer, db.ForeignKey('sport.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    distance = db.Column(db.Float, nullable=False)
    time = db.Column(db.Integer, nullable=False, default=0)
    strava_id = db.Column(db.BigInteger)
    added_on = db.Column(db.DateTime, default = dt.datetime.now())

    def add_to_db(self, activity_form):

        current_app.logger.info(f"User {current_user.id} submited activity form")

        time_in_seconds = (activity_form.time.data - dt.datetime(1900,1,1,0,0,0)).total_seconds()

        newActivity = Activities(date = activity_form.date.data,
                            activity_type_id = activity_form.activity.data,
                            distance = activity_form.distance.data,
                            time = time_in_seconds,
                            user_id = current_user.id)

        try:
    
            db.session.add(newActivity)
            db.session.commit()

            current_app.logger.info(f"User {current_user.id} added activity {newActivity.id}")
            return 'Poprawnie dodano nową aktywność', 'success', 'activity.add_activity'

        except:
            
            current_app.logger.exception(f"User {current_user.id} failed to add activity")
            return 'Aktywność NIE DODANA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem', 'danger', 'activity.add_activity'


    def modify(self, activity_form):

        current_app.logger.info(f"User {current_user.id} submited modify activity form")

        time_in_seconds = (activity_form.time.data - dt.datetime(1900,1,1,0,0,0)).total_seconds()
        self.date = activity_form.date.data
        self.activity_type_id = activity_form.activity.data
        self.distance = activity_form.distance.data
        self.time = time_in_seconds

        try:
            if self.user_id == current_user.id :
                db.session.commit()
                current_app.logger.info(f"User {current_user.id} modified activity {self.id}")

                return 'Poprawnie zmodyfikowano aktywność', 'success', 'activity.my_activities'

            else:
                current_app.logger.warning(f"User {current_user.id} tries to modify not own activity {self.id}")
                return "Możesz edytować tylko swoje aktywności!", 'danger', 'activity.my_activities'

        except:
            current_app.logger.exception(f"User {current_user.id} failed to add activity")

            return 'Aktywność NIE EDYTOWANA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem', 'danger', 'activity.my_activities'


    def delete(self):

        current_app.logger.info(f"User {current_user.id} tries to delete activity {self.id}")

        deleted_activity_type = self.activity_type
        activity_id = self.id

        try:
            if self.user_id == current_user.id :
                db.session.delete(self)
                db.session.commit()
                current_app.logger.info(f"User {current_user.id} deleted activity {activity_id}")
                return "Aktywność ({}) została usunięta z bazy danych".format(deleted_activity_type), 'success', 'activity.my_activities'

            else:
                current_app.logger.warning(f"User {current_user.id} tries to delete not own activity {self.id}")
                return "Możesz usuwać tylko swoje aktywności!", 'danger', 'activity.my_activities'

        except:
            
            current_app.logger.exception(f"User {current_user.id} failed to delete activity {self.id}")
            return 'Aktywność NIE ZOSTAŁA USUNIĘTA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem', 'danger', 'activity.my_activities'



    @classmethod
    def added_in_last_days(cls, days):
        inserts = cls.query.filter(cls.added_on < dt.date.today()).filter(cls.added_on > dt.date.today() - dt.timedelta(days=days)).all()
        return len(inserts)




