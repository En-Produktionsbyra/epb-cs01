from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import asyncio
import uuid
from typing import Dict, Optional
import threading
import os
import json
import shutil
import re
from datetime import datetime

# Import alla funktioner från db_manager
from database.db_manager import (
    init_db,
    get_session,
    add_disk,
    get_disk_by_id,
    get_disk_by_name,
    get_all_disks,
    delete_disk,
    get_files_by_disk,
    get_directories,
    get_files_in_directory,
    search_files,
    get_system_stats,
    populate_directories_for_disk,
    extract_all_files,
    extract_all_files_with_paths,
    get_disk_info,
    format_file_size,
    SessionLocal,
    FileEntry,
    DirectoryEntry,
    DiskIndex
)

app = FastAPI(
    title="Cold Storage API",
    description="API för Cold Storage hårddisk-indexering med PostgreSQL",
    version="2.0.0"
)

# CORS för React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        "http://192.168.1.228:3000",
        "http://192.168.1.*:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/app/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Progress-tracking i minnet
progress_store: Dict[str, dict] = {}
progress_lock = threading.Lock()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    """Grundläggande API-info"""
    return {
        "message": "Cold Storage API (PostgreSQL-backed)",
        "version": "2.0.0",
        "status": "running",
        "database": "PostgreSQL",
        "endpoints": {
            "disks": "/disks",
            "disk_detail": "/disks/{disk_identifier}",
            "disk_files": "/disks/{disk_identifier}/files",
            "disk_directories": "/disks/{disk_identifier}/directories", 
            "files_in_directory": "/disks/{disk_identifier}/files-in-directory",
            "browse": "/disks/{disk_identifier}/browse",
            "search": "/search",
            "upload_json": "/upload/json-index",
            "upload_json_async": "/upload/json-index-async",
            "stats": "/stats",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        session = SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            session.close()
            return {"status": "healthy", "database": "connected"}
        except Exception as db_error:
            session.close()
            return {"status": "unhealthy", "database": "disconnected", "error": str(db_error)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/disks")
def get_disks():
    """Hämta alla hårddiskar"""
    try:
        print("🔍 Fetching disks...")
        disks = get_all_disks()
        print(f"✅ Found {len(disks)} disks")
        return disks
    except Exception as e:
        print(f"❌ Error fetching disks: {e}")
        raise HTTPException(status_code=500, detail=f"Kunde inte hämta diskar: {str(e)}")

@app.get("/disks/{disk_identifier}")
def get_disk(disk_identifier: str):
    """Hämta information om en specifik hårddisk (via ID eller namn)"""
    try:
        print(f"🔍 Fetching disk: {disk_identifier}")
        
        # Validera disk_identifier
        if disk_identifier == "undefined" or not disk_identifier.strip():
            raise HTTPException(status_code=400, detail="Invalid disk identifier: cannot be 'undefined' or empty")
        
        # Försök först som ID (integer)
        disk_data = None
        try:
            disk_id_int = int(disk_identifier)
            disk_data = get_disk_info(disk_id_int)
        except ValueError:
            # Om det inte är en integer, försök som disk-namn
            disk = get_disk_by_name(disk_identifier)
            if disk:
                disk_data = get_disk_info(disk.id)
        
        if not disk_data:
            raise HTTPException(status_code=404, detail=f"Disk '{disk_identifier}' inte hittad")
        
        return disk_data
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching disk {disk_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"Kunde inte hämta disk: {str(e)}")

@app.get("/disks/{disk_identifier}/files")
def get_disk_files(
    disk_identifier: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    path: Optional[str] = None
):
    """Hämta filer från en specifik hårddisk"""
    try:
        print(f"🔍 Fetching files for disk: {disk_identifier}, path: {path}")
        
        # Hitta disk ID
        disk_id_int = None
        try:
            disk_id_int = int(disk_identifier)
        except ValueError:
            disk = get_disk_by_name(disk_identifier)
            if disk:
                disk_id_int = disk.id
            else:
                raise HTTPException(status_code=404, detail=f"Disk '{disk_identifier}' inte hittad")
        
        session = SessionLocal()
        try:
            # Grundläggande query
            query = session.query(FileEntry).filter(FileEntry.disk_id == disk_id_int)
            
            # Lägg till path-filter om det finns
            if path:
                query = query.filter(FileEntry.path.like(f"{path}%"))
            
            # Räkna totalt antal först
            total_count = query.count()
            
            # Hämta filer med pagination
            files = query.order_by(FileEntry.path, FileEntry.name).offset((page - 1) * per_page).limit(per_page).all()
            
            file_list = []
            for file in files:
                file_info = {
                    "id": file.id,
                    "filename": file.name,
                    "file_path": file.path,
                    "full_path": f"{file.path}/{file.name}" if file.path else file.name,
                    "file_size": file.size,
                    "file_type": file.file_type,
                    "mime_type": file.mime_type,
                    "client": file.client,
                    "project": file.project,
                    "keywords": file.keywords,
                    "checksum": file.checksum
                }
                file_list.append(file_info)
            
            print(f"✅ Returning {len(file_list)} files out of {total_count} total")
            
            return {
                "files": file_list,
                "total_count": total_count,
                "page": page,
                "per_page": per_page
            }
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching files for disk {disk_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"Kunde inte hämta filer: {str(e)}")

@app.get("/disks/{disk_identifier}/directories")
def get_disk_directories(
    disk_identifier: str,
    parent_path: Optional[str] = Query(None, description="Parent directory path")
):
    """Hämta mappar i en specifik nivå"""
    try:
        print(f"📁 Directory fetch: disk={disk_identifier}, parent='{parent_path or 'ROOT'}'")
        
        # Hitta disk ID
        disk_id_int = None
        try:
            disk_id_int = int(disk_identifier)
        except ValueError:
            disk = get_disk_by_name(disk_identifier)
            if disk:
                disk_id_int = disk.id
            else:
                raise HTTPException(status_code=404, detail=f"Disk '{disk_identifier}' inte hittad")
        
        directories = get_directories(disk_id_int, parent_path)
        print(f"⚡ Return: {len(directories)} directories")
        
        return {
            "directories": directories,
            "parent_path": parent_path
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Directory fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/disks/{disk_identifier}/files-in-directory")
def get_files_in_directory_endpoint(
    disk_identifier: str,
    directory_path: Optional[str] = Query(None, description="Directory path")
):
    """Hämta bara filer i en specifik mapp"""
    try:
        print(f"📄 File fetch: disk={disk_identifier}, dir='{directory_path or 'ROOT'}'")
        
        # Hitta disk ID
        disk_id_int = None
        try:
            disk_id_int = int(disk_identifier)
        except ValueError:
            disk = get_disk_by_name(disk_identifier)
            if disk:
                disk_id_int = disk.id
            else:
                raise HTTPException(status_code=404, detail=f"Disk '{disk_identifier}' inte hittad")
        
        files = get_files_in_directory(disk_id_int, directory_path or "")
        print(f"⚡ Return: {len(files)} files")
        
        return {
            "files": files,
            "directory_path": directory_path
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Files fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def browse_directory_fallback(disk_id_int: int, path: Optional[str]):
    """Fallback-metod som använder files-tabellen för att bygga directory-view"""
    
    print(f"🔄 Fallback browse for path: '{path or 'ROOT'}'")
    
    session = SessionLocal()
    try:
        # Hämta alla filer från disken
        all_files = session.query(FileEntry).filter(FileEntry.disk_id == disk_id_int).order_by(FileEntry.path, FileEntry.name).all()
        
        # Organisera items för nuvarande path
        items = []
        folders = set()
        
        current_path = path or ""
        
        for file in all_files:
            file_path = file.path or ""  # Hantera NULL values
            
            if current_path == "":
                # Vi är i root - visa toppnivå mappar och filer
                if file_path == "":
                    # Fil i root
                    items.append({
                        "filename": file.name,
                        "type": "file",
                        "file_size": file.size,
                        "file_type": file.file_type,
                        "client": file.client,
                        "project": file.project
                    })
                else:
                    # Fil i mapp - extrahera första mapp-nivån
                    first_folder = file_path.split('/')[0]
                    if first_folder:
                        folders.add(first_folder)
            else:
                # Vi är i en specifik mapp
                if file_path == current_path:
                    # Fil direkt i denna mapp
                    items.append({
                        "filename": file.name,
                        "type": "file",
                        "file_size": file.size,
                        "file_type": file.file_type,
                        "client": file.client,
                        "project": file.project
                    })
                elif file_path.startswith(current_path + "/"):
                    # Fil i undermapp till denna mapp
                    relative_path = file_path[len(current_path) + 1:]
                    next_folder = relative_path.split('/')[0]
                    if next_folder:
                        folders.add(next_folder)
        
        # Lägg till mappar först
        for folder_name in sorted(folders):
            items.insert(0, {
                "filename": folder_name,
                "type": "folder",
                "file_size": None,
                "file_count": 0,  # Vi beräknar inte detta i fallback
                "subdirectory_count": 0,
                "path": f"{current_path}/{folder_name}" if current_path else folder_name
            })
        
        print(f"🔄 Fallback result: {len(folders)} folders, {len(items) - len(folders)} files")
        
        return items
    finally:
        session.close()

@app.get("/disks/{disk_identifier}/browse")
def browse(
    disk_identifier: str,
    path: Optional[str] = Query(None, description="Directory path")
):
    """Kombinerad endpoint - hämta både mappar och filer för en nivå"""
    try:
        print(f"🗂️ Browse: disk={disk_identifier}, path='{path or 'ROOT'}'")
        
        # Validera disk_identifier
        if disk_identifier == "undefined" or not disk_identifier.strip():
            raise HTTPException(status_code=400, detail="Invalid disk identifier: cannot be 'undefined' or empty")
        
        # Hitta disk ID
        disk_id_int = None
        try:
            disk_id_int = int(disk_identifier)
        except ValueError:
            # Om det inte är en integer, försök som disk-namn
            disk = get_disk_by_name(disk_identifier)
            if disk:
                disk_id_int = disk.id
            else:
                raise HTTPException(status_code=404, detail=f"Disk '{disk_identifier}' inte hittad")
        
        # Kontrollera först om vi har data i directories-tabellen
        session = SessionLocal()
        directory_count = session.query(DirectoryEntry).filter(DirectoryEntry.disk_id == disk_id_int).count()
        session.close()
        
        if directory_count > 0:
            print(f"📁 Using fast directories table ({directory_count} dirs)")
            # Använd den snabba directories-metoden
            dirs_result = get_directories(disk_id_int, path)
            files_result = get_files_in_directory(disk_id_int, path or "")
            
            # Kombinera resultat
            items = []
            
            # Lägg till mappar först
            for directory in dirs_result:
                items.append({
                    "filename": directory.get("name", ""),
                    "type": "folder",
                    "file_size": None,
                    "file_count": directory.get("file_count", 0),
                    "subdirectory_count": directory.get("subdirectory_count", 0),
                    "path": directory.get("path", "")
                })
            
            # Lägg till filer
            for file_item in files_result:
                items.append({
                    "filename": file_item.get("name", ""),
                    "type": "file",
                    "file_size": file_item.get("size", 0),
                    "file_type": file_item.get("file_type", ""),
                    "client": file_item.get("client", ""),
                    "project": file_item.get("project", "")
                })
            
            print(f"⚡ Fast browse result: {len(dirs_result)} dirs + {len(files_result)} files")
            
        else:
            print(f"📄 Using fallback files table method")
            # Fallback: Använd gamla metoden med files-tabellen
            items = browse_directory_fallback(disk_id_int, path)
        
        # Räkna folder vs files
        folders = [item for item in items if item["type"] == "folder"]
        files = [item for item in items if item["type"] == "file"]
        
        return {
            "items": items,
            "path": path,
            "directory_count": len(folders),
            "file_count": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Browse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
def search_files_endpoint(
    q: str = Query("", description="Sökterm"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=1000),
    client: Optional[str] = None,
    project: Optional[str] = None,
    file_type: Optional[str] = None,
    disk_id: Optional[int] = None
):
    """Sök efter filer"""
    try:
        print(f"🔍 Searching for: {q}")
        print(f"   Filters - client: {client}, project: {project}, file_type: {file_type}, disk_id: {disk_id}")
        
        results = search_files(
            query=q,
            client=client,
            project=project,
            file_type=file_type,
            disk_id=disk_id,
            limit=per_page
        )
        
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
def get_stats():
    """Hämta systemstatistik"""
    try:
        print("🔍 Fetching system stats...")
        stats = get_system_stats()
        return stats
    except Exception as e:
        print(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Statistik-fel: {str(e)}")

# === PROGRESS TRACKING ===

class ProgressTracker:
    def __init__(self, task_id: str):
        self.task_id = task_id
        
    def update_progress(self, step: str, progress: float, message: str, details: str = ""):
        """Uppdatera progress (synkron version)"""
        progress_data = {
            "task_id": self.task_id,
            "step": step,
            "progress": round(progress, 1),
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        with progress_lock:
            progress_store[self.task_id] = progress_data
        
        print(f"📈 Progress {self.task_id}: {progress}% - {message}")

def import_disk_with_progress(file_data: bytes, filename: str, task_id: str, replace_existing: bool = False):
    """Synkron import med progress tracking och replace-stöd"""
    tracker = ProgressTracker(task_id)
    
    try:
        tracker.update_progress("parsing", 5, "Analyserar JSON-fil...", "Läser filinnehåll")
        
        # Parse JSON
        data = json.loads(file_data.decode('utf-8'))
        
        if 'scan_info' not in data or 'tree' not in data:
            tracker.update_progress("error", 0, "Fel: Ogiltig JSON-struktur", 
                "Förväntar SimpleTreeIndexer format.")
            return {"success": False, "error": "Ogiltig JSON-struktur"}
        
        tracker.update_progress("extracting", 10, "Extraherar fildata...", "Bygger fillista från träd")
        
        # Extrahera data
        scan_info = data['scan_info']
        tree = data['tree']
        statistics = data.get('statistics', {})
        
        # Skapa disk-namn från filnamnet
        base_filename = filename.replace('.json', '')
        safe_disk_name = re.sub(r'[^\w\-_\s]', '_', base_filename)
        
        # *** NY LOGIK: Hantera replace_existing ***
        if replace_existing:
            tracker.update_progress("replacing", 15, "Kontrollerar befintlig disk...", f"Söker efter: {safe_disk_name}")
            
            # Kontrollera om befintlig disk finns
            existing_disk = get_disk_by_name(safe_disk_name)
            if existing_disk:
                tracker.update_progress("deleting", 18, "Tar bort befintlig disk...", 
                    f"Raderar: {safe_disk_name} (ID: {existing_disk.id})")
                
                # Ta bort befintlig disk
                success = delete_disk(safe_disk_name)
                if not success:
                    tracker.update_progress("error", 0, "Kunde inte ta bort befintlig disk", 
                        f"Misslyckades med att radera: {safe_disk_name}")
                    return {"success": False, "error": "Kunde inte ta bort befintlig disk"}
                
                tracker.update_progress("deleted", 22, "Befintlig disk borttagen", 
                    f"Fortsätter med import av: {safe_disk_name}")
            else:
                tracker.update_progress("not_found", 20, "Ingen befintlig disk hittad", 
                    f"Skapar ny disk: {safe_disk_name}")
        else:
            # Originallogik: Kontrollera duplicates och lägg till suffix om nödvändigt
            existing_disk = get_disk_by_name(safe_disk_name)
            if existing_disk:
                delete_disk(safe_disk_name)
                tracker.update_progress("deleting", 18, "Tar bort befintlig disk...", 
                    f"Raderar: {safe_disk_name} (ID: {existing_disk.id})")
        
        tracker.update_progress("preparing", 25, "Förbereder databasimport...", f"Disk namn: {safe_disk_name}")
        
        # Extrahera alla filer
        all_files = extract_all_files_with_paths(tree)
        total_files = len(all_files)
        total_size = sum(f.get('file_size', f.get('size', 0)) for f in all_files)
        scan_date = scan_info.get('scan_date', '')
        
        tracker.update_progress("creating_disk", 30, f"Skapar disk: {safe_disk_name}", 
            f"{total_files} filer att importera ({round(total_size / (1024*1024), 2)} MB)")
        
        # Skapa disk metadata
        disk_metadata = {
            "scan_info": scan_info,
            "statistics": statistics,
            "original_filename": filename,
            "replaced_existing": replace_existing
        }
        
        # Skapa disk
        disk = add_disk(
            name=safe_disk_name,
            disk_metadata=json.dumps(disk_metadata),
            path=f"/uploads/{filename}",
            status="imported"
        )
        
        tracker.update_progress("importing", 35, "Importerar filer...", 
            f"Startar import av {total_files} filer")
        
        # Importera filer med progress
        session = SessionLocal()
        try:
            files_imported = 0
            batch_size = 100
            
            for i, file_info in enumerate(all_files):
                try:
                    file_entry = FileEntry(
                        disk_id=disk.id,
                        name=file_info.get('filename', file_info.get('name', '')),
                        path=file_info.get('file_path', file_info.get('path', '')),
                        size=file_info.get('file_size', file_info.get('size', 0)),
                        file_type=file_info.get('extension', '').lstrip('.') 
                            if file_info.get('extension') else None,
                        client=file_info.get('client'),
                        project=file_info.get('project'),
                        keywords=file_info.get('keywords'),
                        checksum=file_info.get('checksum', ''),
                        mime_type=file_info.get('mime_type', '')
                    )
                    session.add(file_entry)
                    files_imported += 1
                    
                    # Progress updates varje 25:e fil
                    if files_imported % 25 == 0 or files_imported % batch_size == 0:
                        progress = 35 + (files_imported / total_files) * 55  # 35-90%
                        tracker.update_progress(
                            "importing", 
                            progress,
                            f"Importerar filer: {files_imported}/{total_files}",
                            f"{((files_imported/total_files)*100):.1f}% klart"
                        )
                    
                    # Commit i batches för bättre prestanda
                    if files_imported % batch_size == 0:
                        session.commit()
                        
                except Exception as e:
                    print(f"⚠️ Error importing file {file_info.get('filename', file_info.get('name', ''))}: {e}")
                    continue
            
            # Final commit
            session.commit()
            
            tracker.update_progress("directories", 92, "Skapar mappstruktur...", "Populerar directories")
            
            # Skapa directories
            directories_created = populate_directories_for_disk(disk.id)
            
            # Slutresultat
            result = {
                "success": True,
                "disk_id": disk.id,
                "disk_name": safe_disk_name,
                "files_imported": files_imported,
                "directories_created": directories_created,
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024*1024), 2),
                "replaced_existing": replace_existing,
                "message": f"Hårddisk {safe_disk_name} {'ersatt' if replace_existing else 'importerad'} framgångsrikt"
            }
            
            tracker.update_progress("complete", 100, "Import slutförd!", 
                f"Importerade {files_imported} filer")
            
            # Spara slutresultat
            with progress_lock:
                progress_store[task_id]["result"] = result
            
            return result
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        tracker.update_progress("error", 0, f"Fel vid import: {str(e)}", "")
        return {"success": False, "error": str(e)}

# === UPLOAD ENDPOINTS ===

@app.post("/upload/check-duplicate")
def check_duplicate(file: UploadFile = File(...)):
    """Kontrollera om en disk redan finns baserat på filnamn"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Endast JSON-filer tillåtna")
    
    try:
        # Skapa disk-namn från filnamnet (samma logik som i upload)
        base_filename = file.filename.replace('.json', '')
        safe_disk_name = re.sub(r'[^\w\-_\s]', '_', base_filename)
        
        # Kolla om disk redan finns
        existing_disk = get_disk_by_name(safe_disk_name)
        
        if existing_disk:
            return {
                "duplicate_found": True,
                "existing_disk": {
                    "id": existing_disk.id,
                    "name": existing_disk.name,
                    "created_at": existing_disk.created_at.isoformat() if existing_disk.created_at else None,
                    "status": existing_disk.status
                },
                "suggested_name": safe_disk_name,
                "message": f"En disk med namnet '{safe_disk_name}' finns redan"
            }
        else:
            return {
                "duplicate_found": False,
                "suggested_name": safe_disk_name,
                "message": "Ingen duplicate hittad, säker att ladda upp"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kunde inte kontrollera duplicate: {str(e)}")

@app.post("/upload/json-index-async")
def upload_json_index_async(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    replace_existing: bool = False  # Ny parameter
):
    """Async upload endpoint med progress tracking"""
    
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Endast JSON-filer tillåtna")
    
    # Generera unique task ID
    task_id = str(uuid.uuid4())
    
    # Läs fildata synkront (måste göras här för att få access till filen)
    file_data = file.file.read()
    
    # Starta background task MED replace_existing parameter
    background_tasks.add_task(
        import_disk_with_progress, 
        file_data, 
        file.filename, 
        task_id, 
        replace_existing  # Skicka vidare parametern
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Import startad",
        "progress_url": f"/upload/progress/{task_id}",
        "replace_existing": replace_existing
    }

@app.get("/upload/progress/{task_id}")
def get_upload_progress_stream(task_id: str):
    """Server-Sent Events för progress"""
    
    async def event_stream():
        # Skicka initial heartbeat
        yield "data: {\"status\": \"connected\"}\n\n"
        
        last_progress = -1
        timeout_count = 0
        max_timeout = 120  # 2 minuters timeout
        
        while timeout_count < max_timeout:
            with progress_lock:
                if task_id in progress_store:
                    current_data = progress_store[task_id].copy()
                    current_progress = current_data.get("progress", 0)
                    
                    # Skicka bara om progress har ändrats
                    if current_progress != last_progress:
                        yield f"data: {json.dumps(current_data)}\n\n"
                        last_progress = current_progress
                        timeout_count = 0  # Reset timeout
                        
                        # Avsluta om färdig eller fel
                        if current_data.get("step") in ["complete", "error"]:
                            yield f"data: {json.dumps({'status': 'finished'})}\n\n"
                            break
                    else:
                        # Skicka heartbeat varje 10:e sekund
                        if timeout_count % 10 == 0:
                            yield f"data: {json.dumps({'status': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                        timeout_count += 1
                else:
                    # Task finns inte än, skicka heartbeat
                    if timeout_count % 5 == 0:
                        yield f"data: {json.dumps({'status': 'waiting', 'message': 'Väntar på task...'})}\n\n"
                    timeout_count += 1
            
            await asyncio.sleep(1)  # Kolla varje sekund
        
        # Timeout - skicka avslutning
        yield f"data: {json.dumps({'status': 'timeout', 'message': 'Timeout efter 2 minuter'})}\n\n"
    
    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "X-Accel-Buffering": "no",
        }
    )

@app.get("/upload/status/{task_id}")
def get_upload_status(task_id: str):
    """Hämta status för en upload-task"""
    with progress_lock:
        if task_id in progress_store:
            return progress_store[task_id]
        else:
            raise HTTPException(status_code=404, detail="Task inte hittad")

@app.post("/upload/json-index")
def upload_json_index(file: UploadFile = File(...)):
    """Ladda upp och importera JSON-index från SimpleTreeIndexer (synkron version)"""
    print(f"📤 Started processing: {file.filename}")
    
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Endast JSON-filer tillåtna")
    
    try:
        # Läs JSON-innehåll
        print(f"📖 Reading JSON content from {file.filename}")
        content = file.file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Validera JSON-struktur
        if 'scan_info' not in data or 'tree' not in data:
            raise HTTPException(status_code=400, detail="Ogiltig JSON-struktur. Förväntar SimpleTreeIndexer format.")
        
        # Extrahera metadata
        scan_info = data['scan_info']
        tree = data['tree']
        statistics = data.get('statistics', {})
        
        # Skapa disk-namn från filnamnet
        base_filename = file.filename.replace('.json', '')
        safe_disk_name = re.sub(r'[^\w\-_\s]', '_', base_filename)
        
        # Kontrollera om disk redan finns
        existing_disk = get_disk_by_name(safe_disk_name)
        if existing_disk:
            counter = 1
            while True:
                new_disk_name = f"{safe_disk_name}_{counter}"
                if not get_disk_by_name(new_disk_name):
                    safe_disk_name = new_disk_name
                    break
                counter += 1
        
        # Beräkna statistik
        print(f"📊 Extracting file data from tree structure...")
        all_files = extract_all_files_with_paths(tree)
        total_files = len(all_files)
        total_size = sum(f.get('file_size', f.get('size', 0)) for f in all_files)
        scan_date = scan_info.get('scan_date', '')
        
        print(f"💿 Creating disk: {safe_disk_name} with {total_files} files")
        
        # Skapa disk metadata
        disk_metadata = {
            "scan_info": scan_info,
            "statistics": statistics,
            "original_filename": file.filename
        }
        
        # Lägg till disk i databasen
        disk = add_disk(
            name=safe_disk_name,
            disk_metadata=json.dumps(disk_metadata),
            path=f"/uploads/{file.filename}",
            status="imported"
        )
        
        # Importera filer med progress logging
        print(f"📈 Starting database import: {total_files} files to process")
        session = SessionLocal()
        try:
            files_imported = 0
            batch_size = 100  # Commit i batches för bättre prestanda
            
            for i, file_info in enumerate(all_files):
                try:
                    file_entry = FileEntry(
                        disk_id=disk.id,
                        name=file_info.get('filename', file_info.get('name', '')),
                        path=file_info.get('file_path', file_info.get('path', '')),
                        size=file_info.get('file_size', file_info.get('size', 0)),
                        file_type=file_info.get('extension', '').lstrip('.') if file_info.get('extension') else None,
                        checksum=file_info.get('checksum', ''),
                        mime_type=file_info.get('mime_type', '')
                    )
                    session.add(file_entry)
                    files_imported += 1
                    
                    # Progress logging var 500:e fil eller i slutet av batches
                    if (files_imported % 500 == 0) or (files_imported % batch_size == 0):
                        progress_percent = (files_imported / total_files) * 100
                        print(f"📈 Progress: {progress_percent:.1f}% ({files_imported}/{total_files} files)")
                        
                    # Commit i batches för bättre prestanda
                    if files_imported % batch_size == 0:
                        session.commit()
                        
                except Exception as e:
                    print(f"⚠️ Error importing file {file_info.get('filename', file_info.get('name', ''))}: {e}")
                    continue
            
            # Final commit
            session.commit()
            
            # Populera directories-tabellen
            print(f"📁 Building directories structure...")
            directories_created = populate_directories_for_disk(disk.id)
            print(f"✅ Created {directories_created} directory entries")
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
        
        print(f"✅ Completed processing {file.filename}: {files_imported} files imported, {directories_created} directories created")
        
        return {
            "success": True,
            "disk_id": disk.id,
            "disk_name": safe_disk_name,
            "files_imported": files_imported,
            "directories_created": directories_created,
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024*1024), 2),
            "message": f"Hårddisk {safe_disk_name} importerad framgångsrikt"
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Ogiltig JSON-fil")
    except Exception as e:
        print(f"❌ Import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import-fel: {str(e)}")

@app.delete("/disks/{disk_name}")
def delete_disk_endpoint(disk_name: str):
    """Ta bort en disk"""
    try:
        success = delete_disk(disk_name)
        if success:
            return {"success": True, "message": "Disk raderad"}
        raise HTTPException(status_code=404, detail="Disk ej hittad")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kunde inte radera disk: {str(e)}")

# === DEBUG ENDPOINTS ===

@app.get("/debug/disk/{disk_identifier}")
def debug_disk_data(disk_identifier: str):
    """Debug-endpoint för att se disk-data"""
    try:
        # Hitta disk
        disk = None
        try:
            disk_id_int = int(disk_identifier)
            disk = get_disk_by_id(disk_id_int)
        except ValueError:
            disk = get_disk_by_name(disk_identifier)
        
        if not disk:
            raise HTTPException(status_code=404, detail="Disk not found")

        session = SessionLocal()
        try:
            # Files count och sample
            files_count = session.query(FileEntry).filter(FileEntry.disk_id == disk.id).count()
            
            sample_files = session.query(FileEntry).filter(FileEntry.disk_id == disk.id).order_by(FileEntry.path, FileEntry.name).limit(10).all()
            
            # Directories count och sample
            directories_count = session.query(DirectoryEntry).filter(DirectoryEntry.disk_id == disk.id).count()
            
            sample_directories = session.query(DirectoryEntry).filter(DirectoryEntry.disk_id == disk.id).limit(10).all()
            
            # Unique file paths för analys
            unique_paths_result = session.query(FileEntry.path).filter(
                FileEntry.disk_id == disk.id,
                FileEntry.path.isnot(None),
                FileEntry.path != ''
            ).distinct().order_by(FileEntry.path).limit(20).all()
            
            unique_paths = [row[0] for row in unique_paths_result]
            
            return {
                "disk_id": disk.id,
                "disk_info": {
                    'id': disk.id,
                    'name': disk.name,
                    'status': disk.status,
                    'created_at': disk.created_at.isoformat() if disk.created_at else None,
                    'metadata_preview': disk.disk_metadata[:500] if disk.disk_metadata else None
                },
                "files_count": files_count,
                "directories_count": directories_count,
                "sample_files": [
                    {"filename": f.name, "file_path": f.path, "file_size": f.size} 
                    for f in sample_files
                ],
                "sample_directories": [
                    {"directory_path": d.path} 
                    for d in sample_directories
                ],
                "unique_file_paths": unique_paths
            }
        finally:
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/populate-directories/{disk_identifier}")
def debug_populate_directories(disk_identifier: str):
    """Debug-endpoint för att manuellt populera directories för en disk"""
    try:
        # Hitta disk
        disk = None
        try:
            disk_id_int = int(disk_identifier)
            disk = get_disk_by_id(disk_id_int)
        except ValueError:
            disk = get_disk_by_name(disk_identifier)
        
        if not disk:
            raise HTTPException(status_code=404, detail="Disk not found")
        
        # Populera directories
        directories_created = populate_directories_for_disk(disk.id)
        
        return {
            "success": True,
            "disk_id": disk.id,
            "directories_created": directories_created,
            "message": f"Populated {directories_created} directories for disk {disk_identifier}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Cold Storage API (PostgreSQL)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)