from start import db

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



