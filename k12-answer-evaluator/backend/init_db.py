#!/usr/bin/env python3
"""Initialize database tables"""

from app.core.database import engine, Base
from app.models import *

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    init_db()
