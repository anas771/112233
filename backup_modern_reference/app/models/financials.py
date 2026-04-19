from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class CostType(Base):
    __tablename__ = 'cost_types'
    code = Column(String(50), primary_key=True)
    name_ar = Column(String(100), nullable=False)
    category = Column(String(50))

class RevenueType(Base):
    __tablename__ = 'revenue_types'
    code = Column(String(50), primary_key=True)
    name_ar = Column(String(100), nullable=False)

class BatchCost(Base):
    __tablename__ = 'batch_costs'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id'))
    cost_type_code = Column(String(50), ForeignKey('cost_types.code'))
    total_val = Column(Float, default=0.0)
    
    cost_type = relationship("CostType")

class BatchRevenue(Base):
    __tablename__ = 'batch_revenues'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id'))
    rev_type_code = Column(String(50), ForeignKey('revenue_types.code'))
    qty = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    
    revenue_type = relationship("RevenueType")
