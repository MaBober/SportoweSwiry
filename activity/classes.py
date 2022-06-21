#from datetime import datetime

from user.classes import User
from start import db

# Defines tabele for activities for date base
class Activities(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    activity = db.Column(db.String(50), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    time = db.Column(db.Time)
    userName = db.Column(db.String(50), db.ForeignKey(User.id))
    stravaID = db.Column(db.BigInteger)