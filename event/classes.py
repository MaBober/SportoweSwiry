from start import db
from user.classes import User


class CoefficientsList(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    setName = db.Column(db.String(50))

    activityName = db.Column(db.String(50))
    value = db.Column(db.Float)
    constant = db.Column(db.Boolean)

    def __repr__(self):
        return self.setName

class DistancesTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_ID = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer)
    value = db.Column(db.Float)

    
#Defines event table

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),nullable=False)
    start = db.Column(db.Date,nullable=False)
    lengthWeeks = db.Column(db.Integer,nullable=False)
    end = db.Column(db.Date)
    adminID = db.Column(db.String(50), db.ForeignKey(User.id)) 
    status = db.Column(db.String(50), nullable=False)
    isPrivate = db.Column(db.Boolean, nullable=False)
    isSecret = db.Column(db.Boolean, nullable=False)
    password = db.Column(db.String(50))
    maxUserAmount = db.Column(db.Integer,nullable=False)

    coefficientsSetName = db.Column(db.String(50))
    
    participants = db.relationship('Participation', backref='Events', lazy='dynamic')

    def __repr__(self):
        return self.name

        
# Defines tabele, which connect users with events
class Participation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), db.ForeignKey(User.id))
    event_id = db.Column(db.Integer, db.ForeignKey(Event.id))

    def __repr__(self):
        eventName = Event.query.filter(Event.id==self.event_id).first()
        return "Użytkownik:{} bierze udział w Wydarzeniu: {}" .format(self.user_name, eventName)

def get_event():
    return Event.query

def getIDCoefficient():
    return CoefficientsList.query