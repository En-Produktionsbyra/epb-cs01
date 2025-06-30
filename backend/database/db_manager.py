"""
Databas Manager för Cold Storage
Med file browser funktionalitet
"""

import sqlite3
import os
from typing import List, Dict, Tuple, Optional

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def get_connection(self):
        """Skapa databas-anslutning"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def format_file_size(self, size_bytes: int) -> str:
        """Formatera filstorlek"""
        if size_bytes > 1024**3:
            return f"{size_bytes / (1024**3):.2f} GB"
        elif size_bytes > 1024**2:
            return f"{size_bytes / (1024**2):.2f} MB"
        elif size_bytes > 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} B"
    
    def get_file_icon(self, file_type: str) -> str:
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
    
    def search_files(self, query: str = '', disk_id: str = '', 
                    file_type: str = '', client: str = '', project: str = '',
                    limit: int = 100) -> List[Dict]:
        """Sök efter filer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = '''
            SELECT f.*, d.disk_name 
            FROM files f 
            JOIN disks d ON f.disk_id = d.disk_id 
            WHERE d.status = 'active'
        '''
        params = []
        
        if query:
            sql += ' AND (f.filename LIKE ? OR f.keywords LIKE ? OR f.client LIKE ? OR f.project LIKE ?)'
            like_query = f'%{query}%'
            params.extend([like_query, like_query, like_query, like_query])
        
        if disk_id:
            sql += ' AND f.disk_id = ?'
            params.append(disk_id)
        
        if file_type:
            sql += ' AND f.file_type = ?'
            params.append(file_type)
        
        if client:
            sql += ' AND f.client LIKE ?'
            params.append(f'%{client}%')
        
        if project:
            sql += ' AND f.project LIKE ?'
            params.append(f'%{project}%')
        
        sql += ' ORDER BY f.filename LIMIT ?'
        params.append(limit)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        
        # Formatera resultat
        files = []
        for row in results:
            file_data = dict(row)
            file_data['size_formatted'] = self.format_file_size(file_data.get('file_size', 0))
            file_data['icon'] = self.get_file_icon(file_data.get('file_type', 'other'))
            files.append(file_data)
        
        return files
    
    def get_all_disks(self) -> List[Dict]:
        """Hämta alla hårddiskar"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.*, 
                   COUNT(f.id) as actual_file_count,
                   SUM(f.file_size) as actual_total_size,
                   COUNT(CASE WHEN f.file_type = 'image' THEN 1 END) as image_count,
                   COUNT(CASE WHEN f.file_type = 'video' THEN 1 END) as video_count,
                   COUNT(CASE WHEN f.file_type = 'audio' THEN 1 END) as audio_count,
                   COUNT(CASE WHEN f.file_type = 'document' THEN 1 END) as document_count
            FROM disks d 
            LEFT JOIN files f ON d.disk_id = f.disk_id 
            WHERE d.status = 'active'
            GROUP BY d.disk_id 
            ORDER BY d.disk_id
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        disks = []
        for row in results:
            disk_data = dict(row)
            total_size = disk_data.get('actual_total_size', 0) or 0
            disk_data['size_formatted'] = self.format_file_size(total_size)
            disks.append(disk_data)
        
        return disks
    
    def get_disk_info(self, disk_id: str) -> Optional[Dict]:
        """Hämta information om specifik hårddisk"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Hämta hårddisk-info
        cursor.execute('SELECT * FROM disks WHERE disk_id = ? AND status = "active"', (disk_id,))
        disk = cursor.fetchone()
        
        if not disk:
            conn.close()
            return None
        
        # Hämta filstatistik
        cursor.execute('''
            SELECT 
                COUNT(*) as total_files,
                SUM(file_size) as total_size,
                COUNT(CASE WHEN file_type = 'image' THEN 1 END) as image_count,
                COUNT(CASE WHEN file_type = 'video' THEN 1 END) as video_count,
                COUNT(CASE WHEN file_type = 'audio' THEN 1 END) as audio_count,
                COUNT(CASE WHEN file_type = 'document' THEN 1 END) as document_count,
                COUNT(CASE WHEN file_type = 'archive' THEN 1 END) as archive_count,
                COUNT(CASE WHEN file_type = 'other' THEN 1 END) as other_count
            FROM files WHERE disk_id = ?
        ''', (disk_id,))
        
        stats = cursor.fetchone()
        
        # Hämta topp-kunder
        cursor.execute('''
            SELECT client, COUNT(*) as file_count 
            FROM files 
            WHERE disk_id = ? AND client IS NOT NULL AND client != ''
            GROUP BY client 
            ORDER BY file_count DESC 
            LIMIT 10
        ''', (disk_id,))
        top_clients = [dict(row) for row in cursor.fetchall()]
        
        # Hämta topp-projekt
        cursor.execute('''
            SELECT project, COUNT(*) as file_count 
            FROM files 
            WHERE disk_id = ? AND project IS NOT NULL AND project != ''
            GROUP BY project 
            ORDER BY file_count DESC 
            LIMIT 10
        ''', (disk_id,))
        top_projects = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        disk_data = dict(disk)
        if stats:
            disk_data.update(dict(stats))
        
        # Formatera storlek
        total_size = disk_data.get('total_size', 0) or 0
        disk_data['size_formatted'] = self.format_file_size(total_size)
        disk_data['top_clients'] = top_clients
        disk_data['top_projects'] = top_projects
        
        return disk_data
    
    def get_system_stats(self) -> Dict:
        """Hämta systemstatistik"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT d.disk_id) as total_disks,
                COUNT(f.id) as total_files,
                SUM(f.file_size) as total_size,
                COUNT(CASE WHEN f.file_type = 'image' THEN 1 END) as total_images,
                COUNT(CASE WHEN f.file_type = 'video' THEN 1 END) as total_videos,
                COUNT(CASE WHEN f.file_type = 'audio' THEN 1 END) as total_audio,
                COUNT(CASE WHEN f.file_type = 'document' THEN 1 END) as total_documents,
                COUNT(CASE WHEN f.file_type = 'archive' THEN 1 END) as total_archives,
                COUNT(DISTINCT f.client) as total_clients,
                COUNT(DISTINCT f.project) as total_projects
            FROM disks d 
            LEFT JOIN files f ON d.disk_id = f.disk_id 
            WHERE d.status = 'active'
        ''')
        
        stats = dict(cursor.fetchone())
        conn.close()
        
        # Formatera total storlek
        total_size = stats.get('total_size', 0) or 0
        if total_size > 1024**4:
            stats['size_formatted'] = f"{total_size / (1024**4):.2f} TB"
        elif total_size > 1024**3:
            stats['size_formatted'] = f"{total_size / (1024**3):.2f} GB"
        else:
            stats['size_formatted'] = f"{total_size / (1024**2):.2f} MB"
        
        return stats