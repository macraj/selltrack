from datetime import date, datetime, timedelta

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from db import Base

DEFAULT_EXPIRATION_DAYS = 180


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    items = relationship('Item', back_populates='category_rel')


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    auction_link = Column(String(500))
    date_added = Column(DateTime, default=datetime.utcnow)
    activation_date = Column(Date)
    expiration_days = Column(Integer, default=DEFAULT_EXPIRATION_DAYS)
    removal_date = Column(Date)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    status = Column(String(20), default='w_magazynie')

    category_rel = relationship('Category', back_populates='items')
    images = relationship('ItemImage', back_populates='item', cascade='all, delete-orphan')

    @property
    def calculated_status(self):
        if self.status in ('sprzedany', 'zdjety'):
            return self.status
        if self.status == 'w_magazynie' or self.activation_date is None:
            return 'w_magazynie'
        if date.today() > self.activation_date + timedelta(days=self.expiration_days):
            return 'do_likwidacji'
        return 'aktywny'

    @property
    def expiration_date(self):
        if self.activation_date is None:
            return None
        return self.activation_date + timedelta(days=self.expiration_days)

    @property
    def days_until_expiration(self):
        if self.activation_date is None:
            return None
        return (self.expiration_date - date.today()).days


class ItemImage(Base):
    __tablename__ = 'item_images'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)

    item = relationship('Item', back_populates='images')
