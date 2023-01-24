
from start import app, db
from flask_login import current_user
from flask import current_app

from event.classes import Event

import datetime



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


    @staticmethod
    def prepare_list_of_choices_for_admin():

        all_users = [('Wszyscy','Wszyscy')]
        available_list_of_users = MailboxMessage.prepare_list_of_users()
        available_list_of_events = MailboxMessage.crate_available_list_of_events()
    
        available_list_of_choices = all_users + available_list_of_events + available_list_of_users
        return available_list_of_choices


    @staticmethod
    def prepare_list_of_users():
        #Creating list of users

        from user.classes import User

        list_of_users=User.query.filter(User.name!="Konto").filter(User.last_name!="Usunięte").all()
        list_of_users_mails = [(a.mail) for a in list_of_users]
        list_of_users_names = [(a.name) for a in list_of_users]
        list_of_users_last_names = [(a.last_name) for a in list_of_users]

        temp_tuple_name_list=list(zip(list_of_users_names,list_of_users_last_names))
        list_of_users_full_names = []

        for name, last_name in temp_tuple_name_list:
            full_name=name+" "+last_name
            list_of_users_full_names.append(full_name)

        # (mails, name & last name) 
        return list(zip(list_of_users_mails, list_of_users_full_names))


    @staticmethod
    def crate_available_list_of_events():
        # Creating list of events
        list_of_events=Event.query.all()
        list_of_events_name_key = []
        list_of_events_name_value = []

        for event in list_of_events:
            key = event.name + ", ID:" + str(event.id)
            value = "Uczestnicy wyzwania: " + event.name
            list_of_events_name_key.append(key)
            list_of_events_name_value.append(value)

        return list(zip(list_of_events_name_key, list_of_events_name_value))


    @staticmethod
    def prepare_list_of_choices_for_normal_user():
        admin_user=MailboxMessage.prepare_list_of_admins()
        current_user_events=MailboxMessage.prepare_list_of_current_user_events()
        current_user_events_single_users=MailboxMessage.prepare_list_of_current_user_events_single_users()
        available_list_of_choices=admin_user+current_user_events+current_user_events_single_users
        return available_list_of_choices



    @staticmethod
    def prepare_list_of_admins():

        from user.classes import User
        
        list_of_admins=User.query.filter(User.is_admin==True).all()

        list_of_admins_mails = [(a.mail) for a in list_of_admins]
        list_of_admins_names = [(a.name) for a in list_of_admins]
        list_of_admins_last_names = [(a.last_name) for a in list_of_admins]

        temp_tuple_name_list=list(zip(list_of_admins_names,list_of_admins_last_names))
        list_of_admins_full_names = []

        for name, last_name in temp_tuple_name_list:
            full_name=name+" "+last_name
            list_of_admins_full_names.append(full_name)

        return list(zip(list_of_admins_mails, list_of_admins_full_names))


    @staticmethod
    def prepare_list_of_current_user_events():
        list_of_events=Event.query.all()
        list_of_real_events=[]

        for event in list_of_events:
            for participant in event.participants:
                if participant.user_id==current_user.id:
                    list_of_real_events.append(event.name)
                    break

        list_of_events_name_key = []
        list_of_events_name_value = []

        for event in list_of_real_events:
            single_event=Event.query.filter(Event.name==event).first()
            key = single_event.name + ", ID:" + str(single_event.id)
            value = "Uczestnicy wyzwania: " + single_event.name
            list_of_events_name_key.append(key)
            list_of_events_name_value.append(value)
        
        return list(zip(list_of_events_name_key, list_of_events_name_value))


    @staticmethod
    def prepare_list_of_current_user_events_single_users():

        from user.classes import User

        list_of_events=Event.query.all()
        list_of_real_events=[]

        for event in list_of_events:
            for participant in event.participants:
                if participant.user_id==current_user.id:
                    list_of_real_events.append(event.name)
                    break

        list_of_admins=MailboxMessage.prepare_list_of_admins()
        list_of_mails = []
        list_of_full_names = []

        try:

            for single_event in list_of_real_events:
                event=Event.query.filter(Event.name==single_event).first()
                for participant in event.participants:
                    receiver_user=User.query.filter(User.id==participant.user_id).first()
                    receiver_mail=receiver_user.mail
                    receiver_name=receiver_user.name
                    receiver_last_name=receiver_user.last_name
                    receiver_full_name=receiver_name + " " + receiver_last_name
                    if receiver_mail is not current_user.mail and not receiver_mail in list_of_mails and receiver_full_name != "Konto Usunięte":
                        for admin_mail in list_of_admins:
                            if receiver_mail in admin_mail[0]:
                                 break
                        else:
                            list_of_mails.append(receiver_mail)
                            list_of_full_names.append(receiver_full_name)
                    

        except:
            current_app.logger.exception(f"Somethink went wrong!")
            
        return list(zip(list_of_mails, list_of_full_names))


    @staticmethod  
    def save_message_in_db(form):
        try:
            sender_full_name=MailboxMessage.set_sender_full_name()
            receiver_full_name=MailboxMessage.set_receiver_full_name(form)

            new_message = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, sender_name=sender_full_name, receiver = form.receiver_email.data, receiver_name = receiver_full_name, subject = form.subject.data, message = form.message.data, send_by_app = form.send_by_app.data, send_by_email= form.send_by_email.data, message_readed=False, multiple_message=False )
            db.session.add(new_message)
            db.session.commit()
            new_message = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, sender_name=sender_full_name, receiver = form.receiver_email.data, receiver_name = receiver_full_name, subject = form.subject.data, message = form.message.data, send_by_app = form.send_by_app.data, send_by_email= form.send_by_email.data, message_readed=False, multiple_message=True )
            db.session.add(new_message)
            db.session.commit()
            app.logger.info(f"User {current_user.id} sent message to {receiver_full_name}.")
        except:
            current_app.logger.exception(f"User {current_user.id} failed to send message to {receiver_full_name}.")


    @staticmethod
    def set_sender_full_name():
        sender_name=current_user.name
        sender_last_name=current_user.last_name
        return sender_name + " " + sender_last_name


    @staticmethod
    def set_receiver_full_name(form):

        from user.classes import User

        receiver_user=User.query.filter(User.mail==form.receiver_email.data).first()
        receiver_name=receiver_user.name
        receiver_last_name=receiver_user.last_name
        return receiver_name + " " + receiver_last_name

    @staticmethod
    def save_message_in_db_for_event(form):

        from user.classes import User

        try:
            sender_full_name=MailboxMessage.set_sender_full_name()
            (event_name, id) = (form.receiver_email.data).split(', ID:')
            new_message = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, sender_name=sender_full_name, receiver = form.receiver_email.data, receiver_name = event_name, subject = form.subject.data, message = form.message.data, send_by_app = form.send_by_app.data, send_by_email= form.send_by_email.data, message_readed=False, multiple_message=False )
            db.session.add(new_message)
            db.session.commit()

            event=Event.query.filter(Event.name==event_name).first()
            for participant in event.participants:
                receiver_user=User.query.filter(User.id==participant.user_id).first()
                
                if receiver_user.mail!=current_user.mail:
                    receiver_mail=receiver_user.mail
                    receiver_name=receiver_user.name
                    receiver_last_name=receiver_user.last_name
                    receiver_full_name=receiver_name + " " + receiver_last_name
                    new_message = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, sender_name=sender_full_name, receiver = receiver_mail, receiver_name = receiver_full_name, subject = form.subject.data, message = form.message.data, send_by_app = form.send_by_app.data, send_by_email= form.send_by_email.data, message_readed=False, multiple_message=True )
                    db.session.add(new_message)
                    db.session.commit()
                    app.logger.info(f"User {current_user.id} sent message to {event_name} participants.")
        except:
            current_app.logger.exception(f"User {current_user.id} failed to send message to {event_name} participants.")


    @staticmethod
    def save_message_in_db_for_all(form):

        from user.classes import User
        try:
            sender_full_name=MailboxMessage.set_sender_full_name()
            new_message = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, sender_name=sender_full_name, receiver = form.receiver_email.data, receiver_name = form.receiver_email.data, subject = form.subject.data, message = form.message.data, send_by_app = form.send_by_app.data, send_by_email= form.send_by_email.data, message_readed=False, multiple_message=False )
            db.session.add(new_message)
            db.session.commit()

            users=User.query.filter(User.mail!=current_user.mail).all()
            for user in users:
                receiver_mail=user.mail
                receiver_name=user.name
                receiver_last_name=user.last_name
                receiver_full_name=receiver_name + " " + receiver_last_name
                new_message = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, sender_name=sender_full_name, receiver = receiver_mail, receiver_name = receiver_full_name, subject = form.subject.data, message = form.message.data, send_by_app = form.send_by_app.data, send_by_email= form.send_by_email.data, message_readed=False, multiple_message=True )
                db.session.add(new_message)
                db.session.commit()

            app.logger.info(f"User {current_user.id} sent message to all users.")
        except:
            current_app.logger.exception(f"User {current_user.id} failed to send message to all users.")

    @staticmethod
    def delete_messages_from_db(messages_to_delete):
        try:
            for message_id in messages_to_delete:
                message_to_delete=MailboxMessage.query.filter(MailboxMessage.id == message_id).first()
                db.session.delete(message_to_delete)
                db.session.commit()
            return None
        except:
            current_app.logger.exception(f"User failed to delete message from mailbox.")