from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import sys
import json
import tempfile
import zipfile
from datetime import datetime
import re

# Lägg till projektets root-katalog i Python path
sys.path.insert(0, os.path.dirname(__file__))

# Importera dina befintliga moduler
from database.db_manager import DatabaseManager

def extract_all_files(tree_node):
    """Extrahera alla filer från trädstrukturen"""
    files = []
    
    # Lägg till filer från nuvarande nod
    if 'files' in tree_node:
        files.extend(tree_node['files'])
    
    # Rekursivt gå igenom barn-noder
    if 'children' in tree_node:
        for child_name, child_node in tree_node['children'].items():
            files.extend(extract_all_files(child_node))
    
    return files

def extract_all_files_with_paths(tree_node, root_path, current_relative_path=""):
    """Extrahera alla filer med korrekt path-info"""
    files = []
    
    # Lägg till filer från nuvarande nod
    if 'files' in tree_node:
        for file_data in tree_node['files']:
            filename = file_data.get('name', '')
            
            # file_path är den relativa sökvägen från disk-root
            file_path = current_relative_path
            
            # full_path inkluderar filename
            full_path = f"{file_path}/{filename}" if file_path else filename
            
            files.append({
                'filename': filename,
                'file_path': file_path,
                'full_path': full_path,
                'file_size': file_data.get('size', 0),
                'extension': file_data.get('extension', ''),
                'created': file_data.get('created', ''),
                'modified': file_data.get('modified', '')
            })
    
    # Rekursivt gå igenom barn-noder
    if 'children' in tree_node:
        for child_name, child_node in tree_node['children'].items():
            child_path = f"{current_relative_path}/{child_name}" if current_relative_path else child_name
            files.extend(extract_all_files_with_paths(child_node, root_path, child_path))
    
    return files

