from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # En production, utiliser un hash
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    calculations = relationship("Calculation", back_populates="user")


class Equipment(Base):
    __tablename__ = "equipments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    price = Column(Float)
    eco_score = Column(Float)
    lifespan = Column(Integer)  # en années


class Calculation(Base):
    __tablename__ = "calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    house = Column(String)  # Maison LVMH sélectionnée
    equipments = Column(Text)  # JSON des équipements
    eco_weight = Column(Float)  # Pondération écologique (0-100)
    financial_weight = Column(Float)  # Pondération financière (0-100)
    financial_score = Column(Float)
    ecological_score = Column(Float)
    global_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    user = relationship("User", back_populates="calculations")
