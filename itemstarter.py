from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Item, Base, User
engine = create_engine('sqlite:///items.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

session = DBSession()

#Create User1
User1= User(name = "Gimme Money", email="Gimmethemgreens@gmail.com",
            picture = "http://nickleroy.com/wp-content/uploads/2011/09/sales.jpg")

session.add(User1)
session.commit()


# create First Item
Item1 = Item(user_id = 1, title = "Semi Ok Computer for Sale",
             itemPicture = "http://www.interactivesys.net/skins/interactivesys/images/tab_css.jpg",
             price = "300.00", 
             description = "Built this computer a month ago, need money for something else",
             itemtype="Computer", contactinfo = "Gimmethemgreens@gmail.com", location = "New Jersey",)

session.add(Item1)
session.commit()

# create Second Item
Item2 = Item(user_id = 1, title = "Like New Car for sale!",
             itemPicture = "http://sellmyjunkcarsterlingheights.com/wp-content/uploads/2013/03/old-cluncker-1024x688.jpg",
             price = "10,000",
             description = "Great Car for first time Learners!",itemtype="Car", contactinfo = "Gimmethemgreens@gmail.com",
             location = "New Jersey", )

session.add(Item2)
session.commit()

# create Third Item
Item3 = Item(user_id = 1, title = "Gym Equiptment for Sale!",
             itemPicture = "http://www.ilovemsmd.com/wp-content/uploads/2015/10/Home-exercise-equipment-825x510.jpg",
             price = "120",
             description = "If you want to get shredded here is the perfect tool for the job!",
             itemtype="Excerise Equiptment", contactinfo = "Gimmethemgreens@gmail.com",
             location = "New Jersey")

session.add(Item3)
session.commit()

print "added items!"