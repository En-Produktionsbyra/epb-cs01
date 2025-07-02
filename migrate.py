import os
from sqlalchemy import create_engine, text

DB_URL = os.getenv("DB_URL", "postgresql://cold_user:cold_password@localhost:5432/cold_storage")
engine = create_engine(DB_URL)

def migrate_size_column():
    with engine.connect() as conn:
        try:
            # Ändra size-kolumnen från integer till bigint
            conn.execute(text("ALTER TABLE files ALTER COLUMN size TYPE BIGINT"))
            conn.commit()
            print("✅ Successfully migrated size column to BIGINT")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate_size_column()
