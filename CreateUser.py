def CreateUser():
    from app import db, User

    try:
        newUser=User(name='Jan', lastName='Kowalski', mail='jan.kowalski@wp.pl', 
                    userName='JKowalski', password='123', isAdmin=False)
        #adding admins to datebase 
        db.session.add(newUser)
        db.session.commit()
    except Exception as e:
        print ("Błąd: {}".format(e))

