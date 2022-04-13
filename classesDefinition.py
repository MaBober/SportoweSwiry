#from datetime import datetime
import datetime
from email.policy import default


from sqlalchemy import Integer
from start import db
from flask_wtf import FlaskForm
from wtforms.fields import StringField, EmailField, PasswordField, BooleanField, DecimalField, DateField, IntegerField, SelectField, DateTimeField, SubmitField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError, NumberRange, InputRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired

from flask_login import UserMixin


import hashlib
import binascii

from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

import os

class User(db.Model, UserMixin):
    id = db.Column(db.String(50), unique=True, nullable=False , primary_key=True)
    name = db.Column(db.String(50))
    lastName = db.Column(db.String(50))
    mail = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    isAdmin = db.Column(db.Boolean)
    avatar = db.Column(db.LargeBinary)
    confirmed = db.Column(db.Boolean, default=False)

    events = db.relationship('Participation', backref='User', lazy='dynamic')
    activities = db.relationship('Activities', backref='User', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % self.id

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

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'resetPassword': self.id}).decode('utf-8')
    
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def avatarCheck(self, path):
        filename=self.id+'.jpg'
        path=os.path.join(path, filename)
        return os.path.isfile(path)

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('resetPassword'))
        if user is None:
            return False

        user.password = new_password
        
        #Hash of password       
        user.password=user.hash_password()

        db.session.add(user)
        return True

    


#Definition class for User - WTF-FlaskForm
class UserForm(FlaskForm):

    def ValidateMailisExist(form, field):
        tempMail = User.query.filter(User.mail==field.data).first()
        if tempMail:
            raise ValidationError("Ten adres email jest już w użyciu")

    def ValidateUserNameisExist(form, field):
        tempUserName = User.query.filter(User.id==field.data).first()
        if tempUserName:
            raise ValidationError("Ten Login jest już w użyciu")
        
    def ValidatePassword(form, field):
        if field.data!=form.password.data:
            raise ValidationError("Wpisane hasła muszą być identyczne")


    name=StringField("Imię", validators=[DataRequired("Pole nie może być puste")])
    lastName=StringField("Nazwisko", validators=[DataRequired("Pole nie może być puste")])
    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie"), ValidateMailisExist])
    id=StringField("Login", validators=[DataRequired("Pole nie może być puste"), ValidateUserNameisExist])
    password=PasswordField("Hasło", validators=[DataRequired("Pole nie może być puste"), Length(min=8, message="Hasło nie może być krótsze niż 8 znaków")])
    verifyPassword=PasswordField("Potwierdź hasło", validators=[DataRequired("Pole nie może być puste"), ValidatePassword])
    isAdmin=BooleanField("Admin", default=False)
    avatar=BooleanField("Avatar", default=False)


class VerifyEmailForm(FlaskForm):

    def ValidateMailisExist(form, field):
            tempMail = User.query.filter(User.mail==field.data).first()
            if not tempMail:
                raise ValidationError("Tego adresu email nie ma w naszej bazie danych")

    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie"), ValidateMailisExist])


class NewPasswordForm(FlaskForm):

    def ValidatePasswordIsCorrect(form, field):
        tempUser = User.query.filter(User.id==form.userName.data).first()
        currentPassword=tempUser.password

        verify=User.verify_password(currentPassword, field.data)

        if not verify:
            raise ValidationError("Podaj poprawne aktulane hasło")

    def ValidatePassword(form, field):
        if field.data!=form.newPassword.data:
            raise ValidationError("Wpisane nowe hasła muszą być identyczne")


    id=StringField("Login")
    oldPassword=PasswordField("Obecne hasło", validators=[DataRequired("Pole nie może być puste"), ValidatePasswordIsCorrect])
    newPassword=PasswordField("Nowe hasło", validators=[DataRequired("Pole nie może być puste"), Length(min=8, message="Hasło nie może być krótsze niż 8 znaków")])
    verifyNewPassword=PasswordField("Potwierdź nowe hasło", validators=[DataRequired("Pole nie może być puste"), Length(min=8, message="Hasło nie może być krótsze niż 8 znaków"), ValidatePassword])

