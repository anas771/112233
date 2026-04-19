from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from .base import Base

class MarketSale(Base):
    __tablename__ = 'market_sales'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id'))
    date = Column(Date)
    qty_sold = Column(Integer)
    total_weight = Column(Float)
    price_per_kg = Column(Float)
    total_val = Column(Float)
    net_val = Column(Float)
    deaths = Column(Integer, default=0)

class FarmSale(Base):
    __tablename__ = 'farm_sales'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id'))
    date = Column(Date)
    qty = Column(Integer)
    weight = Column(Float)
    price = Column(Float)
    total_val = Column(Float)
