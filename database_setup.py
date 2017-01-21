import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__= 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Item(Base):
    __tablename__= 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    itemPicture = Column(String(250))
    description = Column(String(250))
    contactinfo=Column(String(250))
    itemtype = Column(String(250))
    price = Column(String(8))
    location=Column(String(250))
    contactinfo=Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return{
            'title': self.title,
            'id' : self.id,
            'itemPicture' : self.itemPicture,
            'price': self.price,
            'description': self.description,
            'itemtype': self.itemtype,
            'contactinfo' : self.contactinfo,
            'location': self.location,
            'user_id' : self.user_id

        }

engine = create_engine('sqlite:///items.db')
Base.metadata.create_all(engine)
