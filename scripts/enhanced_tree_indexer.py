#!/usr/bin/env python3
"""
Optimized Tree Indexer för Cold Storage v2 - FIXED VERSION
Skapar JSON-struktur som är perfekt för import till directories-tabellen
Fixar: QR-kod generering och alfabetisk sortering av kundlista
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

class OptimizedTreeIndexer:
    def __init__(self):
        self.version = "2.1.1"  # Uppdaterad version
        self.checkpoint_file = None
        self.progress_bar = None
        
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
        
    def scan_directory_tree(self, root_path: str, output_file: str = None, 
                           include_extensions: List[str] = None,
                           exclude_patterns: List[str] = None,
                           resume: bool = True,
                           checkpoint_interval: int = 1000) -> Dict:
        """
        Scanna katalogträd optimerat för Cold Storage v2
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
                r'/\.',  # Dolda mappar
                r'__MACOSX',
                r'System Volume Information',
                r'\$RECYCLE\.BIN',
                r'\.Spotlight-V100',
                r'\.Trashes',
                r'\.fseventsd'
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
        Scanna katalogträd nivå för nivå med progressbar
        """
        
        # Första: räkna totalt antal kataloger för progressbar
        print("🔢 Räknar totalt antal kataloger...")
        total_dirs = self._count_total_directories(root_path, exclude_regexes)
        print(f"📊 Totalt {total_dirs:,} kataloger att processa")
        
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
                
                # Hoppa över om redan processad
                if dir_path in processed_paths:
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
        """Räkna totalt antal kataloger (för progressbar)"""
        
        total = 0
        stack = [root_path]
        
        while stack:
            current_path = stack.pop()
            
            # Kontrollera exclude patterns
            if any(regex.search(current_path) for regex in exclude_regexes):
                continue
            
            try:
                items = os.listdir(current_path)
                total += 1
                
                for item in items:
                    item_path = os.path.join(current_path, item)
                    
                    if any(regex.search(item_path) for regex in exclude_regexes):
                        continue
                    
                    if os.path.isdir(item_path):
                        stack.append(item_path)
                        
            except (PermissionError, OSError):
                total += 1
                continue
        
        return total
    
    def _process_directory(self, dir_path: str, tree_node: Dict, depth: int, relative_path: str,
                          include_extensions: List[str], exclude_regexes: List,
                          statistics: Dict, next_level: deque):
        """
        Processa en enskild katalog med optimerad metadata
        """
        
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
        Interaktivt hitta rätt nivå för kundmappar
        """
        if not sys.stdin.isatty():
            print("⚠️ Inte en interaktiv terminal - hoppar över kundmapp-detektering")
            return []
        
        def get_folders_at_level(node, current_level, target_level):
            """Hämta alla mappar på en specifik nivå"""
            if current_level == target_level:
                return list(node.get('children', {}).keys())
            
            folders = []
            for child in node.get('children', {}).values():
                folders.extend(get_folders_at_level(child, current_level + 1, target_level))
            return folders
        
        print("\n🗂️ KUNDMAPP-DETEKTERING")
        print("Låt oss hitta rätt nivå för dina kundmappar...")
        
        for level in range(max_attempts):
            folders = get_folders_at_level(tree, 0, level)
            
            if not folders:
                print(f"📁 Nivå {level}: Inga mappar hittades")
                continue
            
            print(f"\n📁 Nivå {level} innehåller {len(folders)} mappar:")
            
            # Visa första 10 mappar
            display_folders = folders[:10]
            for i, folder in enumerate(display_folders, 1):
                print(f"   {i:2d}. {folder}")
            
            if len(folders) > 10:
                print(f"   ... och {len(folders) - 10} till")
            
            # Fråga användaren
            while True:
                response = input(f"\n❓ Är nivå {level} din grundnivå för kunder? (j/n/skip): ").lower().strip()
                
                if response in ['j', 'ja', 'y', 'yes']:
                    print(f"✅ Använder nivå {level} som kundnivå")
                    # SORTERA ALFABETISKT innan returnering - FIX #1
                    sorted_folders = sorted(folders, key=str.lower)
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
        Generera en 50x80mm label med QR-kod och kundlista - FIXED VERSION
        """
        print(f"🏷️ Startar label-generering för: '{disk_name}'")
        
        # Kontrollera dependencies
        if not HAS_LABEL_SUPPORT:
            print(f"❌ QR-kod/PIL moduler saknas")
            print("💡 Installera: pip install qrcode[pil] pillow")
            return None
        
        try:
            import qrcode
            from PIL import Image, ImageDraw, ImageFont
            print("✅ QR-kod och PIL moduler laddade")
        except ImportError as e:
            print(f"❌ Import-fel: {e}")
            return None
        
        # Dimensioner för 50x80mm vid 300 DPI (stående format)
        width_mm, height_mm = 50, 80
        dpi = 900
        width_px = int(width_mm * dpi / 25.4)
        height_px = int(height_mm * dpi / 25.4)
        
        print(f"📏 Label-storlek: {width_px}x{height_px} pixels ({width_mm}x{height_mm}mm)")
        
        # Skapa bild
        img = Image.new('RGB', (width_px, height_px), 'white')
        header = Image.new('RGB', (height_px, int(width_px / 3)), 'white')
        draw = ImageDraw.Draw(img)
        drawHeader = ImageDraw.Draw(header)
        print("✅ Grundbild skapad")
        
        # Marginaler
        margin = 10
        content_width = width_px - (2 * margin)
        
        # Försök ladda font med olika storlekar
        def load_fonts():
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/System/Library/Fonts/Arial.ttf",      # macOS fallback
                "C:/Windows/Fonts/arial.ttf",           # Windows
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
            ]
            
            fonts = {}
            for size_name, base_size in [('header', 250), ('title', 32*3), ('text', 20*3), ('small', 16*3), ('tiny', 14*3)]:
                font_loaded = False
                for path in font_paths:
                    try:
                        fonts[size_name] = ImageFont.truetype(path, base_size)
                        font_loaded = True
                        break
                    except (OSError, IOError):
                        continue
                
                if not font_loaded:
                    fonts[size_name] = ImageFont.load_default()
            
            return fonts
        
        fonts = load_fonts()
        print("✅ Fonts laddade")
        
        # Helper funktion för att få text-dimensioner
        def get_text_size(text, font):
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            except:
                # Fallback för äldre PIL versioner
                return draw.textsize(text, font)
        
        # 1. Rita rubrik (disk-namn) - anpassa längd automatiskt
        current_y = margin
        display_name = disk_name
        
        # Hitta passande rubrik-storlek
        title_font = fonts['title']
        header_font = fonts['header']
        while len(display_name) > 0:
            text_width, text_height = get_text_size(display_name, title_font)
            if text_width <= content_width:
                break
            # Förkorta texten
            display_name = display_name[:-1]
        
        if len(display_name) < len(disk_name):
            display_name = display_name.rstrip() + "..."
        
        # Centrera rubrik
        text_width, text_height = get_text_size(display_name, title_font)
        title_x = (width_px - text_width) // 2
        draw.text((title_x, current_y), display_name, fill='black', font=title_font)
        drawHeader.text((30, 180), display_name, fill='black', font=header_font)
        current_y += text_height + 30
        print(f"✅ Rubrik ritad: '{display_name}'")
        
        # 2. Generera och placera QR-kod - FIX #2: Sätt storlek INNAN QR-kod generering
        qr_max_size = min(content_width // 3, 70)  # FLYTTA DENNA RAD UPP!
        
        qr_y = current_y  # Spara QR-kodens startposition
        try:
            qr_url = f"https://coldstorage.enproduktionsbyra.se/disks/{safe_name}"
            print(f"🔗 Skapar QR-kod för: {qr_url}")
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,  # Mindre box_size för att spara plats
                border=1,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Skala QR-koden till rätt storlek
            qr_img = qr_img.resize((750, 750), Image.Resampling.LANCZOS)
            
            # Placera QR-kod i övre högra hörnet
            qr_x = width_px - 750 - margin
            img.paste(qr_img, (qr_x, qr_y))

            qr_x = height_px - int(width_px / 3) + 30
            qr_img = qr_img.resize((int(width_px / 3) - 60, int(width_px / 3)- 60), Image.Resampling.LANCZOS)
            header.paste(qr_img, (qr_x, 30))
            
            print(f"✅ QR-kod placerad ({qr_max_size}x{qr_max_size}px)")
            
            # Sätt text-start i höjd med QR-koden
            text_start_y = qr_y
                
        except Exception as e:
            print(f"❌ Fel vid QR-kod generering: {e}")
            text_start_y = current_y
        
        # 3. Hitta kundmappar
        try:
            customer_folders = self.ask_for_customer_level(tree_data['tree'])
            print(f"📁 Hittade {len(customer_folders)} kundmappar")
        except Exception as e:
            print(f"⚠️ Fel vid kundmapp-detektering: {e}")
            customer_folders = []
        
        # 4. Rita innehåll (kundlista eller statistik) - MAXIMAL BREDD OCH HÖJD
        if customer_folders:
            # Börja texten i höjd med QR-koden (inte under den!)
            current_y = text_start_y
            
            # Beräkna maximal textbredd - QR-koden tar ca 1/3, så vi kan använda 2/3
            qr_max_size = min(content_width // 3, 70)
            text_max_width = width_px - qr_max_size - (margin * 2) - 10  # Extra marginal från QR-kod
            print(f"📏 Textbredd: {text_max_width}px (QR-kod: {qr_max_size}px)")
            
            # Rita kundlista rubrik på vänstra sidan bredvid QR-koden
            draw.text((margin, current_y), "Kunder/Projekt:", fill='black', font=fonts['text'])
            current_y += get_text_size("Kunder/Projekt:", fonts['text'])[1] + 5
            
            # Nu har vi HELA resten av bilden att fylla!
            total_available_height = height_px - current_y - margin
            print(f"🎯 MAXIMAL tillgänglig höjd: {total_available_height}px (från y={current_y} till y={height_px-margin})")
            
            # Räkna först hur många mappar vi har totalt
            total_folders = len(customer_folders)
            print(f"📊 Ska fördela {total_folders} mappar på {total_available_height}px")
            
            # Beräkna optimal radavstånd för att fylla EXAKT hela höjden
            if total_folders > 0:
                optimal_line_height = total_available_height / total_folders
                # Men inte mindre än 8px per rad (annars blir det oläsligt)
                actual_line_height = max(8, int(optimal_line_height))
            else:
                actual_line_height = 15
            
            print(f"📏 Beräknad radavstånd: {optimal_line_height:.1f}px, använd: {actual_line_height}px")
            
            # Välj font-storlek baserat på radavstånd
            if actual_line_height >= 18:
                customer_font = fonts['small']  # 16pt - stor font
            elif actual_line_height >= 14:
                customer_font = fonts['tiny']   # 14pt - medel font  
            else:
                customer_font = ImageFont.load_default()  # Minsta font
            
            print(f"✅ Vald font för radavstånd {actual_line_height}px")
            
            customers_shown = 0
            
            # Rita ALLA mappar med samma font och radavstånd - VERKLIGEN ALLA!
            for folder in customer_folders:
                # Mjukare kontroll - bara se till att texten inte går utanför bilden
                if current_y > height_px - margin - 8:  # Lämna bara 8px marginal
                    print(f"🛑 VERKLIG STOPP vid y={current_y}, hade planerat {actual_line_height}px radavstånd")
                    break
                
                # INGEN TRUNKERING - använd full bredd!
                # Testa om hela namnet får plats
                full_text = f"• {folder}"
                text_width = get_text_size(full_text, customer_font)[0]
                
                if text_width <= text_max_width:
                    # Hela namnet får plats!
                    display_text = full_text
                else:
                    # Bara om det verkligen inte får plats, förkorta minimalt
                    display_folder = folder
                    while len(display_folder) > 5:
                        test_text = f"• {display_folder}..."
                        if get_text_size(test_text, customer_font)[0] <= text_max_width:
                            break
                        display_folder = display_folder[:-1]
                    display_text = f"• {display_folder}..."
                
                # Rita mappen
                draw.text((margin, current_y), display_text, fill='black', font=customer_font)
                
                # Dynamisk radavstånd - använd mindre space om vi börjar få ont om plats
                remaining_folders = len(customer_folders) - customers_shown - 1
                remaining_height = height_px - margin - current_y - 8
                
                if remaining_folders > 0 and remaining_height > 0:
                    # Anpassa radavståndet för att få plats med resten
                    dynamic_line_height = min(actual_line_height, remaining_height // remaining_folders)
                    dynamic_line_height = max(6, dynamic_line_height)  # Minst 6px
                    current_y += dynamic_line_height
                else:
                    current_y += actual_line_height
                
                customers_shown += 1
                
                # Debug varje 15:e rad
                if customers_shown % 15 == 0:
                    remaining = height_px - margin - current_y
                    print(f"📍 Rad {customers_shown}/{len(customer_folders)}: y={current_y}, kvar={remaining}px")
            
            final_remaining = height_px - margin - current_y
            print(f"🏁 FÖRSTA OMGÅNGEN: {customers_shown}/{total_folders} mappar, {final_remaining}px outnyttjat")
            
            # Om vi FORTFARANDE har mappar kvar, pressa in dem med minimal spacing
            if customers_shown < total_folders:
                print(f"🚨 FORTFARANDE {total_folders - customers_shown} mappar kvar! Pressar in dem...")
                
                micro_font = ImageFont.load_default()
                minimal_spacing = 6  # Absolut minimum
                
                for folder in customer_folders[customers_shown:]:
                    # Hårdare kontroll - verkligen sista pixlarna
                    if current_y + minimal_spacing > height_px - margin:
                        print(f"💀 ABSOLUT STOPP vid mapp {customers_shown}: '{folder}'")
                        break
                    
                    # Kortare namn för att få plats
                    short_text = f"• {folder[:20]}..." if len(folder) > 20 else f"• {folder}"
                    
                    draw.text((margin, current_y), short_text, fill='black', font=micro_font)
                    current_y += minimal_spacing
                    customers_shown += 1
                
                super_final_remaining = height_px - margin - current_y
                print(f"💪 SUPERKAMP: {customers_shown}/{total_folders} mappar, {super_final_remaining}px kvar")
            
        else:
            # Rita disk-statistik istället
            stats = tree_data['statistics']
            
            current_y = draw_wrapped_text("Innehåll:", margin, current_y, 
                                         content_width, fonts['text'])
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
                if current_y + get_text_size(stat_line, fonts['small'])[1] > height_px - margin:
                    break
                current_y = draw_wrapped_text(stat_line, margin + 5, current_y,
                                             content_width, fonts['small'])
                current_y += 3
            
            print("✅ Disk-statistik ritad")
        
        # 5. Spara label
        try:
            label_file = output_file.replace('.json', '_label.jpg')
            img.save(label_file, 'JPEG', dpi=(dpi, dpi), quality=100, speed=0, compress_level=0)
            label_file_header = output_file.replace('.json', '_label_header.jpg')
            header.save(label_file_header, 'JPEG', dpi=(dpi, dpi), quality=100, speed=0, compress_level=0)
            
            if os.path.exists(label_file):
                file_size = os.path.getsize(label_file)
                print(f"✅ Label sparad: {label_file}")
                print(f"📏 Storlek: {width_mm}x{height_mm}mm ({width_px}x{height_px}px, {file_size:,} bytes)")
                return label_file
            else:
                print(f"❌ Label-fil skapades inte: {label_file}")
                return None
                
        except Exception as e:
            print(f"❌ Fel vid sparning av label: {e}")
            return None
    
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
    
    args = parser.parse_args()
    
    # Setup output files - använd disk-namn istället för timestamp
    if not args.output:
        # Skapa filnamn baserat på disk-namn
        disk_name = os.path.basename(args.path.rstrip('/')) or 'UnknownDisk'
        # Rensa ogiltiga tecken för filnamn
        safe_name = re.sub(r'[^\w\-_\.]', '_', disk_name)
        output_file = f"{safe_name}.json"
    else:
        output_file = args.output
        # NYTT: Extrahera safe_name från output_file namnet
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
    
    # Kör optimerad scanning
    indexer = OptimizedTreeIndexer()
    
    try:
        print(f"🚀 Optimized Tree Indexer för Cold Storage v2")
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
        
        # Generera disk-label EFTER scanning
        label_file = None
        if not args.no_label:
            if not HAS_LABEL_SUPPORT:
                print("⚠️ Label-generering ej tillgänglig - installera dependencies:")
                print("   pip install qrcode[pil] pillow")
            else:
                try:
                    # NYTT: Använd safe_name som disk_name för konsistent namngivning
                    disk_name = safe_name.replace('_', ' ').title()  # Gör det lite snyggare för labeln
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