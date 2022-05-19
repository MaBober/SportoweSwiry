
from datetime import date
from start import db

class mailboxMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date,nullable=False)
    sender = db.Column(db.String(50),nullable=False)
    receiver = db.Column(db.String(500),nullable=False)
    subject = db.Column(db.String(50))
    message = db.Column(db.String(500))
    sendByApp = db.Column(db.Boolean, nullable=False)
    sendByEmail = db.Column(db.Boolean, nullable=False)