from user.classes import User
from start import db

def checkIfIsAdmin():
    #checking if admin already exist
    admin = User.query.filter(User.isAdmin==True).first()
    if admin:
        print ("Jest juz admin")
    else: 
        print ("NIE ma admina, zaraz go stworze")
        admin=User(name='Łukasz', lastName='Bartsch', mail='lukasz.bartsch@gmail.com', 
                    id='LukBartsch', password='123', isAdmin=True, avatar=False)
        admin2=User(name='Marcin', lastName='Bober', mail='marcin@bober.pl', 
                id='MaBober', password='123', isAdmin=True, avatar=False)

        #Password hashing
        admin.password=admin.hash_password()
        admin2.password=admin2.hash_password()

        #adding admins to datebase 
        db.session.add(admin)
        db.session.add(admin2)
        db.session.commit()
    return None