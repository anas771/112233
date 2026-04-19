from sqlalchemy import Column, Integer, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base

class DailyRecord(Base):
    __tablename__ = 'daily_records'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id'))
    date = Column(Date, nullable=False)
    dead_count = Column(Integer, default=0)
    feed_kg = Column(Float, default=0.0)
    water_liters = Column(Float, default=0.0)
    avg_weight = Column(Float, default=0.0)
    notes = Column(Text)
    
    batch = relationship("Batch", back_populates="daily_records")
