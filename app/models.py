from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.sqlite import DATETIME as DateTime
from datetime import datetime

Base = declarative_base()

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    receipt_title = Column(String)
    image_filename = Column(String)
    purchase_date = Column(String)
    item = Column(String)
    quantity = Column(Float)
    price = Column(Float)
