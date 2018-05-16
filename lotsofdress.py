from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Shop, Base, DressItem, User

engine = create_engine('sqlite:///shopitems.db')
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


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Menu for burlington
shop1 = Shop(user_id=1, name="Burlington")

session.add(shop1)
session.commit()

menuItem2 = DressItem(user_id=1, name="dress", description="red and pretty",
                     price="$17.50", course="Dresses ", shop=shop1)

session.add(menuItem2)
session.commit()


menuItem1 = DressItem(user_id=1, name="jeans", description="blue n bottom wear",
                     price="$12.99", course=" Bottom", shop=shop1)

session.add(menuItem1)
session.commit()


menuItem3 = DressItem(user_id=1, name="shorts", description="denim",
                     price="$23.99", course="Bottom ", shop=shop1)

session.add(menuItem3)
session.commit()


# Menu for maccies
shop2 = Shop(user_id=1, name="Maccies")

session.add(shop2)
session.commit()


menuItem1 = DressItem(user_id=1, name="parse", description="red color",
                     price="$97.99", course="Misc ", shop=shop2)

session.add(menuItem1)
session.commit()

menuItem2 = DressItem(user_id=1, name="dress",
                     description=" blue floral print",
                     price="$55", course="Dresses ", shop=shop2)

session.add(menuItem2)
session.commit()


# Menu for walmart
shop3 = Shop(user_id=1, name="walmart")

session.add(shop3)
session.commit()


menuItem1 = DressItem(user_id=1, name="lunch bag", description="a lunch bag with bottle",
                     price="$28.99", course="Utensils", shop=shop3)

session.add(menuItem1)
session.commit()

menuItem2 = DressItem(user_id=1, name="face wash", description="aevone face wash",
                     price="$6.99", course="Skin ", shop=shop3)


print "added menu items!"