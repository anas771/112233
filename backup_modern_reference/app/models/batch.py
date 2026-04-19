from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base

class Warehouse(Base):
    __tablename__ = 'warehouses'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    batches = relationship("Batch", back_populates="warehouse")

class Batch(Base):
    __tablename__ = 'batches'
    
    id = Column(Integer, primary_key=True)
    batch_num = Column(Integer, nullable=False)
    wh_id = Column(Integer, ForeignKey('warehouses.id'))
    date_in = Column(Date)
    date_out = Column(Date)
    partner_name = Column(String(100))
    share_pct = Column(Float, default=65.0)
    
    # Financials (Legacy Columns)
    chicks = Column(Integer, default=0)
    chick_val = Column(Float, default=0.0)
    feed_qty = Column(Float, default=0.0)
    feed_val = Column(Float, default=0.0)
    sawdust_qty = Column(Float, default=0.0)
    sawdust_val = Column(Float, default=0.0)
    gas_qty = Column(Float, default=0.0)
    gas_val = Column(Float, default=0.0)
    water_val = Column(Float, default=0.0)
    drugs_val = Column(Float, default=0.0)
    wh_expenses = Column(Float, default=0.0)
    house_exp = Column(Float, default=0.0)
    breeders_pay = Column(Float, default=0.0)
    qat_pay = Column(Float, default=0.0)
    rent_val = Column(Float, default=0.0)
    light_val = Column(Float, default=0.0)
    admin_val = Column(Float, default=0.0)
    vaccine_pay = Column(Float, default=0.0)
    
    # Supervisor pays
    sup_wh_pay = Column(Float, default=0.0)
    sup_co_pay = Column(Float, default=0.0)
    sup_sale_pay = Column(Float, default=0.0)
    
    # Other costs/rev
    delivery_val = Column(Float, default=0.0)
    mixing_val = Column(Float, default=0.0)
    wash_val = Column(Float, default=0.0)
    other_costs = Column(Float, default=0.0)
    
    offal_val = Column(Float, default=0.0)
    feed_sale = Column(Float, default=0.0)
    feed_sale_qty = Column(Float, default=0.0)
    feed_trans_r = Column(Float, default=0.0)
    feed_trans_r_qty = Column(Float, default=0.0)
    feed_rem_qty = Column(Float, default=0.0)
    drug_return = Column(Float, default=0.0)
    gas_return = Column(Float, default=0.0)
    
    # Stats
    total_cost = Column(Float, default=0.0)
    total_rev = Column(Float, default=0.0)
    net_result = Column(Float, default=0.0)
    total_dead = Column(Integer, default=0)
    total_sold = Column(Integer, default=0)
    mort_rate = Column(Float, default=0.0)
    fcr = Column(Float, default=0.0)
    avg_weight = Column(Float, default=0.0)
    consumed_birds = Column(Integer, default=0)
    
    notes = Column(Text)
    
    warehouse = relationship("Warehouse", back_populates="batches")
    daily_records = relationship("DailyRecord", back_populates="batch")
