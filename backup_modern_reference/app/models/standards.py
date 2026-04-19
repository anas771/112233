from sqlalchemy import Column, Integer, Float
from .base import Base

class BatchStandards(Base):
    __tablename__ = 'batch_standards'
    id = Column(Integer, primary_key=True)
    day = Column(Integer)
    feed_per_bird = Column(Float)
    weight_gain = Column(Float)
    cum_feed = Column(Float)
