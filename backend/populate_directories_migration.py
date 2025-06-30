#!/usr/bin/env python3
"""
Migration script för att skapa och populera directories-tabell
"""

import sqlite3
import os
from collections import defaultdict

def migrate_database(db_path):
    """Migrera databasen med directories-tabell"""
    
    print(f"🔧 Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Skapa directories-tabell
        print("📁 Creating directories table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disk_id TEXT NOT NULL,
                directory_path TEXT NOT NULL,
                directory_name TEXT NOT NULL,
                parent_path TEXT,
                depth_level INTEGER NOT NULL,
                file_count INTEGER DEFAULT 0,
                subdirectory_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (disk_id) REFERENCES disks (disk_id)
            )
        """)
        
        # 2. Skapa index
        print("📊 Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_directories_disk_parent ON directories (disk_id, parent_path)",
            "CREATE INDEX IF NOT EXISTS idx_directories_disk_depth ON directories (disk_id, depth_level)",
            "CREATE INDEX IF NOT EXISTS idx_directories_path ON directories (disk_id, directory_path)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # 3. Hämta alla diskar
        cursor.execute("SELECT DISTINCT disk_id FROM files")
        disk_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"🗂️ Processing {len(disk_ids)} disks...")
        
        for disk_id in disk_ids:
            print(f"📀 Processing disk: {disk_id}")
            populate_directories_for_disk(cursor, disk_id)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # 4. Visa statistik
        cursor.execute("SELECT COUNT(*) FROM directories")
        dir_count = cursor.fetchone()[0]
        print(f"📊 Created {dir_count} directory entries")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def populate_directories_for_disk(cursor, disk_id):
    """Populera directories för en specifik disk"""
    
    # Hämta alla unika directory paths för denna disk
    cursor.execute("""
        SELECT DISTINCT file_path 
        FROM files 
        WHERE disk_id = ? AND file_path IS NOT NULL AND file_path != ''
        ORDER BY file_path
    """, (disk_id,))
    
    file_paths = [row[0] for row in cursor.fetchall()]
    
    # Bygg directory-hierarki
    directories = set()
    
    for file_path in file_paths:
        # Lägg till alla delar av sökvägen
        parts = file_path.split('/')
        current_path = ""
        
        for i, part in enumerate(parts):
            if current_path:
                current_path += "/" + part
            else:
                current_path = part
            
            parent_path = "/".join(parts[:i]) if i > 0 else None
            depth = i
            
            directories.add((current_path, part, parent_path, depth))
    
    # Spara directories i databasen
    for directory_path, directory_name, parent_path, depth_level in directories:
        
        # Räkna filer direkt i denna mapp
        cursor.execute("""
            SELECT COUNT(*) 
            FROM files 
            WHERE disk_id = ? AND file_path = ?
        """, (disk_id, directory_path))
        file_count = cursor.fetchone()[0]
        
        # Räkna undermappar
        cursor.execute("""
            SELECT COUNT(DISTINCT SUBSTR(file_path, LENGTH(?) + 2, 
                   CASE WHEN INSTR(SUBSTR(file_path, LENGTH(?) + 2), '/') > 0 
                        THEN INSTR(SUBSTR(file_path, LENGTH(?) + 2), '/') - 1
                        ELSE LENGTH(SUBSTR(file_path, LENGTH(?) + 2))
                   END))
            FROM files 
            WHERE disk_id = ? AND file_path LIKE ? AND file_path != ?
        """, (directory_path, directory_path, directory_path, directory_path, 
              disk_id, f"{directory_path}/%", directory_path))
        subdirectory_count = cursor.fetchone()[0]
        
        # Lägg till directory
        cursor.execute("""
            INSERT OR REPLACE INTO directories 
            (disk_id, directory_path, directory_name, parent_path, depth_level, file_count, subdirectory_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (disk_id, directory_path, directory_name, parent_path, depth_level, file_count, subdirectory_count))
    
    print(f"   📁 Added {len(directories)} directories for {disk_id}")

if __name__ == "__main__":
    # Kör migration
    DB_PATH = os.getenv('DB_PATH', '/app/data/cold_storage.db')
    migrate_database(DB_PATH)