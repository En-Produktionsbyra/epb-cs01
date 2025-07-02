import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, BigInteger
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
from typing import List, Dict, Optional

# === Konfiguration ===
DB_URL = os.getenv("DB_URL", "postgresql://cold_user:cold_password@localhost:5432/cold_storage")
engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# === Modeller ===
class DiskIndex(Base):
    __tablename__ = "disk_index"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    disk_metadata = Column(Text)
    path = Column(String(512))
    status = Column(String(64), default="imported")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FileEntry(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    disk_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255))
    path = Column(String(1024))
    size = Column(BigInteger)  # Ändrat från Integer till BigInteger för stora filer
    client = Column(String(255))
    project = Column(String(255))
    file_type = Column(String(64))
    keywords = Column(Text)
    checksum = Column(String(128))
    mime_type = Column(String(128))

class DirectoryEntry(Base):
    __tablename__ = "directories"
    id = Column(Integer, primary_key=True, index=True)
    disk_id = Column(Integer, nullable=False, index=True)
    path = Column(String(1024), nullable=False)

# === Init ===
def init_db():
    Base.metadata.create_all(bind=engine)

# === Sessionshantering ===
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Utility functions ===
def format_file_size(size_bytes: int) -> str:
    """Formatera filstorlek"""
    if not size_bytes:
        return "0 B"
    if size_bytes > 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    elif size_bytes > 1024**2:
        return f"{size_bytes / (1024**2):.2f} MB"
    elif size_bytes > 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} B"

def get_file_icon(file_type: str) -> str:
    """Hämta ikon för filtyp"""
    icons = {
        'image': '🖼️',
        'video': '🎬',
        'audio': '🎵',
        'document': '📄',
        'archive': '📦',
        'other': '📄'
    }
    return icons.get(file_type, '📄')

# === CRUD Diskar ===
def add_disk(name, disk_metadata, path, status="imported"):
    session = SessionLocal()
    try:
        disk = DiskIndex(name=name, disk_metadata=disk_metadata, path=path, status=status)
        session.add(disk)
        session.commit()
        session.refresh(disk)  # För att få ID
        return disk
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Kunde inte lägga till disk: {e}")
    finally:
        session.close()

def get_disk_by_id(disk_id):
    session = SessionLocal()
    try:
        return session.query(DiskIndex).filter(DiskIndex.id == disk_id).first()
    finally:
        session.close()

def get_disk_by_name(name):
    session = SessionLocal()
    try:
        return session.query(DiskIndex).filter(DiskIndex.name == name).first()
    finally:
        session.close()

