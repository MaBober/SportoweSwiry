from start import db
from user.classes import User
from event.classes import Event

def checkIfIsAdmin():
    #checking if admin already exist
    admin = User.query.filter(User.is_admin==True).first()
    if admin:
        print ("Jest juz admin")
    else: 
        print ("NIE ma admina, zaraz go stworze")
        admin=User(name='Łukasz', last_name='Bartsch', mail='lukasz.bartsch@gmail.com', 
                    id='LukBartsch', password='123', is_admin=True)
        admin2=User(name='Marcin', last_name='Bober', mail='marcin@bober.pl', 
                id='MaBober', password='123', is_admin=True)

        #Password hashing
        admin.password=admin.hash_password()
        admin2.password=admin2.hash_password()

        #adding admins to datebase 
        db.session.add(admin)
        db.session.add(admin2)
        db.session.commit()
    return None