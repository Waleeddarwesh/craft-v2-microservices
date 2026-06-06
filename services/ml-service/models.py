from sqlalchemy import Column, Integer, String, Float, DateTime, BigIntegerField
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FrequentlyBoughtTogether(Base):
    __tablename__ = "frequently_bought_together"

    id = Column(Integer, primary_key=True, index=True)
    product_a_id = Column(BigIntegerField, index=True)
    product_b_id = Column(BigIntegerField)
    score = Column(Float)
    computed_at = Column(DateTime, default=datetime.utcnow)

class UserProductView(Base):
    __tablename__ = "user_product_views"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigIntegerField, index=True)
    product_id = Column(BigIntegerField, index=True)
    viewed_at = Column(DateTime, default=datetime.utcnow)

class UserProductInteraction(Base):
    __tablename__ = "user_product_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigIntegerField, index=True)
    product_id = Column(BigIntegerField, index=True)
    interaction_type = Column(String(50)) # 'view', 'cart', 'purchase'
    timestamp = Column(DateTime, default=datetime.utcnow)

class AnalyticsAggregate(Base):
    __tablename__ = "analytics_aggregates"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), index=True)
    dimension = Column(String(100), nullable=True)
    value = Column(Float)
    period = Column(String(50)) # 'daily', 'weekly', 'monthly'
    computed_at = Column(DateTime, default=datetime.utcnow)
