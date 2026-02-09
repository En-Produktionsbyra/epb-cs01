#!/usr/bin/env python3
"""
Optimized Tree Indexer för Cold Storage v2 - COMPLETE FIXED VERSION
Skapar JSON-struktur som är perfekt för import till directories-tabellen
ALLA FIXES: Djup-begränsning, Auto-skalad text, Roterad header, Smart kundlista-filtrering
UPDATERAD v3.0.0: KATASYMBOL EDITION - Native 203 DPI för pixel-perfekt skärpa
"""

import os
import json
import argparse
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import re
import sys
import math
from collections import deque

# För QR-kod och label-generering
try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    HAS_LABEL_SUPPORT = True
except ImportError:
    HAS_LABEL_SUPPORT = False
    print("⚠️ För label-generering: pip install qrcode[pil] pillow")

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️ Installera 'tqdm' för progressbar: pip install tqdm")

def get_text_size_global(text, font, draw_obj):
    """Helper för att få text-dimensioner kompatibelt med olika PIL versioner"""
    try:
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return draw_obj.textsize(text, font=font)

def render_wrapped_list(items, full_width, max_height, start_x, start_y, qr_box, draw_obj):
    """
    NY SMART FUNKTION (v2.7.0): Flow layout som 'rappar' texten runt QR-koden.
    
    qr_box: Tuple (x, y, w, h) som definierar området där QR-koden ligger (exkludera detta).
    """
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf", 
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    def load_font(size):
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
        return ImageFont.load_default()

    best_config = None
    
    # QR exclusion zone (left, top, right, bottom)
    # Lägg till padding runt QR-koden så texten inte nuddar den
    qx, qy, qw, qh = qr_box
    qr_padding = 5 # Justerat för 203 DPI (var 20)
    qr_rect = (qx - qr_padding, qy - qr_padding, qx + qw + qr_padding, qy + qh + qr_padding)

    # Funktion för att kontrollera kollision med QR-koden
    def check_collision(slot_rect, exclusion_rect):
        sl, st, sr, sb = slot_rect
        el, et, er, eb = exclusion_rect
        
        # Om slotten är helt till vänster, höger, ovanför eller under exclusion -> INGEN krock
        if sr < el or sl > er or sb < et or st > eb:
            return False
        return True

    # === OPTIMERINGS-LOOP ===
    # Anpassade font-storlekar för 203 DPI (ca 1/4 av 900 DPI)
    # Testar från ca 25px (stort) ner till 8px (läsbart)
    for font_size in range(30, 7, -1):
        font = load_font(font_size)
        
        # Mät radhöjd
        _, text_height = get_text_size_global("Ay", font, draw_obj)
        line_height = text_height + int(font_size * 0.2) # 20% spacing
        
        # Testa kolumnantal (1-2)
        for num_cols in range(1, 3):
            col_width = full_width // num_cols
            padding_x = 5 # Justerat för 203 DPI
            
            # Simulera utplacering
            current_y = start_y
            items_placed = 0
            success = True
            
            # Kopiera item-listan för simulering
            sim_items = list(items)
            
            while sim_items and current_y + line_height <= start_y + max_height:
                # Försök fylla en rad med slots
                row_slots = []
                for c in range(num_cols):
                    slot_x = start_x + (c * col_width)
                    slot_rect = (slot_x, current_y, slot_x + col_width, current_y + line_height)
                    
                    # Kolla om denna slot krockar med QR-koden
                    if not check_collision(slot_rect, qr_rect):
                        row_slots.append((slot_x, current_y))
                
                # Fyll slotsen med items
                for slot in row_slots:
                    if sim_items:
                        sim_items.pop(0)
                        items_placed += 1
                
                current_y += line_height
            
            # Om alla items fick plats
            if not sim_items:
                best_config = {
                    'font': font,
                    'font_size': font_size,
                    'num_cols': num_cols,
                    'line_height': line_height,
                    'col_width': col_width,
                    'padding_x': padding_x
                }
                break # Hittade en config för denna font-storlek, gå vidare (eftersom vi vill ha störst möjliga font)
        
        if best_config:
            break

    # Fallback om inget passar
    if not best_config:
        print("⚠️ Varning: Texten får knappt plats, använder fallback-läge.")
        font_size = 8 # Minsta läsbara vid 203 DPI
        font = load_font(font_size)
        _, text_height = get_text_size_global("Ay", font, draw_obj)
        best_config = {
            'font': font,
            'font_size': font_size,
            'num_cols': 2, # Begränsad till 2 även i fallback
            'line_height': text_height + 2,
            'col_width': full_width // 2,
            'padding_x': 2
        }

    # === RENDERING ===
    print(f"🎨 Vald layout: {best_config['num_cols']} kolumner, textstorlek {best_config['font_size']}px (Wrapped)")
    
    font = best_config['font']
    line_h = best_config['line_height']
    col_w = best_config['col_width']
    pad_x = best_config['padding_x']
    
    current_y = start_y
    item_idx = 0
    
    while item_idx < len(items):
        # Identifiera giltiga slots för denna rad
        row_slots = []
        for c in range(best_config['num_cols']):
            slot_x = start_x + (c * col_w)
            slot_rect = (slot_x, current_y, slot_x + col_w, current_y + line_h)
            
            if not check_collision(slot_rect, qr_rect):
                row_slots.append(slot_x)
        
        # Rita items i slotsen
        for slot_x in row_slots:
            if item_idx >= len(items):
                break
                
            item_text = f"• {items[item_idx]}"
            
            # Truncera text om den är för lång för sin kolumn
            avail_w = col_w - pad_x
            text_w, _ = get_text_size_global(item_text, font, draw_obj)
            
            display_text = item_text
            if text_w > avail_w:
                while text_w > avail_w and len(display_text) > 5:
                    display_text = display_text[:-4] + "..."
                    text_w, _ = get_text_size_global(display_text, font, draw_obj)
            
            draw_obj.text((slot_x, current_y), display_text, fill='black', font=font)
            item_idx += 1
            
        current_y += line_h
        
        # Säkerhetsspärr
        if current_y > start_y + max_height:
            break

