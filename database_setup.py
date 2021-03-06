from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Shop(Base):
    __tablename__ = 'shop'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    #user_id = Column(Integer, ForeignKey('user.id'))
    #user = relationship(User)
    creator_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    dress_item = relationship('DressItem', cascade='all, delete-orphan')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class DressItem(Base):
    __tablename__ = 'dress_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    course = Column(String(250))
    shop_id = Column(Integer, ForeignKey('shop.id'))
    shop = relationship(Shop)
    #user_id = Column(Integer, ForeignKey('user.id'))
    #user = relationship(User)
    creator_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'course': self.course,
        }



engine = create_engine('sqlite:///shopitems.db')


Base.metadata.create_all(engine)