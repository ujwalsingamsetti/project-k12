"""Migration script to add new columns to questions and question_papers tables"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Add section and has_or_option to questions table
        try:
            conn.execute(text("ALTER TABLE questions ADD COLUMN section VARCHAR(10)"))
            print("✓ Added section column to questions")
        except Exception as e:
            print(f"section column might already exist: {e}")
        
        try:
            conn.execute(text("ALTER TABLE questions ADD COLUMN has_or_option BOOLEAN DEFAULT FALSE"))
            print("✓ Added has_or_option column to questions")
        except Exception as e:
            print(f"has_or_option column might already exist: {e}")
        
        # Add pdf_path to question_papers table
        try:
            conn.execute(text("ALTER TABLE question_papers ADD COLUMN pdf_path VARCHAR"))
            print("✓ Added pdf_path column to question_papers")
        except Exception as e:
            print(f"pdf_path column might already exist: {e}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate()
