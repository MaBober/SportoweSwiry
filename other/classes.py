
from datetime import date
from start import db

class MailboxMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date,nullable=False)
    sender = db.Column(db.String(50),nullable=False)
    sender_name = db.Column(db.String(50))
    receiver = db.Column(db.String(500),nullable=False)
    receiver_name = db.Column(db.String(50))
    subject = db.Column(db.String(50))
    message = db.Column(db.String(500))
    send_by_app = db.Column(db.Boolean, nullable=False)
    send_by_email = db.Column(db.Boolean, nullable=False)
    message_readed = db.Column(db.Boolean, nullable=False)
    multiple_message = db.Column(db.Boolean, nullable=False)