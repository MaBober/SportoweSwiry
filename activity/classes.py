from start import db
import datetime as dt
from flask import current_app
from flask_login import current_user

class Sport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    default_coefficient = db.Column(db.Float, nullable = False, default = 0)
    default_is_constant = db.Column(db.Boolean, nullable = False, default = False)
    category = db.Column(db.String(50), nullable = False, default = 'Other')

    activities = db.relationship('Activities', backref='activity_type', lazy='dynamic')
    events = db.relationship('CoefficientsList', backref='sport', lazy='dynamic')

    def __repr__(self):
        return self.name

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

            return 'Poprawnie dodano nową aktywność', 'success'

        except:
            current_app.logger.exception(f"User {current_user.id} failed to add activity")

            return 'Aktywność NIE DODANA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem', 'danger'


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





