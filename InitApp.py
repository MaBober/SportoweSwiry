def InitApp():

    from main import db, User
    
    #creating datebase if not exist
    db.create_all()

    #checking if admin already exist
    admin = User.query.filter(User.isAdmin==True).first()
    if admin:
        print ("jest juz admin")
    else: 
        print ("NIE ma admina, zaraz go stworze")
        admin=User(name='Łukasz', lastName='Bartsch', mail='lukasz.bartsch@gmail.com', 
                    userName='LukBartsch', password='123', isAdmin=True)
        admin2=User(name='Marcin', lastName='Bober', mail='marcin@bober.pl', 
                userName='MaBober', password='123', isAdmin=True)
        #adding admins to datebase 
        db.session.add(admin)
        db.session.add(admin2)
        db.session.commit()

    return User