class OptimizedTreeIndexer:
    def __init__(self, max_depth=8):
        self.version = "3.0.0"  # Uppdaterad version: Katasymbol Native (203 DPI)
        self.checkpoint_file = None
        self.progress_bar = None
        self.max_depth = max_depth
        
    def determine_file_type(self, extension: str) -> str:
        """Bestäm fil-kategori baserat på extension"""
        if not extension:
            return 'other'
            
        ext = extension.lower().lstrip('.')
        
        # Bilder (inklusive RAW)
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'svg',
                   'cr2', 'cr3', 'nef', 'arw', 'dng', 'iiq', '3fr', 'orf', 'rw2', 'pef']:
            return 'image'
        
        # Video
        elif ext in ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg',
                     'r3d', 'braw', 'mxf', 'prores']:
            return 'video'
        
        # Audio
        elif ext in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'aiff', 'aif', 'm4a']:
            return 'audio'
        
        # Dokument
        elif ext in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'pages', 'ai', 'eps', 'indd', 'psd']:
            return 'document'
        
        # Arkiv
        elif ext in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'dmg', 'iso']:
            return 'archive'
        
        # Kod/Data
        elif ext in ['js', 'jsx', 'ts', 'tsx', 'html', 'css', 'json', 'xml', 'yml', 'yaml', 
                     'py', 'java', 'cpp', 'c', 'h', 'sql']:
            return 'code'
        
        else:
            return 'other'
    
    def _should_exclude_directory(self, dir_path: str, root_path: str, exclude_regexes: List) -> bool:
        """Gemensam logik för om en mapp ska exkluderas"""
        
        # Nivå 0 filtrering - exkludera problematiska root-mappar
        if dir_path == root_path or os.path.dirname(dir_path) == root_path:
            folder_name = os.path.basename(dir_path)
            excluded_root_folders = [
                'Backups.backupdb',
                '.Spotlight-V100', 
                '.TemporaryItems',
                '.Trashes',
                '.fseventsd'
            ]
            if folder_name in excluded_root_folders:
                return True
        
        # Regex-filtrering
        if any(regex.search(dir_path) for regex in exclude_regexes):
            return True
        
        return False
        
    def scan_directory_tree(self, root_path: str, output_file: str = None, 
                           include_extensions: List[str] = None,
                           exclude_patterns: List[str] = None,
                           resume: bool = True,
                           checkpoint_interval: int = 1000) -> Dict:
        """
        Scanna katalogträd optimerat för Cold Storage v2 med djup-begränsning
        """
        
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Sökväg finns inte: {root_path}")
        
        # Setup checkpoint fil
        if output_file:
            self.checkpoint_file = output_file.replace('.json', '_checkpoint.pkl')
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"tree_structure_{timestamp}.json"
            self.checkpoint_file = f"tree_structure_{timestamp}_checkpoint.pkl"
        
        print(f"📁 Optimized Tree Indexer v{self.version}")
        print(f"📂 Skannar: {root_path}")
        print(f"💾 Output: {output_file}")
        print(f"🔄 Checkpoint: {self.checkpoint_file}")
        print(f"📏 Max djup: {self.max_depth} nivåer")
        print(f"⏰ Starttid: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Default file extensions (bred täckning för foto/video-arkiv)
        if include_extensions is None:
            include_extensions = [
                # RAW foto
                '.cr2', '.cr3', '.nef', '.arw', '.dng', '.iiq', '.3fr', '.orf', '.rw2', '.pef',
                # Standard foto
                '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.psd', '.gif', '.bmp', '.webp',
                # Video
                '.mp4', '.mov', '.avi', '.r3d', '.braw', '.mxf', '.mkv', '.wmv', '.m4v',
                # Audio
                '.wav', '.aiff', '.mp3', '.flac', '.aac', '.m4a',
                # Dokument
                '.pdf', '.ai', '.eps', '.indd', '.doc', '.docx'
            ]
        
        # Default exclude patterns
        if exclude_patterns is None:
            exclude_patterns = [
                r'\.DS_Store$',
                r'Thumbs\.db$', 
                r'\.tmp$',
                r'\.temp$',
                r'__MACOSX',
                r'System Volume Information',
                r'\$RECYCLE\.BIN',
                r'\.VolumeIcon'
            ]
        
        # Kompilera exclude patterns
        exclude_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in exclude_patterns]
        
        # Försök återuppta från checkpoint
        if resume and os.path.exists(self.checkpoint_file):
            print(f"🔄 Hittade checkpoint - återupptar scanning...")
            try:
                with open(self.checkpoint_file, 'rb') as f:
                    checkpoint_data = pickle.load(f)
                
                tree_data = checkpoint_data['tree_data']
                processed_paths = checkpoint_data['processed_paths']
                start_time = checkpoint_data['start_time']
                
                print(f"📊 Återupptar från: {len(processed_paths)} processade sökvägar")
                print(f"📄 Redan: {tree_data['statistics']['total_files']} filer, {tree_data['statistics']['total_directories']} mappar")
                
            except Exception as e:
                print(f"⚠️ Kunde inte läsa checkpoint: {e}")
                print("🔄 Startar från början...")
                tree_data, processed_paths, start_time = self._initialize_scan_data(
                    root_path, include_extensions, exclude_patterns
                )
        else:
            tree_data, processed_paths, start_time = self._initialize_scan_data(
                root_path, include_extensions, exclude_patterns
            )
        
        # Utför scanning nivå för nivå
        try:
            self._scan_level_by_level(
                root_path, 
                tree_data, 
                processed_paths,
                include_extensions, 
                exclude_regexes,
                checkpoint_interval
            )
            
        except KeyboardInterrupt:
            print(f"\n⚠️ Avbrutet av användaren - sparar checkpoint...")
            self._save_checkpoint(tree_data, processed_paths, start_time)
            raise
        
        # Slutstatistik
        end_time = datetime.now()
        tree_data['statistics']['scan_duration_seconds'] = (end_time - start_time).total_seconds()
        
        if self.progress_bar:
            self.progress_bar.close()
        
        print(f"\n✅ Scanning slutförd!")
        print(f"📊 Slutstatistik:")
        print(f"   📁 {tree_data['statistics']['total_directories']} mappar")
        print(f"   📄 {tree_data['statistics']['total_files']} filer")
        print(f"   📏 Djup: {tree_data['statistics']['max_depth']} nivåer")
        print(f"   ⏱️  Tid: {tree_data['statistics']['scan_duration_seconds']:.1f} sekunder")
        
        # Visa filtyp-fördelning
        if tree_data['statistics']['file_types']:
            print(f"   📋 Filtyper:")
            sorted_types = sorted(
                tree_data['statistics']['file_types'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            for ftype, count in sorted_types:
                print(f"      {ftype}: {count:,} filer")
        
        # Spara slutresultat
        self._save_tree_data(tree_data, output_file)
        
        return tree_data
    
    def _initialize_scan_data(self, root_path: str, include_extensions: List[str], 
                             exclude_patterns: List[str]) -> Tuple[Dict, set, datetime]:
        """Initialisera scan-data med optimerad struktur"""
        
        tree_data = {
            'scan_info': {
                'root_path': root_path,
                'scan_date': datetime.now().isoformat(),
                'scanner': 'OptimizedTreeIndexer',
                'version': self.version,
                'max_depth': self.max_depth,
                'include_extensions': include_extensions,
                'exclude_patterns': exclude_patterns,
                'optimized_for': 'Cold Storage v2 with directories table'
            },
            'statistics': {
                'total_files': 0,
                'total_directories': 0,
                'file_extensions': {},
                'file_types': {},  # NY: kategoriserade filtyper
                'max_depth': 0,
                'largest_file': {'name': '', 'size': 0},
                'scan_duration_seconds': 0,
                'directory_depth_distribution': {}  # NY: fördelning av djup-nivåer
            },
            'tree': {
                'type': 'directory',
                'name': os.path.basename(root_path) or root_path,
                'path': root_path,
                'relative_path': '',  # NY: relativ sökväg från root
                'parent_path': None,  # NY: förälder-sökväg
                'depth': 0,  # NY: djup-nivå
                'children': {},
                'files': [],
                'metadata': {
                    'depth': 0,
                    'file_count': 0,
                    'subdirectory_count': 0,
                    'total_size': 0  # NY: total storlek i denna mapp
                }
            }
        }
        
        processed_paths = set()
        start_time = datetime.now()
        
        return tree_data, processed_paths, start_time
    
    def _scan_level_by_level(self, root_path: str, tree_data: Dict, processed_paths: set,
                            include_extensions: List[str], exclude_regexes: List,
                            checkpoint_interval: int):
        """
        Scanna katalogträd nivå för nivå med progressbar och djup-begränsning
        """
        
        # Första: räkna totalt antal kataloger för progressbar
        print("🔢 Räknar totalt antal kataloger...")
        total_dirs = self._count_total_directories(root_path, exclude_regexes)
        print(f"📊 Totalt {total_dirs:,} kataloger att processa (max djup: {self.max_depth})")
        
        # Skapa progressbar
        if HAS_TQDM:
            self.progress_bar = tqdm(
                total=total_dirs,
                desc="Scannar kataloger",
                unit="dir",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
            )
        
        # Kö för nivå-för-nivå scanning
        current_level = deque([(root_path, tree_data['tree'], 0, '')])  # (full_path, tree_node, depth, relative_path)
        checkpoint_counter = 0
        
        while current_level:
            next_level = deque()
            
            # Processa alla kataloger på nuvarande nivå
            while current_level:
                dir_path, tree_node, depth, relative_path = current_level.popleft()
                
                # DJUP-BEGRÄNSNING
                if depth > self.max_depth:
                    if HAS_TQDM and self.progress_bar:
                        self.progress_bar.update(1)
                    continue
                
                # Hoppa över om redan processad
                if dir_path in processed_paths:
                    if HAS_TQDM and self.progress_bar:
                        self.progress_bar.update(1)
                    continue
                
                # Hoppa över exkluderade mappar
                if self._should_exclude_directory(dir_path, root_path, exclude_regexes):
                    if HAS_TQDM and self.progress_bar:
                        self.progress_bar.update(1)
                    continue
                
                # Processa denna katalog
                self._process_directory(
                    dir_path, tree_node, depth, relative_path,
                    include_extensions, exclude_regexes,
                    tree_data['statistics'], next_level
                )
                
                processed_paths.add(dir_path)
                checkpoint_counter += 1
                
                # Uppdatera progressbar
                if HAS_TQDM and self.progress_bar:
                    self.progress_bar.set_postfix({
                        'filer': f"{tree_data['statistics']['total_files']:,}",
                        'djup': depth,
                        'typer': len(tree_data['statistics']['file_types'])
                    })
                    self.progress_bar.update(1)
                
                # Spara checkpoint
                if checkpoint_counter >= checkpoint_interval:
                    self._save_checkpoint(tree_data, processed_paths, datetime.now())
                    checkpoint_counter = 0
            
            # Nästa nivå blir nuvarande nivå
            current_level = next_level
    
    def _count_total_directories(self, root_path: str, exclude_regexes: List) -> int:
        """Räkna totalt antal kataloger (för progressbar) med djup-begränsning"""
        
        total = 0
        # Använd en stack med djup-information: (path, depth)
        stack = [(root_path, 0)]
        
        while stack:
            current_path, current_depth = stack.pop()
            
            # DJUP-BEGRÄNSNING
            if current_depth > self.max_depth:
                continue
            
            # Exkludering
            if self._should_exclude_directory(current_path, root_path, exclude_regexes):
                continue
            
            try:
                items = os.listdir(current_path)
                total += 1
                
                # Lägg bara till underkataloger om vi inte är för djupt
                if current_depth < self.max_depth:
                    for item in items:
                        item_path = os.path.join(current_path, item)
                        
                        if self._should_exclude_directory(item_path, root_path, exclude_regexes):
                            continue
                        
                        if os.path.isdir(item_path):
                            stack.append((item_path, current_depth + 1))
                            
            except (PermissionError, OSError):
                total += 1
                continue
        
        return total
    
    def _process_directory(self, dir_path: str, tree_node: Dict, depth: int, relative_path: str,
                          include_extensions: List[str], exclude_regexes: List,
                          statistics: Dict, next_level: deque):
        """
        Processa en enskild katalog med optimerad metadata och djup-begränsning
        """
        
        # DJUP-BEGRÄNSNING
        if depth > self.max_depth:
            return
        
        # Uppdatera max djup och djup-fördelning
        statistics['max_depth'] = max(statistics['max_depth'], depth)
        if depth not in statistics['directory_depth_distribution']:
            statistics['directory_depth_distribution'][depth] = 0
        statistics['directory_depth_distribution'][depth] += 1
        
        try:
            items = os.listdir(dir_path)
        except PermissionError:
            if not HAS_TQDM:
                print(f"⚠️ Ingen åtkomst till: {dir_path}")
            return
        except Exception as e:
            if not HAS_TQDM:
                print(f"❌ Fel vid läsning av {dir_path}: {e}")
            return
        
        # Sortera items
        items.sort()
        
        total_size = 0
        
        for item in items:
            item_path = os.path.join(dir_path, item)
            
            # Kontrollera exclude patterns
            if any(regex.search(item_path) for regex in exclude_regexes):
                continue
            
            if os.path.isdir(item_path):
                # Hoppa över om vi når max djup
                if depth >= self.max_depth:
                    continue
                    
                # Skapa mapp-nod med optimerad struktur
                child_relative_path = f"{relative_path}/{item}" if relative_path else item
                
                child_node = {
                    'type': 'directory',
                    'name': item,
                    'path': item_path,
                    'relative_path': child_relative_path,  # NY: relativ sökväg
                    'parent_path': relative_path if relative_path else None,  # NY: förälder
                    'depth': depth + 1,  # NY: djup-nivå
                    'children': {},
                    'files': [],
                    'metadata': {
                        'depth': depth + 1,
                        'file_count': 0,
                        'subdirectory_count': 0,
                        'total_size': 0
                    }
                }
                
                tree_node['children'][item] = child_node
                tree_node['metadata']['subdirectory_count'] += 1
                statistics['total_directories'] += 1
                
                # Lägg till i nästa nivå
                next_level.append((item_path, child_node, depth + 1, child_relative_path))
                
            elif os.path.isfile(item_path):
                # Processa fil
                file_size = self._process_file(
                    item, item_path, relative_path, include_extensions,
                    tree_node, statistics
                )
                total_size += file_size
        
        # Uppdatera total storlek för denna mapp
        tree_node['metadata']['total_size'] = total_size
    
    def _process_file(self, filename: str, file_path: str, relative_dir_path: str,
                     include_extensions: List[str], tree_node: Dict, 
                     statistics: Dict) -> int:
        """
        Processa en enskild fil med optimerad metadata
        """
        
        file_ext = Path(filename).suffix.lower()
        
        # Kontrollera filextension
        if include_extensions and file_ext not in include_extensions:
            return 0
        
        try:
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            
            # Bestäm filtyp
            file_type = self.determine_file_type(file_ext)
            
            # Uppdatera statistik
            statistics['total_files'] += 1
            tree_node['metadata']['file_count'] += 1
            
            # Extension-statistik
            if file_ext not in statistics['file_extensions']:
                statistics['file_extensions'][file_ext] = 0
            statistics['file_extensions'][file_ext] += 1
            
            # Filtyp-statistik
            if file_type not in statistics['file_types']:
                statistics['file_types'][file_type] = 0
            statistics['file_types'][file_type] += 1
            
            # Största fil
            if file_size > statistics['largest_file']['size']:
                statistics['largest_file'] = {
                    'name': file_path,
                    'size': file_size
                }
            
            # Optimerad fil-info för import
            file_info = {
                'name': filename,
                'path': file_path,
                'relative_path': f"{relative_dir_path}/{filename}" if relative_dir_path else filename,  # NY
                'parent_directory': relative_dir_path,  # NY: föräldermapp
                'extension': file_ext,
                'size': file_size,
                'type': file_type,  # NY: kategoriserad typ
                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            }
            
            tree_node['files'].append(file_info)
            
            return file_size
            
        except (OSError, IOError) as e:
            if not HAS_TQDM:
                print(f"⚠️ Kunde inte läsa fil {file_path}: {e}")
            return 0
    
    def _save_checkpoint(self, tree_data: Dict, processed_paths: set, start_time: datetime):
        """Spara checkpoint för återupptagning"""
        
        checkpoint_data = {
            'tree_data': tree_data,
            'processed_paths': processed_paths,
            'start_time': start_time,
            'checkpoint_time': datetime.now().isoformat()
        }
        
        try:
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            
            if not HAS_TQDM:
                print(f"💾 Checkpoint sparad: {len(processed_paths)} kataloger, {tree_data['statistics']['total_files']} filer")
                
        except Exception as e:
            if not HAS_TQDM:
                print(f"⚠️ Kunde inte spara checkpoint: {e}")
    
    def ask_for_customer_level(self, tree: Dict, max_attempts: int = 4) -> List[str]:
        """
        Interaktivt hitta rätt nivå för kundmappar med KORREKT filtrering
        """
        if not sys.stdin.isatty():
            print("⚠️ Inte en interaktiv terminal - hoppar över kundmapp-detektering")
            return []
        
        def get_folders_at_level(node, current_level, target_level):
            """Hämta alla mappar på en specifik nivå och filtrera systemfiler"""
            if current_level == target_level:
                all_folders = list(node.get('children', {}).keys())
                
                # SYSTEMFILER ATT FILTRERA BORT
                system_folders = {
                    '.fseventsd', 
                    '.Spotlight-V100', 
                    '.TemporaryItems', 
                    '.Trashes',
                    'Backups.backupdb',
                    '.DS_Store',
                    '.VolumeIcon.icns',
                    '.disk_label',
                    '.disk_label_2x',
                    '.hedge-enabled',
                    '__MACOSX',
                    'System Volume Information',
                    '$RECYCLE.BIN',
                    'Thumbs.db'
                }
                
                # Filtrera bort systemfiler och dolda mappar
                filtered_folders = []
                for folder in all_folders:
                    # Hoppa över exakta systemfiler
                    if folder in system_folders:
                        print(f"   🚫 Filtrerar bort systemfil: {folder}")
                        continue
                    
                    # Hoppa över alla dolda filer/mappar (börjar med punkt)
                    if folder.startswith('.'):
                        print(f"   🚫 Filtrerar bort dold mapp: {folder}")
                        continue
                    
                    # Hoppa över mycket korta namn (troligen systemfiler)
                    if len(folder) <= 2:
                        print(f"   🚫 Filtrerar bort kort namn: {folder}")
                        continue
                    
                    # DENNA ÄR FÖRMODLIGEN EN RIKTIG KUNDMAPP
                    filtered_folders.append(folder)
                    print(f"   ✅ Behåller: {folder}")
                
                print(f"📊 Filtrering: {len(all_folders)} totalt → {len(filtered_folders)} efter filtrering")
                return filtered_folders
            
            # För djupare nivåer - rekursiv sökning
            folders = []
            for child in node.get('children', {}).values():
                folders.extend(get_folders_at_level(child, current_level + 1, target_level))
            return folders
        
        print("\n🗂️ KUNDMAPP-DETEKTERING")
        print("Låt oss hitta rätt nivå för dina kundmappar...")
        
        for level in range(max_attempts):
            print(f"\n🔍 Analyserar nivå {level}...")
            folders = get_folders_at_level(tree, 0, level)
            
            if not folders:
                print(f"📁 Nivå {level}: Inga relevanta mappar hittades efter filtrering")
                continue
            
            print(f"\n📁 Nivå {level} innehåller {len(folders)} relevanta mappar:")
            
            # Visa mappar (max 15 för läsbarhet)
            display_folders = folders[:15]
            for i, folder in enumerate(display_folders, 1):
                print(f"   {i:2d}. {folder}")
            
            if len(folders) > 15:
                print(f"   ... och {len(folders) - 15} till")
            
            # Fråga användaren
            while True:
                response = input(f"\n❓ Är nivå {level} din grundnivå för kunder/projekt? (j/n/skip): ").lower().strip()
                
                if response in ['j', 'ja', 'y', 'yes']:
                    print(f"✅ Använder nivå {level} som kundnivå")
                    # SORTERA ALFABETISKT innan returnering
                    sorted_folders = sorted(folders, key=str.lower)
                    print(f"📋 Returnerar {len(sorted_folders)} kundmappar")
                    return sorted_folders
                elif response in ['n', 'nej', 'no']:
                    print(f"➡️ Fortsätter till nästa nivå...")
                    break
                elif response in ['skip', 's']:
                    print(f"⏭️ Hoppar över kundmapp-detektering")
                    return []
                else:
                    print("❌ Svara j (ja), n (nej) eller skip")
        
        print(f"⚠️ Ingen lämplig kundnivå hittades efter {max_attempts} försök")
        return []
    
    def generate_disk_label(self, disk_name: str, tree_data: Dict, output_file: str, safe_name: str) -> str:
        """
        Generera labels med KORREKT auto-skalning och header-layout
        """
        print(f"🏷️ Startar label-generering för: '{disk_name}'")
        
        if not HAS_LABEL_SUPPORT:
            print(f"❌ QR-kod/PIL moduler saknas")
            return None
        
        try:
            import qrcode
            from PIL import Image, ImageDraw, ImageFont
            print("✅ QR-kod och PIL moduler laddade")
        except ImportError as e:
            print(f"❌ Import-fel: {e}")
            return None
        
        # === MAIN LABEL (50x80mm) ===
        width_mm, height_mm = 50, 80
        # KATASYMBOL NATIVE DPI (203 DPI)
        dpi = 203
        width_px = int(width_mm * dpi / 25.4)
        height_px = int(height_mm * dpi / 25.4)
        
        print(f"📏 Main Label: {width_px}x{height_px} pixels ({width_mm}x{height_mm}mm @ {dpi} DPI)")
        
        img = Image.new('RGB', (width_px, height_px), 'white')
        draw = ImageDraw.Draw(img)
        
        margin = 0
        content_width = width_px - (2 * margin)
        
        # Font paths
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        
        def get_text_size(text, font):
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            except:
                return draw.textsize(text, font)
        
        # === BORTTAGET: RUBRIK OCH TITEL ===
        # Vi använder hela ytan för listan
        current_y = margin
        # QR storlek i pixlar vid 203 DPI (21mm = ~170px)
        qr_size = 170 
        
        # === QR-KOD FÖR MAIN LABEL ===
        try:
            qr_url = f"https://coldstorage.enproduktionsbyra.se/disks/{safe_name}"
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=2, border=1) # Box size 2 för lägre upplösning
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            
            qr_x = width_px - qr_size - margin
            qr_y = margin
            img.paste(qr_img, (qr_x, qr_y))
            
            # Definiera exkluderingsområdet för text-wrappern
            # (Left, Top, Width, Height)
            qr_rect = (qr_x, qr_y, qr_size, qr_size)
            
            print(f"✅ Main QR-kod: {qr_size}x{qr_size}px")
        except Exception as e:
            print(f"❌ QR-kod fel: {e}")
            qr_rect = (width_px, 0, 0, 0) # Ingen exclusion om QR misslyckas
        
        # === SMART KUNDLISTA (BARA RIKTIGA MAPPAR) ===
        try:
            customer_folders = self.ask_for_customer_level(tree_data['tree'])
            
            # EXTRA SÄKERHET: Dubbelkolla att inga systemfiler kom igenom
            if customer_folders:
                system_folders = {
                    '.fseventsd', '.Spotlight-V100', '.TemporaryItems', '.Trashes',
                    'Backups.backupdb', '.DS_Store', '.VolumeIcon.icns', '.disk_label',
                    '.disk_label_2x', '.hedge-enabled'
                }
                
                before_count = len(customer_folders)
                customer_folders = [f for f in customer_folders 
                                  if f not in system_folders and not f.startswith('.')]
                customer_folders = sorted(customer_folders, key=str.lower)
                after_count = len(customer_folders)
                
                if before_count != after_count:
                    print(f"🔧 Extra filtrering: {before_count} → {after_count} mappar")
                
                print(f"📁 Slutgiltiga kundmappar: {customer_folders}")
                
        except Exception as e:
            print(f"⚠️ Kundmapp-fel: {e}")
            customer_folders = []
        
        if customer_folders:
            # === BORTTAGET: KUNDER/PROJEKT RUBRIK ===
            # Vi börjar rendera listan direkt
            
            # Tillgänglig höjd för kundlista (hela etiketten)
            total_available_height = height_px - current_y - margin
            
            # === ANVÄND NYA DYNAMISKA FUNKTIONEN MED WRAPPING ===
            if total_available_height > 0:
                render_wrapped_list(
                    customer_folders, content_width, total_available_height, 
                    margin, current_y, qr_rect, draw
                )
        else:
            # Rita disk-statistik istället
            stats = tree_data['statistics']
            
            current_y = self.draw_wrapped_text("Innehåll:", margin, current_y, 
                                             content_width, 
                                             ImageFont.truetype(font_paths[0], 12) if font_paths else ImageFont.load_default(), 
                                             draw)
            current_y += 5
            
            # Statistik-rader
            stat_lines = [
                f"📁 {stats['total_directories']:,} mappar",
                f"📄 {stats['total_files']:,} filer"
            ]
            
            # Lägg till filtyp-info om det finns plats
            if stats.get('file_types'):
                sorted_types = sorted(stats['file_types'].items(), 
                                    key=lambda x: x[1], reverse=True)
                top_type = sorted_types[0]
                stat_lines.append(f"🔝 {top_type[0]}: {top_type[1]:,}")
            
            for stat_line in stat_lines:
                try:
                    small_font = ImageFont.truetype(font_paths[0], 10)
                except:
                    small_font = ImageFont.load_default()
                    
                if current_y + get_text_size(stat_line, small_font)[1] > height_px - margin:
                    break
                current_y = self.draw_wrapped_text(stat_line, margin + 5, current_y,
                                                 content_width, small_font, draw)
                current_y += 3
            
            print("✅ Disk-statistik ritad")
        
        # === HEADER LABEL (KORREKT 80x50mm LANDSKAPSLÄGE) ===
        # FIX: Vi skapar denna i LANDSKAPSLÄGE (80x50) direkt istället för att rotera en 50x80 bild.
        # Detta gör att text-skalningen använder den LÅNGA sidan (80mm) istället för den KORTA (50mm).
        
        header_width_px = height_px  # 80mm bred
        header_height_px = width_px  # 50mm hög
        
        header = Image.new('RGB', (header_width_px, header_height_px), 'white')
        drawHeader = ImageDraw.Draw(header)
        
        print(f"📏 Header Label: {header_width_px}x{header_height_px} pixels (FIXAD: Landskapsläge för max textstorlek)")
        
        header_margin = 0
        
        # === HEADER QR-KOD (högerjusterad, centrerad vertikalt) ===
        header_qr_size = 120 # ~15mm vid 203 DPI
        try:
            qr_header = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=2, border=1)
            qr_header.add_data(qr_url)
            qr_header.make(fit=True)
            
            qr_header_img = qr_header.make_image(fill_color="black", back_color="white")
            qr_header_img = qr_header_img.resize((header_qr_size, header_qr_size), Image.Resampling.LANCZOS)
            
            # Högerjusterad
            header_qr_x = header_width_px - header_qr_size - header_margin
            # Centrerad vertikalt
            header_qr_y = (header_height_px - header_qr_size) // 2
            
            header.paste(qr_header_img, (header_qr_x, header_qr_y))
            
            print(f"✅ Header QR-kod: {header_qr_size}x{header_qr_size}px (högerjusterad)")
        except Exception as e:
            print(f"❌ Header QR-kod fel: {e}")
            header_qr_size = 0
        
        # === HEADER TEXT (vänsterjusterad, max storlek) ===
        # Texten får ta upp allt utrymme till vänster om QR-koden
        header_text_width = header_width_px - header_qr_size - (header_margin * 3)
        header_text_height = header_height_px - (header_margin * 2)
        
        print(f"🔍 Auto-skalar header-text i {header_text_width}x{header_text_height}px (NU använder den hela bredden!)")
        
        # Auto-skala header-text (Justerad för 203 DPI)
        header_optimal_font = None
        for font_size in range(60, 5, -2): # Testar ännu större fonts (upp till 60px för 203 DPI)
            font_loaded = False
            for font_path in font_paths:
                try:
                    test_font = ImageFont.truetype(font_path, font_size)
                    font_loaded = True
                    break
                except (OSError, IOError):
                    continue
            
            if not font_loaded:
                test_font = ImageFont.load_default()
            
            # Mät HELA disk-namnet för header
            # Vi använder vår helper för att vara säker på mätningen
            try:
                bbox = drawHeader.textbbox((0, 0), disk_name, font=test_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width, text_height = drawHeader.textsize(disk_name, font=test_font)
            
            if text_width <= header_text_width and text_height <= header_text_height:
                header_optimal_font = test_font
                
                # Vänsterjusterad, centrerad vertikalt
                header_text_x = header_margin
                header_text_y = (header_height_px - text_height) // 2
                drawHeader.text((header_text_x, header_text_y), disk_name, fill='black', font=header_optimal_font)
                
                print(f"✅ Header text: {font_size}px (vänsterjusterad, stor)")
                break
        
        # Rotera header -90 grader för att passa utskrift (50x80mm)
        # Texten blir vertikal
        header_final = header.rotate(-90, expand=True)
        print("✅ Header roterad -90° för utskrift (Portrait)")

        # === SPARA BÅDA LABELS ===
        try:
            # Main label
            label_file = output_file.replace('.json', '_label.jpg')
            img.save(label_file, 'JPEG', dpi=(dpi, dpi), quality=100)
            
            # Header label (Spara den roterade versionen)
            label_file_header = output_file.replace('.json', '_label_header.jpg')
            header_final.save(label_file_header, 'JPEG', dpi=(dpi, dpi), quality=100)
            
            if os.path.exists(label_file):
                print(f"✅ Main label: {label_file}")
            
            if os.path.exists(label_file_header):
                print(f"✅ Header label: {label_file_header} (korrekt skalad)")
            
            return label_file
            
        except Exception as e:
            print(f"❌ Sparning fel: {e}")
            return None
    
    def draw_wrapped_text(self, text, x, y, max_width, font, draw, color="black", line_spacing=1.2):
        """
        Rita text med automatisk radbrytning
        """
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        current_y = y
        for line in lines:
            draw.text((x, current_y), line, font=font, fill=color)
            bbox = draw.textbbox((0, 0), line, font=font)
            line_height = bbox[3] - bbox[1]
            current_y += int(line_height * line_spacing)
        
        return current_y
    
    def _save_tree_data(self, tree_data: Dict, output_file: str):
        """Spara träd-data till fil"""
        
        print(f"💾 Sparar träd-data till: {output_file}")
        
        # Skapa output-katalog om den inte finns
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Spara som JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, indent=2, ensure_ascii=False)
        
        file_size = os.path.getsize(output_file)
        print(f"✅ Träd-data sparad ({file_size / 1024:.1f} KB)")
        print(f"🚀 Optimerad för Cold Storage v2 import!")

