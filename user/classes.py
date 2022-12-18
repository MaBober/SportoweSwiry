import pandas as pd
import pygal

from start import db, app
from flask_login import UserMixin, current_user, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError
from other.functions import send_email
import hashlib
import binascii
from flask import current_app, redirect, url_for, render_template
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
import datetime as dt

from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from other.classes import MailboxMessage
from event.classes import Event
from .functions import password_generator



class User(db.Model, UserMixin):

    id = db.Column(db.String(50), unique=True, nullable=False , primary_key=True)
    name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    mail = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    is_admin = db.Column(db.Boolean)
    confirmed = db.Column(db.Boolean, default=False)
    added_on = db.Column(db.DateTime, default = dt.datetime.now())

    is_added_by_google = db.Column(db.Boolean, default=False)
    is_added_by_fb = db.Column(db.Boolean, default=False)

    event_admin = db.relationship('Event', backref='admin', lazy='dynamic')
    events = db.relationship('Participation', backref='user', lazy='dynamic')
    activities = db.relationship('Activities', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % self.id

    @classmethod
    def create_standard_account(cls, form):

            current_app.logger.info(f"New user tries to create account")
            #Rewriting data from the form
            new_user = cls(
                name = form.name.data,
                last_name = form.lastName.data,
                mail = form.mail.data, 
                id = form.name.data[0:3]+form.lastName.data[0:3],
                password = form.password.data)

            #Generatin new user ID
            new_user.id = new_user.generate_ID()
            new_user.id = new_user.removeAccents()

            #Hash of password       
            new_user.password=new_user.hash_password()

            try:
                #adding user to datebase 
                db.session.add(new_user)
                db.session.commit()

                new_user.generate_confirmation_token()
                login_user(new_user)

                message = "Nowe konto zostało utworzone, a na Twój adres e-mail wysłano prośbę o potwierdzenie konta."
                current_app.logger.info(f"New user ({new_user.id}) created account!")
                return message, 'success', redirect(url_for('other.hello'))

            except:
                message = "NIE UTWORZONO KONTA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
                current_app.logger.exception(f"User failed to create account!")
                return message, 'danger', redirect(url_for('other.hello'))


    @classmethod
    def create_account_from_social_media(cls, first_name, last_name, email, media):

        current_app.logger.info(f"New user generate callback from {media} to create new account")
        
        
        new_user = cls(name = first_name,
                      last_name = last_name,
                      mail=  email,
                      id = first_name[0:3]+last_name[0:3],
                      password = password_generator(),
                      is_admin = False,
                      confirmed = True,
                      is_added_by_google = False,
                      is_added_by_fb = False)

        if media == "Google":
            new_user.is_added_by_google = True
        
        elif media == 'Facebook':
            new_user.is_added_by_fb = True

        #Generatin new user ID
        new_user.id = new_user.generate_ID()
        new_user.id = new_user.removeAccents()

        #Hash of password       
        new_user.password=new_user.hash_password()

        try:
            #adding admins to datebase 
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)

            message = "Nowe konto zostało utworzone!"
            current_app.logger.info(f"New user ({new_user.id}) created account with {media}!")
            return message, 'success', redirect(url_for('other.hello'))

        except:
            message = "NIE UTWORZONO KONTA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
            current_app.logger.exception(f"User failed to create account!")
            return message, 'danger', redirect(url_for('other.hello'))



    def modify(self, user_form):

        current_app.logger.info(f"User ({self.id}) tries to modify account!")

        try:
            self.name = user_form.name.data
            self.last_name = user_form.lastName.data
            db.session.commit()

            message = 'Dane zmienione poprawnie'
            current_app.logger.info(f"User ({self.id}) modified account!")
            return message, 'success', redirect(url_for('user.settings'))

        except:
            message = "NIE ZMIENIONO DANYCH! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
            current_app.logger.exception(f"User failed to modify account!")
            return message, 'danger', redirect(url_for('user.settings'))

    def delete(self):

        account_to_delete = self.id
        current_app.logger.info(f"User ({current_user.id}) tries to delete account {self.id}!")

        if not current_user.is_admin:
            logout_user()
        
        if self.is_admin:
            message = "Nie można usunąć konta administratora!"
            current_app.logger.warning(f"User ({current_user.id}) tried to delete admin account {self.id}!")
            return message, 'danger', redirect(url_for('user.settings'))

        try:
            db.session.delete(self)
            db.session.commit()
            message = "Użytkownik {} {} został usunięty z bazy danych".format(self.name, self.last_name)
            current_app.logger.info(f"User ({account_to_delete}) deleted account!")
            return message, 'success', redirect(url_for('other.hello'))

        except (SQLAlchemyError, AssertionError) as e:
            db.session.rollback()

            self.name = "Konto"
            self.last_name = 'Usunięte'
            self.mail = password_generator()
            db.session.commit()

            message = f"Konto usunięte!"
            current_app.logger.info(f"User ({account_to_delete}) account was anonimzed!")
            return message, 'success', redirect(url_for('other.hello'))


        except Exception as e:
            message = "NIE USUNIĘTO KONTA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
            current_app.logger.exception(f"User ({current_user.id}) failed to delete account {account_to_delete}!")
            return message, 'danger', redirect(url_for('user.settings'))


    
    def change_password(self, password_form):

        current_app.logger.info(f"User ({self.id}) tries to modify passowrd!")

        try:
            self.password = password_form.newPassword.data
            self.password = self.hash_password()
            db.session.commit()
            current_app.logger.info(f"User ({self.id}) modified password!")
            message = "Hasło zmienione poprawnie!"

            return message, "success", redirect(url_for('other.hello'))
        
        except:
            message = "NIE ZMIENIONO HASŁA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
            current_app.logger.exception(f"User failed to modify password!")
            return message, 'danger', redirect(url_for('user.password_change'))

    def standard_login(self, login_form = None, social_media_login = False, remember=True):

        from user.functions import check_next_url
        if social_media_login or self.verify_password(login_form.password.data):

            try:
                login_user(self, remember)
                check_next_url()
                message = "Jesteś zalogowany jako: {} {}".format(current_user.name, current_user.last_name)
                current_app.logger.info(f"User ({self.id}) loged in!")
                return message, "success", redirect(url_for('user.dashboard'))
            
            except:
                message = "NIE ZALOGOWOANO! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
                current_app.logger.exception(f"User failed to log in!")
                return message, 'danger', redirect(url_for('other.hello'))

        else:
            message = "Nie udało się zalogować. Podaj pawidłowe hasło!"
            current_app.logger.info(f"User ({self.id}) tried to login with wrong password!")
            return message, 'danger', redirect(url_for('user.login'))


    def change_message_status(self,id):
        messageFromInBox=MailboxMessage.query.filter(MailboxMessage.id == id).first()
        messageFromInBox.messageReaded = 1
        db.session.commit()
        return None

    def countNotReadedMessages(self):
        notReadedMessages=MailboxMessage.query.filter(MailboxMessage.receiver == self.mail).filter(MailboxMessage.messageReaded == 0).filter(MailboxMessage.multipleMessage == True).all()
        amountOfNotReadedMessages=len(notReadedMessages)
        return amountOfNotReadedMessages


    def removeAccents(self):
        strange='ŮôῡΒძěἊἦëĐᾇόἶἧзвŅῑἼźἓŉἐÿἈΌἢὶЁϋυŕŽŎŃğûλВὦėἜŤŨîᾪĝžἙâᾣÚκὔჯᾏᾢĠфĞὝŲŊŁČῐЙῤŌὭŏყἀхῦЧĎὍОуνἱῺèᾒῘᾘὨШūლἚύсÁóĒἍŷöὄЗὤἥბĔõὅῥŋБщἝξĢюᾫაπჟῸდΓÕűřἅгἰშΨńģὌΥÒᾬÏἴქὀῖὣᾙῶŠὟὁἵÖἕΕῨčᾈķЭτἻůᾕἫжΩᾶŇᾁἣჩαἄἹΖеУŹἃἠᾞåᾄГΠКíōĪὮϊὂᾱიżŦИὙἮὖÛĮἳφᾖἋΎΰῩŚἷРῈĲἁéὃσňİΙῠΚĸὛΪᾝᾯψÄᾭêὠÀღЫĩĈμΆᾌἨÑἑïოĵÃŒŸζჭᾼőΣŻçųøΤΑËņĭῙŘАдὗპŰἤცᾓήἯΐÎეὊὼΘЖᾜὢĚἩħĂыῳὧďТΗἺĬὰὡὬὫÇЩᾧñῢĻᾅÆßшδòÂчῌᾃΉᾑΦÍīМƒÜἒĴἿťᾴĶÊΊȘῃΟúχΔὋŴćŔῴῆЦЮΝΛῪŢὯнῬũãáἽĕᾗნᾳἆᾥйᾡὒსᾎĆрĀüСὕÅýფᾺῲšŵкἎἇὑЛვёἂΏθĘэᾋΧĉᾐĤὐὴιăąäὺÈФĺῇἘſგŜæῼῄĊἏØÉПяწДĿᾮἭĜХῂᾦωთĦлðὩზკίᾂᾆἪпἸиᾠώᾀŪāоÙἉἾρаđἌΞļÔβĖÝᾔĨНŀęᾤÓцЕĽŞὈÞუтΈέıàᾍἛśìŶŬȚĳῧῊᾟάεŖᾨᾉςΡმᾊᾸįᾚὥηᾛġÐὓłγľмþᾹἲἔбċῗჰხοἬŗŐἡὲῷῚΫŭᾩὸùᾷĹēრЯĄὉὪῒᾲΜᾰÌœĥტ'
        ascii_replacements='UoyBdeAieDaoiiZVNiIzeneyAOiiEyyrZONgulVoeETUiOgzEaoUkyjAoGFGYUNLCiIrOOoqaKyCDOOUniOeiIIOSulEySAoEAyooZoibEoornBSEkGYOapzOdGOuraGisPngOYOOIikoioIoSYoiOeEYcAkEtIuiIZOaNaicaaIZEUZaiIaaGPKioIOioaizTIYIyUIifiAYyYSiREIaeosnIIyKkYIIOpAOeoAgYiCmAAINeiojAOYzcAoSZcuoTAEniIRADypUitiiIiIeOoTZIoEIhAYoodTIIIaoOOCSonyKaAsSdoACIaIiFIiMfUeJItaKEISiOuxDOWcRoiTYNLYTONRuaaIeinaaoIoysACRAuSyAypAoswKAayLvEaOtEEAXciHyiiaaayEFliEsgSaOiCAOEPYtDKOIGKiootHLdOzkiaaIPIIooaUaOUAIrAdAKlObEYiINleoOTEKSOTuTEeiaAEsiYUTiyIIaeROAsRmAAiIoiIgDylglMtAieBcihkoIrOieoIYuOouaKerYAOOiaMaIoht'
        translator=str.maketrans(strange,ascii_replacements)
        return self.id.translate(translator)

    def generate_ID(self):

        sufix = 0

        id = self.name[0:3] + self.last_name[0:3] + str(sufix)
        id = self.removeAccents()
        user=User.query.filter(User.id == id).first()

        while user != None:
            sufix +=1
            id = self.name[0:3] + self.last_name[0:3] + str(sufix)
            user=User.query.filter(User.id == id).first()

        return id

    def hash_password(self):
        """Hash a password for storing."""
        # the value generated using os.urandom(60)
        os_urandom_static = b"ID_\x12p:\x8d\xe7&\xcb\xf0=H1\xc1\x16\xac\xe5BX\xd7\xd6j\xe3i\x11\xbe\xaa\x05\xccc\xc2\xe8K\xcf\xf1\xac\x9bFy(\xfbn.`\xe9\xcd\xdd'\xdf`~vm\xae\xf2\x93WD\x04"
        #os_urandom_static = b"ID_\x12p:\x8d\xe7&\xcb\xf0=H1"
        salt = hashlib.sha256(os_urandom_static).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', self.password.encode('utf-8'), salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii') 

    
    def verify_password(self, provided_password):
        """Verify a stored password against one provided by user"""
        salt = self.password[:64]
        stored_password = self.password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'),
        salt.encode('ascii'), 100000)
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        return pwdhash == stored_password


    def generate_confirmation_token(self, expiration=3600, remind = False):

        current_app.logger.info(f"User {self.id} tries to generate confirmation token")
        try:
            s = Serializer(current_app.config['SECRET_KEY'], expiration)
            token = s.dumps({'confirm': self.id}).decode('utf-8')
            send_email(self.mail, 'Potwierdź swoje konto.','confirm', user = self, token = token)

            current_app.logger.info(f"User {self.id} generated confirmation token")
            return token

        except:
            current_app.logger.exception(f"User {self.id} failed to generate confirmation token")


    def generate_reset_token(self, expiration=3600):

        current_app.logger.info(f"User {self.id} tries to generate reset token")
        try:
            s = Serializer(current_app.config['SECRET_KEY'], expiration)
            token = s.dumps({'resetPassword': self.id}).decode('utf-8')
            send_email(self.mail, 'Zresetuj hasło','reset', user = self, token = token)

            current_app.logger.info(f"User {self.id} generated reset token")
            message = f'Na Twój adres e-mail ({self.mail}) wysłaliśmy link do resetowania hasła'
            return message, "success", render_template("verify_email_sent.html", title_prefix = "Resetowanie hasła")

        except:

            current_app.logger.exception(f"User {self.id} failed to generate reset token")
            message = f'NIE UDAŁO SIĘ ZRESETOWAĆ HASŁA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem'
            return message, "danger", redirect(url_for('user.reset'))

    
    def confirm(self, token):

        current_app.logger.info(f"User {self.id }tries to confirm account")
        if self.confirmed:
            message = f"Twoje kotno jest już aktywowane!"
            current_app.logger.warning(f"User {self.id } tries to confirm account. It is already confrimed!")
            return message, "message", redirect(url_for('other.hello'))
        
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))

        except:
            message = 'Link potwierdzający jest nieprawidłowy lub już wygasł'
            current_app.logger.warning(f"User {self.id } tries to confirm account with wrong token!")
            return message, "danger", redirect(url_for('other.hello'))

        if data.get('confirm') != self.id:
            message = 'Link potwierdzający jest nieprawidłowy lub już wygasł'
            current_app.logger.warning(f"User {self.id } tries to confirm account with wrong token!")
            return message, "danger", redirect(url_for('other.hello'))

        try:
            self.confirmed = True
            db.session.add(self)
            db.session.commit()

            message = "Twoje konto zostało potwierdzone. Dzięki!"
            current_app.logger.info(f"User {self.id} confirmed account")
            return message, "success", redirect(url_for('other.hello'))

        except:
            message = "NIE POTWIERDZONO KONTA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
            current_app.logger.exception(f"User {self.id} failed to confirm account")
            return message, "danger", redirect(url_for('other.hello'))


    def upload_avatar(self, file):

        current_app.logger.info(f"User {self.id} tries to upload avatar")
        try:
            avatar = Image.open(file)
            avatar.thumbnail((60,60))

            if avatar.format in ('png','PNG'):
                filename = secure_filename(self.id + '.png')
                avatar = avatar.convert('RGB') #Convert from png to jpg

            filename = secure_filename(self.id + '.jpg')
            avatar.save(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))

            message = "Zdjęcie profilowe zostało poprawnie przesłane na serwer"
            current_app.logger.info(f"User {self.id} uploaded avatar")
            return message, "success", redirect(url_for('user.settings'))

        except UnidentifiedImageError as e:
            message = "Nie poprawny format obrazu!"
            current_app.logger.warning(f"User {self.id} tried to upload wrong picture format.")
            return message, "message", redirect(url_for('user.settings'))

        except:
            message = "NIE WGRANO AVATARA! Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem"
            current_app.logger.exception(f"User {self.id} failed to upload avatar!")
            return message, "danger", redirect(url_for('user.settings'))



    def avatarCheck(self, path):
        filename = self.id+'.jpg'
        path = os.path.join(path, filename)
        return os.path.isfile(path)
        
        
    def give_avatar_path(self):

        avatars_location = os.path.join(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH']))

        if self.avatarCheck(avatars_location):
            avatar_path = '/static/avatars/{}'.format(self.id+'.jpg')
            return avatar_path

        else:
            avatar_path = "/static/pictures/runner_logo.svg"
            return avatar_path

    @staticmethod
    def reset_password(token, new_password):

        current_app.logger.infor(f"User tries to reset password")
        s = Serializer(current_app.config['SECRET_KEY'])

        try:
            data = s.loads(token.encode('utf-8'))

        except:
            message = 'Hasło nie zostało poprawnie zmienione!'
            current_app.logger.warning(f"User didn't reset password")
            return message, 'danger', redirect(url_for('other.hello'))

        user = User.query.get(data.get('resetPassword'))

        if user is None:
            message = 'Hasło nie zostało poprawnie zmienione!'
            current_app.logger.warning(f"User didn't reset password")
            return message, 'danger', redirect(url_for('other.hello'))

        try:
            user.password = new_password      
            user.password = user.hash_password()

            db.session.add(user)
            db.session.commit()

            message = 'Hasło zostało poprawnie zmienione. Możesz się zalogować'
            current_app.logger.info(f"User {user.id} reset password")
            return message, 'success', redirect(url_for('user.login'))

        except:
            message = 'HASŁO NIE ZOSTAŁO ZMIENIONE. Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem'
            current_app.logger.exception(f"User {user.id} failed to reset password")
            return message, 'danger', redirect(url_for('other.hello'))

    
    def rotate_avatar(self, angle):

        current_app.logger.infor(f"User tries to rotate avatar ({angle})")
        try:

            filename = secure_filename(self.id + '.jpg')
            avatar = Image.open(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))
            rotatedAvatar = avatar.rotate(angle, expand = True)
            rotatedAvatar.save(os.path.join(app.root_path, app.config['AVATARS_SAVE_PATH'], filename))

            message = 'Avatar obrócony. Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem'
            current_app.logger.info(f"User {self.id} rotated avatar ({angle})")
            return message, 'danger', redirect(url_for('user.settings'))

        except:
            message = 'AVATAR NIE OBRÓCONY. Jeżeli błąd będzie się powtarzał, skontaktuj się z administratorem'
            current_app.logger.exception(f"User {self.id} failed to rotate avatar ({angle})")
            return message, 'danger', redirect(url_for('user.settings'))


    @property
    def all_events(self):

        from event.classes import Participation, Event

        user_events = Participation.query.filter(Participation.user_id == self.id)
        user_events = pd.read_sql(user_events.statement, db.engine, index_col='event_id')

        user_events_ids = user_events.index.values.tolist()
        user_events = Event.query.filter(Event.id.in_(user_events_ids))

        return user_events


    @property
    def future_events(self):

        from event.classes import Event
        current_events = self.all_events.filter(Event.status == "0").all()

        return current_events

    @property
    def current_events(self):

        from event.classes import Event
        current_events = self.all_events.filter(Event.status != "5").filter(Event.status != "4").filter(Event.status != "0").all()

        return current_events


    @property
    def finished_events(self):

        from event.classes import Event
        finished_events = self.all_events.filter(Event.status.in_(['4','5'])).all()

        return finished_events

    @classmethod
    def all_application_admins(cls):
        admins = cls.query.filter(cls.is_admin == True).all()
        return admins


    @classmethod
    def added_in_last_days(cls, days):
        inserts = cls.query.filter(cls.added_on < dt.date.today()).filter(cls.added_on > dt.date.today() - dt.timedelta(days=days)).all()
        return len(inserts)

    

