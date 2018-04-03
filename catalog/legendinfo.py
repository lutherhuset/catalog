from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Activity, Base, Legend, User
 
engine = create_engine('sqlite:///gr8est.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

#User List
user1 = User(name= "Luther Huset", email = "lutherhuset@gmail.com")



#Legends for Hockey
activity1 = Activity(name = "Hockey", user = user1)

session.add(activity1)
session.commit()


legend1 = Legend(name = "Anze Kopitar", description = "Center for Los Angeles Kings", salary = "$15,000,000", stats = "Goals: 242, Assists: 261", activity = activity1, user = user1)

session.add(legend1)
session.commit()

legend2 = Legend(name = "Wayne Gretzky", description = "Center for Edmonton Oilers", salary = "$3,000,000", stats = "Goals: 321, Assists: 1,406", activity = activity1, user = user1)

session.add(legend2)
session.commit()

legend3 = Legend(name = "Alexander Ovechkin", description = "Left Wing for the Washington Capitals", salary = "$19,000,000", stats = "Goals: 301, Assists: 167", activity = activity1, user = user1)

session.add(legend3)
session.commit()





#Legends for Soccer
activity2 = Activity(name = "Soccer", user = user1)

session.add(activity2)
session.commit()


legend1 = Legend(name = "Pele", description = "Forward, Midfielder", salary = "$1,000,000", stats = "Goals: 201, Assists: 148", activity = activity2, user = user1)

session.add(legend1)
session.commit()

legend2 = Legend(name = "Lionel Messi", description = "Forward for Barcelona FC", salary = "$25,000,000", stats = "Goals: 315, Assists: 612", activity = activity2, user = user1)

session.add(legend2)
session.commit()

legend3 = Legend(name = "Zlatan Ibrahimović", description = "Forward for LA Galaxy", salary = "$11,500,000", stats = "Goals: 203, Assists: 67", activity = activity2, user = user1)

session.add(legend3)
session.commit()




#Legends for Golf
activity1 = Activity(name = "Golf", user = user1)

session.add(activity1)
session.commit()


legend1 = Legend(name = "Tiger Woods", description = "Dominated golf in the late 90's and early 2000's", salary = "$11,000,000", stats = "79 PGA Tour wins", activity = activity1, user = user1)

session.add(legend1)
session.commit()

legend2 = Legend(name = "Sam Snead", description = "Dominated golf in the 40's, 50's and 60's", salary = "$6,750,000", stats = "A record 82 PGA Tour wins", activity = activity1, user = user1)

session.add(legend2)
session.commit()

legend3 = Legend(name = "Arnold Palmer", description = "The golfer with the best lemonade to iced tea ratio", salary = "$12,000,000", stats = "60 PGA Tour wins", activity = activity1, user = user1)

session.add(legend3)
session.commit()




#Legends for Football
activity1 = Activity(name = "Football", user = user1)

session.add(activity1)
session.commit()


legend1 = Legend(name = "Jim Brown", description = "Running Back, Cleveland Browns, 1957-65", salary = "$1,500,000", stats = "12,312 yards", activity = activity1, user = user1)

session.add(legend1)
session.commit()

legend2 = Legend(name = "Lawrence Taylor", description = "Linebacker, New York Giants, 1981-93", salary = "$12,250,000", stats = "132½ sacks", activity = activity1, user = user1)

session.add(legend2)
session.commit()

legend3 = Legend(name = "Joe Montana", description = "Quarterback, San Francisco 49ers 1979-92, Kansas City Chiefs 1993-94", salary = "$16,000,000", stats = "40,551 career passing yards", activity = activity1, user = user1)

session.add(legend3)
session.commit()





print ("added legends!")