def init_database(db_path: str):
    """Initialize the database with required tables"""
    import sqlite3
    
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='disks'")
    if cursor.fetchone() is None:
        print("🏗️ Creating database tables...")
        
        # Create disks table
        cursor.execute('''
            CREATE TABLE disks (
                disk_id TEXT PRIMARY KEY,
                disk_name TEXT NOT NULL,
                description TEXT,
                total_size INTEGER DEFAULT 0,
                file_count INTEGER DEFAULT 0,
                scan_date TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create files table
        cursor.execute('''
            CREATE TABLE files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disk_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT,
                full_path TEXT,
                file_size INTEGER DEFAULT 0,
                file_type TEXT,
                mime_type TEXT,
                created_date TEXT,
                modified_date TEXT,
                scan_date TEXT,
                client TEXT,
                project TEXT,
                keywords TEXT,
                checksum TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (disk_id) REFERENCES disks (disk_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE directories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disk_id TEXT NOT NULL,
                directory_path TEXT NOT NULL,        -- "folder1/subfolder2"
                directory_name TEXT NOT NULL,        -- "subfolder2"  
                parent_path TEXT,                    -- "folder1" (NULL för root)
                depth_level INTEGER NOT NULL,       -- 0 för root, 1 för första nivå, etc
                file_count INTEGER DEFAULT 0,       -- Antal filer direkt i denna mapp
                subdirectory_count INTEGER DEFAULT 0, -- Antal undermappar
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (disk_id) REFERENCES disks (disk_id)
            )
        ''')
        
        # Create indexes for better performance
        indexes = [
            'CREATE INDEX idx_files_disk_id ON files (disk_id)',
            'CREATE INDEX idx_files_filename ON files (filename)',
            'CREATE INDEX idx_files_file_path ON files (file_path)',
            'CREATE INDEX idx_files_full_path ON files (full_path)',
            'CREATE INDEX idx_files_client ON files (client)',
            'CREATE INDEX idx_files_project ON files (project)',
            'CREATE INDEX idx_files_file_type ON files (file_type)',
            'CREATE INDEX idx_directories_path ON directories (disk_id, directory_path)',
            'CREATE INDEX idx_directories_disk_parent ON directories (disk_id, parent_path)',
            'CREATE INDEX idx_directories_disk_depth ON directories (disk_id, depth_level)',
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        print("✅ Database tables created successfully")
    else:
        print("ℹ️ Database tables already exist")
    
    conn.close()
    print(f"✅ Database ready at: {db_path}")

# Initialize database
DB_PATH = os.getenv('DB_PATH', '/app/data/cold_storage.db')
print(f"🗄️ Initializing database at: {DB_PATH}")
init_database(DB_PATH)

app = FastAPI(
    title="Cold Storage API",
    description="API för Cold Storage hårddisk-indexering",
    version="2.0.0"
)

# CORS för React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Databas
db_manager = DatabaseManager(DB_PATH)

@app.get("/")
async def root():
    """Grundläggande API-info"""
    return {
        "message": "Cold Storage API",
        "version": "2.0.0",
        "status": "running",
        "database": DB_PATH,
        "endpoints": {
            "disks": "/disks",
            "disk_detail": "/disks/{disk_id}",
            "disk_files": "/disks/{disk_id}/files",
            "search": "/search",
            "upload_json": "/upload/json-index",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/disks")
async def get_disks():
    """Hämta alla hårddiskar"""
    try:
        print("🔍 Fetching disks...")
        disks = db_manager.get_all_disks()
        print(f"✅ Found {len(disks)} disks")
        return disks
    except Exception as e:
        print(f"❌ Error fetching disks: {e}")
        raise HTTPException(status_code=500, detail=f"Kunde inte hämta diskar: {str(e)}")

@app.get("/disks/{disk_id}")
async def get_disk(disk_id: str):
    """Hämta information om en specifik hårddisk"""
    try:
        print(f"🔍 Fetching disk: {disk_id}")
        disk_info = db_manager.get_disk_info(disk_id)
        if not disk_info:
            raise HTTPException(status_code=404, detail="Hårddisk inte hittad")
        return disk_info
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching disk {disk_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Kunde inte hämta disk: {str(e)}")

@app.get("/disks/{disk_id}/files")
async def get_disk_files(
    disk_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    path: Optional[str] = None
):
    """Hämta filer från en specifik hårddisk"""
    try:
        print(f"🔍 Fetching files for disk: {disk_id}, path: {path}")
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Grundläggande query
        base_query = """
            SELECT filename, file_path, full_path, file_size, file_type, 
                   mime_type, created_date, modified_date, client, project, keywords
            FROM files 
            WHERE disk_id = ?
        """
        params = [disk_id]
        
        # Lägg till path-filter om det finns
        if path:
            base_query += " AND file_path LIKE ?"
            params.append(f"{path}%")
        
        # Räkna totalt antal först
        count_query = "SELECT COUNT(*) FROM files WHERE disk_id = ?"
        count_params = [disk_id]
        if path:
            count_query += " AND file_path LIKE ?"
            count_params.append(f"{path}%")
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        # Hämta filer
        base_query += " ORDER BY file_path, filename LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(base_query, params)
        files = []
        for row in cursor.fetchall():
            file_info = {
                "filename": row[0],
                "file_path": row[1],
                "full_path": row[2],
                "file_size": row[3],
                "file_type": row[4],
                "mime_type": row[5],
                "created_date": row[6],
                "modified_date": row[7],
                "client": row[8],
                "project": row[9],
                "keywords": row[10]
            }
            files.append(file_info)
        
        conn.close()
        print(f"✅ Returning {len(files)} files out of {total_count} total")
        
        return {
            "files": files,
            "total_count": total_count,
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        print(f"❌ Error fetching files: {e}")
        raise HTTPException(status_code=500, detail=f"Kunde inte hämta filer: {str(e)}")

@app.get("/search")
async def search_files(
    q: str = Query(..., description="Sökterm"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=1000),
    client: Optional[str] = None,
    project: Optional[str] = None,
    file_type: Optional[str] = None,
    disk_id: Optional[str] = None
):
    """Sök efter filer"""
    try:
        print(f"🔍 Searching for: {q}")
        print(f"   Filters - client: {client}, project: {project}, file_type: {file_type}, disk_id: {disk_id}")
        
        # Anropa search_files med bara de parametrar som den förväntar sig
        # Ta bort 'project' parameter tills vi uppdaterar db_manager
        results = db_manager.search_files(
            query=q,
            disk_id=disk_id or '',
            file_type=file_type or '',
            client=client or '',
            limit=per_page
        )
        
        # Om project-filter är specificerat, filtrera resultaten efteråt
        if project and results:
            results = [r for r in results if r.get('project') and project.lower() in r.get('project', '').lower()]
        
        print(f"✅ Found {len(results)} search results")
        return {
            "files": results,
            "total_count": len(results),
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        print(f"❌ Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Sökfel: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Hämta systemstatistik"""
    try:
        print("🔍 Fetching system stats...")
        stats = db_manager.get_system_stats()
        return stats
    except Exception as e:
        print(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Statistik-fel: {str(e)}")

@app.get("/disks/{disk_id}/directories")
async def get_disk_directories(
    disk_id: str,
    parent_path: Optional[str] = Query(None, description="Parent directory path (NULL för root)")
):
    """Hämta mappar i en specifik nivå - SUPERSNABBT"""
    try:
        print(f"📁 Fast directory fetch: disk={disk_id}, parent='{parent_path or 'ROOT'}'")
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        if parent_path is None or parent_path == "":
            # ROOT LEVEL - bara första nivån
            cursor.execute("""
                SELECT directory_name, directory_path, file_count, subdirectory_count
                FROM directories 
                WHERE disk_id = ? AND depth_level = 0
                ORDER BY directory_name
            """, (disk_id,))
        else:
            # SPECIFIK MAPP - bara direkta barn
            cursor.execute("""
                SELECT directory_name, directory_path, file_count, subdirectory_count
                FROM directories 
                WHERE disk_id = ? AND parent_path = ?
                ORDER BY directory_name
            """, (disk_id, parent_path))
        
        directories = []
        for row in cursor.fetchall():
            directories.append({
                "name": row[0],
                "path": row[1], 
                "file_count": row[2],
                "subdirectory_count": row[3],
                "type": "directory"
            })
        
        conn.close()
        print(f"⚡ Super fast return: {len(directories)} directories")
        
        return {
            "directories": directories,
            "parent_path": parent_path
        }
        
    except Exception as e:
        print(f"❌ Directory fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/disks/{disk_id}/files-in-directory")
async def get_files_in_directory(
    disk_id: str,
    directory_path: Optional[str] = Query(None, description="Directory path (NULL för root)")
):
    """Hämta bara filer i en specifik mapp - SUPERSNABBT"""
    try:
        print(f"📄 Fast file fetch: disk={disk_id}, dir='{directory_path or 'ROOT'}'")
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        if directory_path is None or directory_path == "":
            # ROOT FILES
            cursor.execute("""
                SELECT filename, file_size, file_type, modified_date, client, project
                FROM files 
                WHERE disk_id = ? AND (file_path = '' OR file_path IS NULL)
                ORDER BY filename
            """, (disk_id,))
        else:
            # FILER I SPECIFIK MAPP
            cursor.execute("""
                SELECT filename, file_size, file_type, modified_date, client, project
                FROM files 
                WHERE disk_id = ? AND file_path = ?
                ORDER BY filename
            """, (disk_id, directory_path))
        
        files = []
        for row in cursor.fetchall():
            files.append({
                "filename": row[0],
                "file_size": row[1],
                "file_type": row[2], 
                "modified_date": row[3],
                "client": row[4],
                "project": row[5],
                "type": "file"
            })
        
        conn.close()
        print(f"⚡ Super fast return: {len(files)} files")
        
        return {
            "files": files,
            "directory_path": directory_path
        }
        
    except Exception as e:
        print(f"❌ Files fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/disks/{disk_id}/browse")
async def browse_directory(
    disk_id: str,
    path: Optional[str] = Query(None, description="Directory path")
):
    """Kombinerad endpoint - hämta både mappar och filer för en nivå"""
    try:
        print(f"🗂️ Browse: disk={disk_id}, path='{path or 'ROOT'}'")
        
        # Parallella anrop för mappar och filer
        directories_response = await get_disk_directories(disk_id, path)
        files_response = await get_files_in_directory(disk_id, path)
        
        # Kombinera resultat
        items = []
        
        # Lägg till mappar först
        for directory in directories_response["directories"]:
            items.append({
                "filename": directory["name"],
                "type": "folder",
                "file_size": None,
                "file_count": directory["file_count"],
                "subdirectory_count": directory["subdirectory_count"],
                "path": directory["path"]
            })
        
        # Lägg till filer
        for file in files_response["files"]:
            items.append({
                "filename": file["filename"],
                "type": "file", 
                "file_size": file["file_size"],
                "file_type": file["file_type"],
                "modified_date": file["modified_date"],
                "client": file["client"],
                "project": file["project"]
            })
        
        print(f"⚡ Browse result: {len(directories_response['directories'])} dirs + {len(files_response['files'])} files")
        
        return {
            "items": items,
            "path": path,
            "directory_count": len(directories_response["directories"]),
            "file_count": len(files_response["files"])
        }
        
    except Exception as e:
        print(f"❌ Browse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/json-index")
async def upload_json_index(file: UploadFile = File(...)):
    """Ladda upp och importera JSON-index från SimpleTreeIndexer"""
    print(f"📁 Uploading file: {file.filename}")
    
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Endast JSON-filer tillåtna")
    
    try:
        # Läs JSON-innehåll
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Validera JSON-struktur
        if 'scan_info' not in data or 'tree' not in data:
            raise HTTPException(status_code=400, detail="Ogiltig JSON-struktur. Förväntar SimpleTreeIndexer format.")
        
        # Extrahera metadata
        scan_info = data['scan_info']
        tree = data['tree']
        statistics = data.get('statistics', {})
        
        # Skapa disk_id från root path och datum
        root_path = scan_info.get('root_path', '')
        scan_date = scan_info.get('scan_date', '')
        
        # Generera disk_id (t.ex. "HD_2025_20250623")
        year = None
        if root_path:
            year_match = re.search(r'/(\d{4})(?:/|$)', root_path)
            if year_match:
                year = year_match.group(1)
        
        if not year and scan_date:
            try:
                dt = datetime.fromisoformat(scan_date.replace('Z', '+00:00'))
                year = str(dt.year)
            except:
                year = "UNKN"
        
        # Skapa disk_id
        date_part = scan_date[:10].replace('-', '') if scan_date else "00000000"
        disk_id = f"HD_{year}_{date_part}"
        
        # Kontrollera om disk redan finns
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT disk_id FROM disks WHERE disk_id = ?", (disk_id,))
        if cursor.fetchone():
            # Lägg till suffix om den redan finns
            counter = 1
            while True:
                new_disk_id = f"{disk_id}_{counter}"
                cursor.execute("SELECT disk_id FROM disks WHERE disk_id = ?", (new_disk_id,))
                if not cursor.fetchone():
                    disk_id = new_disk_id
                    break
                counter += 1
        
        # Skapa disk-namn från root path
        disk_name = root_path.split('/')[-1] if root_path else f"Disk {disk_id}"
        total_size = sum(f.get('size', 0) for f in extract_all_files(tree))
        total_files = statistics.get('total_files', 0)
        
        print(f"💿 Creating disk: {disk_id} ({disk_name})")
        
        # Lägg till disk i databasen
        cursor.execute('''
            INSERT INTO disks (
                disk_id, disk_name, description, total_size, file_count, 
                scan_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            disk_id,
            disk_name,
            f"Importerad från {file.filename}",
            total_size,
            total_files,
            scan_date,
            'active'
        ))
        
        # Extrahera och importera alla filer
        files_imported = 0
        all_files = extract_all_files_with_paths(tree, root_path)
        
        print(f"📄 Importing {len(all_files)} files...")
        
        for file_info in all_files:
            try:
                cursor.execute('''
                    INSERT INTO files (
                        disk_id, filename, file_path, full_path, file_size,
                        file_type, mime_type, created_date, modified_date,
                        scan_date, client, project, keywords
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    disk_id,
                    file_info['filename'],
                    file_info['file_path'],
                    file_info['full_path'],
                    file_info['file_size'],
                    file_info['extension'].lstrip('.') if file_info['extension'] else None,
                    None,  # mime_type
                    file_info['created'],
                    file_info['modified'],
                    scan_date,
                    None,  # client - kommer fyllas i via tagging
                    None,  # project - kommer fyllas i via tagging
                    None   # keywords
                ))
                files_imported += 1
            except Exception as e:
                print(f"⚠️ Error importing file {file_info['filename']}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Import complete: {files_imported} files imported")
        
        return {
            "success": True,
            "disk_id": disk_id,
            "disk_name": disk_name,
            "files_imported": files_imported,
            "total_files": total_files,
            "total_size": total_size,
            "message": f"Hårddisk {disk_id} importerad framgångsrikt"
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Ogiltig JSON-fil")
    except Exception as e:
        print(f"❌ Import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import-fel: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Cold Storage API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

    