class DashboardPage:

    user_distance_sum = "---"
    average_time = "---"
    average_distance_for_event = '---'
    beers_recived_in_event = '---'
    

    def __init__(self, requested_event = None) -> None:
        
        self.event = self.define_event_to_present(requested_event)

        if self.event != None:
            summary =  self.event.give_user_overall_summary(current_user.id)

            self.user_distance_sum = summary['user_distance_sum']
            self.average_time = summary['average_time']
            self.average_distance_for_event = summary['average_distance_for_event']

            all_event_activities = self.event.give_all_event_activities(calculated_values = True)
            split_list = self.event.give_overall_weekly_summary(all_event_activities)

            self.event_week_distance =  split_list[self.event.current_week-1].loc['total']['calculated_distance'][current_user.id][0]

            if self.event.status != '0':
                beers_summary = self.event.give_beers_summary(split_list)
                self.beers_recived_in_event = beers_summary['beers_to_recive'][current_user.id]
            else:
                self.beers_recived_in_event = '---'
            
            self.generete_charts()
            self.define_next_previous_events()
        
        else:
            self.user_distance_sum = '---'
            self.average_time = '---'
            self.average_distance_for_event = '---'
            self.event_week_distance = '---'
            self.beers_recived_in_event = '---'


    def define_event_to_present(self, requested_event):

        from event.classes import Event, Participation

        self.user_events = current_user.current_events

        if self.user_events != []:
            if 'event_id' in requested_event:
                try:
                    event_id = int(requested_event['event_id'])
                    event = Event.query.filter(Event.id == event_id).first()

                except:
                    event_id = 0
                    event = self.user_events[0]
            
            else:
                event_id = 0
                event = self.user_events[0]

            return event
        
        else:
            return None


    def generete_charts(self):

        #creating a pie chart
        self.pie_chart = pygal.Pie(inner_radius=.4, width=500, height=400)
        self.pie_chart.title = 'Różnorodność aktywności (w %)'

        #Render a URL adress for chart
        self.pie_chart = self.pie_chart.render_data_uri()
        try:
            if self.event.current_week < self.event.length_weeks:
                self.d1 = self.event.current_week / self.event.length_weeks * 100
                self.d1 = round(self.d1,0)
            
            else:
                self.d1 = 100
        except:
                current_app.logger.exception(f"self.event.current_week < self.event.length_weeks")

        try:

            if self.event_week_distance < self.event.current_week_target:
                self.d2 = self.event_week_distance / self.event.current_week_target * 100
                self.d2 = round(self.d2, 0)
            
            else:
                self.d2=100
        except:
                current_app.logger.exception("self.event_week_distance < self.current_week_target")

        return None


    def define_next_previous_events(self):
        
        active_events_ids = []
        for event in self.user_events:
            active_events_ids.append(event.id)

        ## Defines next / previous event to display
        if active_events_ids.index(self.event.id) == len(active_events_ids)-1:
            self.next_event = active_events_ids[0]
        else:
            self.next_event = active_events_ids[active_events_ids.index(self.event.id) + 1]

        if active_events_ids.index(self.event.id) == 0:   
            self.previous_event = active_events_ids[len(active_events_ids)-1]

        else:
            self.previous_event = active_events_ids[active_events_ids.index(self.event.id) -1]

        return None