def get_all_disks():
    """Hämta alla hårddiskar med statistik"""
    session = SessionLocal()
    try:
        result = session.query(DiskIndex).order_by(DiskIndex.created_at.desc()).all()
        
        disks = []
        for disk in result:
            # Räkna filer för denna disk
            file_count = session.query(FileEntry).filter(FileEntry.disk_id == disk.id).count()
            
            # Räkna total storlek
            total_size_result = session.query(func.sum(FileEntry.size)).filter(FileEntry.disk_id == disk.id).scalar()
            total_size = total_size_result or 0
            
            # Räkna filer per typ
            image_count = session.query(FileEntry).filter(
                FileEntry.disk_id == disk.id, 
                FileEntry.file_type.in_(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'])
            ).count()
            
            video_count = session.query(FileEntry).filter(
                FileEntry.disk_id == disk.id,
                FileEntry.file_type.in_(['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm'])
            ).count()
            
            audio_count = session.query(FileEntry).filter(
                FileEntry.disk_id == disk.id,
                FileEntry.file_type.in_(['mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a'])
            ).count()
            
            document_count = session.query(FileEntry).filter(
                FileEntry.disk_id == disk.id,
                FileEntry.file_type.in_(['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'])
            ).count()
            
            disk_data = {
                'id': disk.id,
                'name': disk.name,
                'disk_metadata': disk.disk_metadata,
                'path': disk.path,
                'status': disk.status,
                'created_at': disk.created_at.isoformat() if disk.created_at else None,
                'actual_file_count': file_count,
                'actual_total_size': total_size,
                'size_formatted': format_file_size(total_size),
                'image_count': image_count,
                'video_count': video_count,
                'audio_count': audio_count,
                'document_count': document_count
            }
            disks.append(disk_data)
        
        return disks
    finally:
        session.close()

def delete_disk(name):
    session = SessionLocal()
    try:
        disk = session.query(DiskIndex).filter(DiskIndex.name == name).first()
        if disk:
            session.query(FileEntry).filter(FileEntry.disk_id == disk.id).delete()
            session.query(DirectoryEntry).filter(DirectoryEntry.disk_id == disk.id).delete()
            session.delete(disk)
            session.commit()
            return True
        return False
    finally:
        session.close()

# === Filer & kataloger ===
def get_files_by_disk(disk_id, path=None, skip=0, limit=100):
    session = SessionLocal()
    try:
        query = session.query(FileEntry).filter(FileEntry.disk_id == disk_id)
        if path:
            query = query.filter(FileEntry.path == path)
        files = query.offset(skip).limit(limit).all()
        
        result = []
        for file in files:
            result.append({
                'id': file.id,
                'name': file.name,
                'path': file.path,
                'size': file.size,
                'file_type': file.file_type,
                'client': file.client,
                'project': file.project,
                'keywords': file.keywords,
                'checksum': file.checksum,
                'mime_type': file.mime_type
            })
        return result
    finally:
        session.close()

def get_directories(disk_id, parent_path=None):
    session = SessionLocal()
    try:
        # Om parent_path är None eller tom, hämta root-level directories
        if parent_path is None or parent_path == "":
            # Hämta alla unika första nivå-mappar
            file_paths = session.query(FileEntry.path).filter(
                FileEntry.disk_id == disk_id,
                FileEntry.path.isnot(None),
                FileEntry.path != ''
            ).distinct().all()
            
            # Extrahera första nivån av varje path
            root_dirs = set()
            for (path,) in file_paths:
                if path and '/' in path:
                    root_dir = path.split('/')[0]
                    root_dirs.add(root_dir)
                elif path:
                    root_dirs.add(path)
            
            result = []
            for dir_name in sorted(root_dirs):
                # Räkna filer i denna mapp
                file_count = session.query(FileEntry).filter(
                    FileEntry.disk_id == disk_id,
                    FileEntry.path == dir_name
                ).count()
                
                # Räkna undermappar
                subdirectory_count = session.query(FileEntry.path).filter(
                    FileEntry.disk_id == disk_id,
                    FileEntry.path.like(f"{dir_name}/%")
                ).distinct().count()
                
                result.append({
                    'name': dir_name,
                    'path': dir_name,
                    'file_count': file_count,
                    'subdirectory_count': subdirectory_count,
                    'type': 'directory'
                })
            
            return result
        else:
            # Hämta subdirectories för en specifik parent_path
            file_paths = session.query(FileEntry.path).filter(
                FileEntry.disk_id == disk_id,
                FileEntry.path.like(f"{parent_path}/%"),
                FileEntry.path != parent_path
            ).distinct().all()
            
            # Extrahera nästa nivå av directories
            subdirs = set()
            for (path,) in file_paths:
                if path and path.startswith(parent_path + "/"):
                    relative_path = path[len(parent_path) + 1:]
                    if '/' in relative_path:
                        next_dir = relative_path.split('/')[0]
                        subdirs.add(f"{parent_path}/{next_dir}")
                    
            result = []
            for dir_path in sorted(subdirs):
                dir_name = dir_path.split('/')[-1]
                
                # Räkna filer i denna mapp
                file_count = session.query(FileEntry).filter(
                    FileEntry.disk_id == disk_id,
                    FileEntry.path == dir_path
                ).count()
                
                # Räkna undermappar
                subdirectory_count = session.query(FileEntry.path).filter(
                    FileEntry.disk_id == disk_id,
                    FileEntry.path.like(f"{dir_path}/%")
                ).distinct().count()
                
                result.append({
                    'name': dir_name,
                    'path': dir_path,
                    'file_count': file_count,
                    'subdirectory_count': subdirectory_count,
                    'type': 'directory'
                })
            
            return result
    finally:
        session.close()

def get_files_in_directory(disk_id, dir_path):
    session = SessionLocal()
    try:
        # Om dir_path är tom eller None, hämta filer i root
        if not dir_path or dir_path == "":
            files = session.query(FileEntry).filter(
                FileEntry.disk_id == disk_id,
                func.coalesce(FileEntry.path, '') == ''
            ).all()
        else:
            files = session.query(FileEntry).filter(
                FileEntry.disk_id == disk_id, 
                FileEntry.path == dir_path
            ).all()
        
        result = []
        for file in files:
            result.append({
                'name': file.name,
                'size': file.size,
                'file_type': file.file_type,
                'client': file.client,
                'project': file.project,
                'type': 'file'
            })
        return result
    finally:
        session.close()

def search_files(query, client=None, project=None, file_type=None, disk_id=None, limit=100):
    session = SessionLocal()
    try:
        q = session.query(FileEntry)
        if disk_id:
            q = q.filter(FileEntry.disk_id == disk_id)
        if query:
            q = q.filter(FileEntry.name.ilike(f"%{query}%"))
        if client:
            q = q.filter(FileEntry.client.ilike(f"%{client}%"))
        if project:
            q = q.filter(FileEntry.project.ilike(f"%{project}%"))
        if file_type:
            q = q.filter(FileEntry.file_type == file_type)
        
        files = q.limit(limit).all()
        
        result = []
        for file in files:
            result.append({
                'id': file.id,
                'name': file.name,
                'filename': file.name,  # Alias for compatibility
                'path': file.path,
                'file_path': file.path,  # Alias for compatibility
                'size': file.size,
                'file_size': file.size,  # Alias for compatibility
                'file_type': file.file_type,
                'client': file.client,
                'project': file.project,
                'keywords': file.keywords,
                'checksum': file.checksum,
                'mime_type': file.mime_type,
                'size_formatted': format_file_size(file.size or 0),
                'icon': get_file_icon(file.file_type or 'other')
            })
        return result
    finally:
        session.close()

def get_system_stats():
    """Hämta systemstatistik"""
    session = SessionLocal()
    try:
        total_disks = session.query(DiskIndex).count()
        total_files = session.query(FileEntry).count()
        total_dirs = session.query(DirectoryEntry).count()
        
        # Räkna total storlek
        total_size_result = session.query(func.sum(FileEntry.size)).scalar()
        total_size = total_size_result or 0
        
        # Räkna filer per typ
        image_count = session.query(FileEntry).filter(
            FileEntry.file_type.in_(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'])
        ).count()
        
        video_count = session.query(FileEntry).filter(
            FileEntry.file_type.in_(['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm'])
        ).count()
        
        audio_count = session.query(FileEntry).filter(
            FileEntry.file_type.in_(['mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a'])
        ).count()
        
        document_count = session.query(FileEntry).filter(
            FileEntry.file_type.in_(['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'])
        ).count()
        
        archive_count = session.query(FileEntry).filter(
            FileEntry.file_type.in_(['zip', 'rar', '7z', 'tar', 'gz', 'bz2'])
        ).count()
        
        # Räkna unika klienter och projekt
        total_clients = session.query(FileEntry.client).filter(
            FileEntry.client.isnot(None), 
            FileEntry.client != ''
        ).distinct().count()
        
        total_projects = session.query(FileEntry.project).filter(
            FileEntry.project.isnot(None), 
            FileEntry.project != ''
        ).distinct().count()
        
        return {
            "disks": total_disks,
            "files": total_files,
            "directories": total_dirs,
            "total_disks": total_disks,
            "total_files": total_files,
            "total_size": total_size,
            "size_formatted": format_file_size(total_size),
            "total_images": image_count,
            "total_videos": video_count,
            "total_audio": audio_count,
            "total_documents": document_count,
            "total_archives": archive_count,
            "total_clients": total_clients,
            "total_projects": total_projects
        }
    finally:
        session.close()

def populate_directories_for_disk(disk_id):
    """Populera directories för en specifik disk baserat på files-tabellen"""
    session = SessionLocal()
    try:
        # Hämta alla unika directory paths för denna disk
        file_paths_result = session.query(FileEntry.path).filter(
            FileEntry.disk_id == disk_id,
            FileEntry.path.isnot(None),
            FileEntry.path != ''
        ).distinct().order_by(FileEntry.path).all()
        
        file_paths = [row[0] for row in file_paths_result]
        
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
                
                directories.add(current_path)
        
        # Rensa befintliga directories
        session.query(DirectoryEntry).filter(DirectoryEntry.disk_id == disk_id).delete()
        
        # Spara directories i databasen
        directories_created = 0
        
        for directory_path in directories:
            directory_entry = DirectoryEntry(
                disk_id=disk_id,
                path=directory_path
            )
            session.add(directory_entry)
            directories_created += 1
        
        session.commit()
        return directories_created
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def extract_all_files(tree):
    """Extract a flat list of file objects from a nested JSON tree."""
    files = []

    def recurse(node, parent_path=""):
        if isinstance(node, dict):
            if 'name' in node and node.get('type') == 'file':
                files.append(node)
            if 'children' in node:
                for child in node['children']:
                    recurse(child, parent_path + '/' + node.get('name', ''))
        elif isinstance(node, list):
            for item in node:
                recurse(item, parent_path)

    recurse(tree)
    return files

def extract_all_files_with_paths(tree_node, root_path="", current_relative_path=""):
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

def get_disk_info(disk_id: int) -> Optional[Dict]:
    """Hämta information om specifik hårddisk med utökad statistik"""
    session = SessionLocal()
    try:
        # Hämta hårddisk-info
        disk = session.query(DiskIndex).filter(DiskIndex.id == disk_id).first()
        
        if not disk:
            return None
        
        # Hämta filstatistik
        stats = session.query(
            func.count().label('total_files'),
            func.sum(FileEntry.size).label('total_size'),
            func.count().filter(FileEntry.file_type.in_(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'])).label('image_count'),
            func.count().filter(FileEntry.file_type.in_(['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm'])).label('video_count'),
            func.count().filter(FileEntry.file_type.in_(['mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a'])).label('audio_count'),
            func.count().filter(FileEntry.file_type.in_(['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'])).label('document_count'),
            func.count().filter(FileEntry.file_type.in_(['zip', 'rar', '7z', 'tar', 'gz', 'bz2'])).label('archive_count')
        ).filter(FileEntry.disk_id == disk_id).first()
        
        # Hämta topp-kunder
        top_clients = session.query(
            FileEntry.client,
            func.count().label('file_count')
        ).filter(
            FileEntry.disk_id == disk_id,
            FileEntry.client.isnot(None),
            FileEntry.client != ''
        ).group_by(FileEntry.client).order_by(func.count().desc()).limit(10).all()
        
        # Hämta topp-projekt
        top_projects = session.query(
            FileEntry.project,
            func.count().label('file_count')
        ).filter(
            FileEntry.disk_id == disk_id,
            FileEntry.project.isnot(None),
            FileEntry.project != ''
        ).group_by(FileEntry.project).order_by(func.count().desc()).limit(10).all()
        
        disk_data = {
            'id': disk.id,
            'name': disk.name,
            'disk_metadata': disk.disk_metadata,
            'path': disk.path,
            'status': disk.status,
            'created_at': disk.created_at.isoformat() if disk.created_at else None,
            'total_files': stats.total_files or 0,
            'total_size': stats.total_size or 0,
            'size_formatted': format_file_size(stats.total_size or 0),
            'image_count': stats.image_count or 0,
            'video_count': stats.video_count or 0,
            'audio_count': stats.audio_count or 0,
            'document_count': stats.document_count or 0,
            'archive_count': stats.archive_count or 0,
            'top_clients': [{'client': c[0], 'file_count': c[1]} for c in top_clients],
            'top_projects': [{'project': p[0], 'file_count': p[1]} for p in top_projects]
        }
        
        return disk_data
    finally:
        session.close()

# === Database Manager Class (för kompatibilitet med gamla koden) ===
class DatabaseManager:
    """Kompatibilitetsklass för gamla SQLite-koden"""
    
    def __init__(self, db_path: str = None):
        # db_path ignoreras för PostgreSQL, men behålls för kompatibilitet
        pass
    
    def get_connection(self):
        """Returnera en SQLAlchemy session (för kompatibilitet)"""
        return SessionLocal()
    
    def format_file_size(self, size_bytes: int) -> str:
        """Formatera filstorlek"""
        return format_file_size(size_bytes)
    
    def get_file_icon(self, file_type: str) -> str:
        """Hämta ikon för filtyp"""
        return get_file_icon(file_type)
    
    def search_files(self, query: str = '', disk_id: str = '', 
                    file_type: str = '', client: str = '', project: str = '',
                    limit: int = 100) -> List[Dict]:
        """Sök efter filer"""
        session = SessionLocal()
        try:
            # Konvertera disk_id från string till int om nödvändigt
            disk_id_int = None
            if disk_id and disk_id.strip():
                try:
                    disk_id_int = int(disk_id)
                except ValueError:
                    pass
            
            q = session.query(FileEntry)
            if disk_id_int:
                q = q.filter(FileEntry.disk_id == disk_id_int)
            if query:
                q = q.filter(FileEntry.name.ilike(f"%{query}%"))
            if client:
                q = q.filter(FileEntry.client.ilike(f"%{client}%"))
            if project:
                q = q.filter(FileEntry.project.ilike(f"%{project}%"))
            if file_type:
                q = q.filter(FileEntry.file_type == file_type)
            
            files = q.limit(limit).all()
            
            result = []
            for file in files:
                result.append({
                    'id': file.id,
                    'name': file.name,
                    'filename': file.name,
                    'path': file.path,
                    'file_path': file.path,
                    'size': file.size,
                    'file_size': file.size,
                    'file_type': file.file_type,
                    'client': file.client,
                    'project': file.project,
                    'keywords': file.keywords,
                    'checksum': file.checksum,
                    'mime_type': file.mime_type,
                    'size_formatted': format_file_size(file.size or 0),
                    'icon': get_file_icon(file.file_type or 'other')
                })
            return result
        finally:
            session.close()
    
    def get_all_disks(self) -> List[Dict]:
        """Hämta alla hårddiskar"""
        return get_all_disks()
    
    def get_disk_info(self, disk_id: str) -> Optional[Dict]:
        """Hämta information om specifik hårddisk"""
        try:
            disk_id_int = int(disk_id)
            return get_disk_info(disk_id_int)
        except ValueError:
            return None
    
    def get_system_stats(self) -> Dict:
        """Hämta systemstatistik"""
        return get_system_stats()