#Definition class for LOGIN function
class LoginForm(FlaskForm):
    name=StringField("Login")
    password=PasswordField("Hasło")
    remember=BooleanField("Zapamiętaj mnie")


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


class EventForm(FlaskForm):

    name = StringField("Nazwa")

    start = DateField("Data rozpoczęcia")
    length = IntegerField("Długość w tygodniach", validators=[NumberRange(min=0, max=15, message="Podaj proszę liczbę nie ujemną!")], default=10)

    #adminID = IntegerField("ID administratora", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1)
    adminID = SelectField("Administrator wyzwania", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1, choices=[])

    isPrivate =BooleanField("Wydarzenie prywatne")
    isSecret = BooleanField("Wydarenie ukryte")
    status = SelectField("Status wyzwania", validators=[NumberRange(min=0, message="Wybierz pozycję z listy!")], default=1, choices=[])

    #coefficientsTable_id = IntegerField("ID tablicy ze wspołczynnikami", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1)
    coefficientsSetName = SelectField("ID tablicy ze wspołczynnikami", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1, choices=[])

class CoeficientsForm(FlaskForm):

    setName = StringField("Nazwa zestawu współczynników", validators=[DataRequired("Pole nie może być puste")])
    activityName = StringField("Nazwa aktywności", validators=[DataRequired("Pole nie może być puste")])
    constant = BooleanField("Stała wartość?", default=False)
    value = DecimalField("Współczynnik", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1)
    
class NewCoeficientsSetForm(FlaskForm):

    setName = StringField("Nazwa zestawu współczynników", validators=[DataRequired("Pole nie może być puste")])

class DistancesForm(FlaskForm):

    w1 = DecimalField("Tydzień 1", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w2 = DecimalField("Tydzień 2", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w3 = DecimalField("Tydzień 3", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w4 = DecimalField("Tydzień 4", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w5 = DecimalField("Tydzień 5", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w6 = DecimalField("Tydzień 6", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w7 = DecimalField("Tydzień 7", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w8 = DecimalField("Tydzień 8", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w9 = DecimalField("Tydzień 9", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w10 = DecimalField("Tydzień 10", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w11 = DecimalField("Tydzień 11", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w12 = DecimalField("Tydzień 12", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w13 = DecimalField("Tydzień 13", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w14 = DecimalField("Tydzień 14", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w15 = DecimalField("Tydzień 15", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)


# Defines tabele for activities for date base
class Activities(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    week = db.Column(db.Integer, default=0) 
    activity = db.Column(db.String(50), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    time = db.Column(db.Time)
    userName = db.Column(db.String(50), db.ForeignKey(User.id))

# Defines form for activities
class ActivityForm(FlaskForm):

    def ValidateFutureDate (form, field):
        today=datetime.date.today()
        if field.data>today:
            raise ValidationError("Nie możesz podać daty z przyszłości")

    date = DateField("Data aktywności", validators=[InputRequired("Musisz podać date"), ValidateFutureDate], default=datetime.date.today())
    activity = SelectField("Rodzaj aktywności", default=1, choices=[])
    distance = DecimalField("Dystans", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    time = DateTimeField("Czas", format='%H:%M:%S', default=datetime.time())


class UploadAvatarForm(FlaskForm):
    image = FileField('Wgraj zdjęcie (<=3MB)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Zdjęcie może być wyłącznie w formacie .jpg lub .png')])

class MessageForm(FlaskForm):
    name=StringField("Imię", validators=[DataRequired("Pole nie może być puste")])
    lastName=StringField("Nazwisko", validators=[DataRequired("Pole nie może być puste")])
    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie")])
    subject=StringField("Temat", validators=[DataRequired("Pole nie może być puste")])
    message = TextAreaField("Wiadomość", validators=[DataRequired("Pole nie może być puste")])
  