def main():
    parser = argparse.ArgumentParser(description='Optimized Tree Indexer för Cold Storage v2')
    
    parser.add_argument('path', help='Sökväg att scanna')
    parser.add_argument('--output', '-o', help='Output JSON-fil')
    parser.add_argument('--extensions', nargs='*', help='Inkludera bara dessa filextensions (t.ex. .jpg .cr3)')
    parser.add_argument('--exclude', nargs='*', help='Exkludera patterns (regex)')
    parser.add_argument('--no-label', action='store_true', help='Hoppa över label-generering')
    parser.add_argument('--foto-only', action='store_true', help='Bara foto/video-filer')
    parser.add_argument('--no-resume', action='store_true', help='Starta från början (ignorera checkpoint)')
    parser.add_argument('--checkpoint-interval', type=int, default=1000, help='Spara checkpoint var N kataloger (default: 1000)')
    parser.add_argument('--max-depth', type=int, default=8, help='Max djup att scanna (default: 8)')
    
    args = parser.parse_args()
    
    # Setup output files
    if not args.output:
        disk_name = os.path.basename(args.path.rstrip('/')) or 'UnknownDisk'
        safe_name = re.sub(r'[^\w\-_\.]', '_', disk_name)
        output_file = f"{safe_name}.json"
    else:
        output_file = args.output
        safe_name = os.path.basename(output_file).replace('.json', '')
        safe_name = re.sub(r'[^\w\-_\.]', '_', safe_name)
    
    extensions = None
    if args.foto_only:
        extensions = [
            '.cr2', '.cr3', '.nef', '.arw', '.dng', '.iiq', '.3fr', '.orf', '.rw2',  # RAW
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.psd', '.ai',  # Standard
            '.mp4', '.mov', '.avi', '.r3d', '.braw', '.mxf'  # Video
        ]
    elif args.extensions:
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions]
    
    exclude_patterns = args.exclude or None
    
    # Skapa indexer med djup-begränsning
    indexer = OptimizedTreeIndexer(max_depth=args.max_depth)
    
    try:
        print(f"🚀 Optimized Tree Indexer för Cold Storage v2")
        print(f"📏 Max djup: {args.max_depth} nivåer")
        if not HAS_TQDM:
            print("💡 Tips: Installera 'tqdm' för visuell progressbar: pip install tqdm")
        if not HAS_LABEL_SUPPORT and not args.no_label:
            print("💡 Tips: Installera 'qrcode[pil] pillow' för automatisk label-generering")
        
        tree_data = indexer.scan_directory_tree(
            args.path,
            output_file,
            extensions,
            exclude_patterns,
            resume=not args.no_resume,
            checkpoint_interval=args.checkpoint_interval
        )
        
        # Generera disk-label efter scanning
        label_file = None
        if not args.no_label:
            if not HAS_LABEL_SUPPORT:
                print("⚠️ Label-generering ej tillgänglig - installera dependencies:")
                print("   pip install qrcode[pil] pillow")
            else:
                try:
                    disk_name = safe_name.replace('_', ' ').title()
                    
                    print(f"🏷️ Försöker skapa label för: {disk_name} (URL: {safe_name})")
                    
                    label_file = indexer.generate_disk_label(disk_name, tree_data, output_file, safe_name)
                    
                    if label_file and os.path.exists(label_file):
                        print(f"✅ Label skapad framgångsrikt: {label_file}")
                    else:
                        print("❌ Label-fil kunde inte skapas")
                        
                except Exception as e:
                    print(f"❌ Fel vid label-generering: {e}")
                    print(f"🔍 Fullständig felmeddelande: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()
        else:
            print("⏭️ Hoppar över label-generering (--no-label)")
        
        print(f"\n📋 SLUTRESULTAT:")
        print(f"   📁 Mappar: {tree_data['statistics']['total_directories']:,}")
        print(f"   📄 Filer: {tree_data['statistics']['total_files']:,}")
        print(f"   📏 Max djup: {tree_data['statistics']['max_depth']} nivåer")
        print(f"   🗂️ Filtyper: {len(tree_data['statistics']['file_types'])}")
        
        print(f"\n✅ Färdigt! Optimerad för Cold Storage v2 import:")
        print(f"   📄 JSON: {output_file}")
        if label_file and os.path.exists(label_file):
            print(f"   🏷️  Label: {label_file}")
            print(f"   🏷️  Header: {label_file.replace('_label.jpg', '_label_header.jpg')}")
        elif not args.no_label:
            print(f"   ⚠️  Label kunde inte skapas")
        print(f"💡 Ladda upp JSON-filen via Cold Storage web-interface")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Scanning avbruten - checkpoint sparad för återupptagning")
        print(f"💡 Kör samma kommando igen för att fortsätta")
        return 1
    except Exception as e:
        print(f"❌ Fel: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
