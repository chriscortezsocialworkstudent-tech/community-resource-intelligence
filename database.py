# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 12:41:51 2026

@author: cortez
"""

import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    org_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    
    # Granular Address Fields
    street_address = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    county = Column(String(100))
    
    latitude = Column(Float)
    longitude = Column(Float)
    
    funding_status = Column(String(50), default="Open")
    eligibility_notes = Column(Text)
    proof_url = Column(String(500))

    # Audit & Verification Controls
    last_verified = Column(DateTime, default=datetime.datetime.utcnow)
    verified_by_student = Column(String(100))
    verification_status = Column(String(50), default="Pending")
    points_awarded = Column(Integer, default=10)
    rejection_reason = Column(Text, nullable=True)


engine = create_engine("sqlite:///cris_prototype.db", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)