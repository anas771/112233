from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Date, DateTime, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String(100), primary_key=True)
    value = Column(Text)

class Warehouse(Base):
    __tablename__ = 'warehouses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    notes = Column(Text, default='')
    
    batches = relationship("Batch", back_populates="warehouse", cascade="all, delete-orphan")

class Batch(Base):
    __tablename__ = 'batches'
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    batch_num = Column(String(50), default='')
    partner_name = Column(String(100), default='')
    
    date_in = Column(Date, nullable=False)
    date_out = Column(Date)
    days = Column(Integer, default=0)
    
    # Inputs
    chicks = Column(Integer, nullable=False)
    chick_price = Column(Float, default=0.0)
    chick_val = Column(Float, default=0.0)
    
    # Costs summary (can be calculated or stored)
    feed_qty = Column(Float, default=0.0)  # tons
    feed_val = Column(Float, default=0.0)
    feed_trans = Column(Float, default=0.0)
    
    total_cost = Column(Float, default=0.0)
    total_rev = Column(Float, default=0.0)
    net_result = Column(Float, default=0.0)
    
    # Stats
    total_dead = Column(Integer, default=0)
    mort_rate = Column(Float, default=0.0)
    avg_weight = Column(Float, default=0.0)
    fcr = Column(Float, default=0.0)
    epef = Column(Float, default=0.0)
    
    # Sharing
    share_pct = Column(Float, default=65.0)
    share_val = Column(Float, default=0.0)
    
    notes = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

    warehouse = relationship("Warehouse", back_populates="batches")
    daily_records = relationship("DailyRecord", back_populates="batch", cascade="all, delete-orphan")
    farm_sales = relationship("FarmSale", back_populates="batch", cascade="all, delete-orphan")
    market_sales = relationship("MarketSale", back_populates="batch", cascade="all, delete-orphan")
    cost_records = relationship("CostRecord", back_populates="batch", cascade="all, delete-orphan")
    vaccinations = relationship("Vaccination", back_populates="batch", cascade="all, delete-orphan")

class DailyRecord(Base):
    __tablename__ = 'daily_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey('batches.id', ondelete='CASCADE'), nullable=False)
    rec_date = Column(Date, nullable=False)
    day_num = Column(Integer, default=0)
    dead_count = Column(Integer, default=0)
    feed_kg = Column(Float, default=0.0)
    water_ltr = Column(Float, default=0.0)
    temperature = Column(Float)
    humidity = Column(Float)
    notes = Column(Text, default='')

    batch = relationship("Batch", back_populates="daily_records")

class FarmSale(Base):
    __tablename__ = 'farm_sales'
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey('batches.id', ondelete='CASCADE'), nullable=False)
    customer = Column(String(200))
    qty = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    total_val = Column(Float, default=0.0)
    sale_date = Column(Date)
    notes = Column(Text, default='')

    batch = relationship("Batch", back_populates="farm_sales")

class MarketSale(Base):
    __tablename__ = 'market_sales'
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey('batches.id', ondelete='CASCADE'), nullable=False)
    office = Column(String(200))
    qty_sent = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    qty_sold = Column(Integer, default=0)
    net_val = Column(Float, default=0.0)
    inv_num = Column(String(50))
    sale_date = Column(Date)

    batch = relationship("Batch", back_populates="market_sales")

class CostRecord(Base):
    __tablename__ = 'cost_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey('batches.id', ondelete='CASCADE'), nullable=False)
    cost_name = Column(String(200))
    category = Column(String(100)) # Feed, Drugs, Sawdust, Gas, Labor, etc.
    qty = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    company_val = Column(Float, default=0.0)
    supervisor_val = Column(Float, default=0.0)
    notes = Column(Text, default='')
    date_recorded = Column(Date)

    batch = relationship("Batch", back_populates="cost_records")

class Vaccination(Base):
    __tablename__ = 'vaccinations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey('batches.id', ondelete='CASCADE'), nullable=False)
    vaccine_name = Column(String(100))
    planned_date = Column(Date)
    applied_date = Column(Date)
    is_done = Column(Boolean, default=False)
    notes = Column(Text, default='')

    batch = relationship("Batch", back_populates="vaccinations")

class InventoryItem(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True)
    category = Column(String(100)) # Feed, Medication, etc.
    unit = Column(String(20)) # Kg, Liter, Bag
    current_stock = Column(Float, default=0.0)
    min_stock = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.now)
