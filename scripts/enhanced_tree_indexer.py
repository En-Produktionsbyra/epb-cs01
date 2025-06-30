#!/usr/bin/env python3
"""
Enhanced Simpel trädstruktur-indexer för Cold Storage ML-träning
Med progressbar, återupptagning och nivå-för-nivå scanning
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

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️ Installera 'tqdm' för progressbar: pip install tqdm")

class EnhancedTreeIndexer:
    def __init__(self):
        self.version = "2.0.0"
        self.checkpoint_file = None
        self.progress_bar = None
        
    def scan_directory_tree(self, root_path: str, output_file: str = None, 
                           include_extensions: List[str] = None,
                           exclude_patterns: List[str] = None,
                           resume: bool = True,
                           checkpoint_interval: int = 1000) -> Dict:
        """
        Scanna katalogträd med progressbar och återupptagning
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
        
        print(f"📁 Enhanced Tree Indexer v{self.version}")
        print(f"📂 Skannar: {root_path}")
        print(f"💾 Output: {output_file}")
        print(f"🔄 Checkpoint: {self.checkpoint_file}")
        print(f"⏰ Starttid: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Default file extensions
        if include_extensions is None:
            include_extensions = [
                # RAW foto
                '.cr2', '.cr3', '.nef', '.arw', '.dng', '.iiq', '.3fr',
                # Standard foto
                '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.psd',
                # Video
                '.mp4', '.mov', '.avi', '.r3d', '.braw', '.mxf',
                # Audio
                '.wav', '.aiff', '.mp3', '.flac',
                # Dokument
                '.pdf', '.ai', '.eps', '.indd'
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
                r'\$RECYCLE\.BIN'
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
        
        # Visa vanligaste filtyper
        if tree_data['statistics']['file_extensions']:
            print(f"   📋 Top 10 filtyper:")
            sorted_extensions = sorted(
                tree_data['statistics']['file_extensions'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            for ext, count in sorted_extensions[:10]:
                print(f"      {ext}: {count:,} filer")
        
        # Spara slutresultat
        self._save_tree_data(tree_data, output_file)
        
        # Rensa checkpoint
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print(f"🗑️ Checkpoint-fil borttagen")
        
        return tree_data
    
    def _initialize_scan_data(self, root_path: str, include_extensions: List[str], 
                             exclude_patterns: List[str]) -> Tuple[Dict, set, datetime]:
        """Initialisera scan-data"""
        
        tree_data = {
            'scan_info': {
                'root_path': root_path,
                'scan_date': datetime.now().isoformat(),
                'scanner': 'EnhancedTreeIndexer',
                'version': self.version,
                'include_extensions': include_extensions,
                'exclude_patterns': exclude_patterns
            },
            'statistics': {
                'total_files': 0,
                'total_directories': 0,
                'file_extensions': {},
                'max_depth': 0,
                'largest_file': {'name': '', 'size': 0},
                'scan_duration_seconds': 0
            },
            'tree': {
                'type': 'directory',
                'name': os.path.basename(root_path) or root_path,
                'path': root_path,
                'children': {},
                'files': [],
                'metadata': {
                    'depth': 0,
                    'file_count': 0,
                    'subdirectory_count': 0
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
        current_level = deque([(root_path, tree_data['tree'], 0)])
        checkpoint_counter = 0
        
        while current_level:
            next_level = deque()
            
            # Processa alla kataloger på nuvarande nivå
            while current_level:
                dir_path, tree_node, depth = current_level.popleft()
                
                # Hoppa över om redan processad
                if dir_path in processed_paths:
                    if HAS_TQDM and self.progress_bar:
                        self.progress_bar.update(1)
                    continue
                
                # Processa denna katalog
                self._process_directory(
                    dir_path, tree_node, depth, 
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
                        'ext': len(tree_data['statistics']['file_extensions'])
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
                total += 1  # Räkna även kataloger vi inte kan läsa
                continue
        
        return total
    
    def _process_directory(self, dir_path: str, tree_node: Dict, depth: int,
                          include_extensions: List[str], exclude_regexes: List,
                          statistics: Dict, next_level: deque):
        """
        Processa en enskild katalog
        """
        
        # Uppdatera max djup
        statistics['max_depth'] = max(statistics['max_depth'], depth)
        
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
        
        for item in items:
            item_path = os.path.join(dir_path, item)
            
            # Kontrollera exclude patterns
            if any(regex.search(item_path) for regex in exclude_regexes):
                continue
            
            if os.path.isdir(item_path):
                # Skapa mapp-nod
                child_node = {
                    'type': 'directory',
                    'name': item,
                    'path': item_path,
                    'children': {},
                    'files': [],
                    'metadata': {
                        'depth': depth + 1,
                        'file_count': 0,
                        'subdirectory_count': 0
                    }
                }
                
                tree_node['children'][item] = child_node
                tree_node['metadata']['subdirectory_count'] += 1
                statistics['total_directories'] += 1
                
                # Lägg till i nästa nivå
                next_level.append((item_path, child_node, depth + 1))
                
            elif os.path.isfile(item_path):
                # Processa fil
                self._process_file(
                    item, item_path, include_extensions,
                    tree_node, statistics
                )
    
    def _process_file(self, filename: str, file_path: str, 
                     include_extensions: List[str], tree_node: Dict, 
                     statistics: Dict):
        """
        Processa en enskild fil
        """
        
        file_ext = Path(filename).suffix.lower()
        
        # Kontrollera filextension
        if include_extensions and file_ext not in include_extensions:
            return
        
        try:
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            
            # Uppdatera statistik
            statistics['total_files'] += 1
            tree_node['metadata']['file_count'] += 1
            
            if file_ext not in statistics['file_extensions']:
                statistics['file_extensions'][file_ext] = 0
            statistics['file_extensions'][file_ext] += 1
            
            if file_size > statistics['largest_file']['size']:
                statistics['largest_file'] = {
                    'name': file_path,
                    'size': file_size
                }
            
            # Fil-info
            file_info = {
                'name': filename,
                'path': file_path,
                'extension': file_ext,
                'size': file_size,
                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            }
            
            tree_node['files'].append(file_info)
            
        except (OSError, IOError) as e:
            if not HAS_TQDM:
                print(f"⚠️ Kunde inte läsa fil {file_path}: {e}")
    
    def _save_checkpoint(self, tree_data: Dict, processed_paths: set, start_time: datetime):
        """
        Spara checkpoint för återupptagning
        """
        
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
    
    def _save_tree_data(self, tree_data: Dict, output_file: str):
        """
        Spara träd-data till fil
        """
        
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
    
    def create_summary_report(self, tree_data: Dict, output_file: str = None):
        """
        Skapa sammanfattningsrapport av träd-strukturen
        """
        
        summary = {
            'scan_summary': tree_data['scan_info'],
            'statistics': tree_data['statistics'],
            'structure_analysis': self._analyze_structure(tree_data['tree']),
            'naming_patterns': self._analyze_naming_patterns(tree_data['tree']),
            'recommendations': []
        }
        
        # Generera rekommendationer
        summary['recommendations'] = self._generate_recommendations(summary)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"📊 Sammanfattningsrapport sparad: {output_file}")
        
        return summary
    
    def _analyze_structure(self, tree: Dict) -> Dict:
        """Analysera träd-strukturen"""
        
        analysis = {
            'root_directories': list(tree.get('children', {}).keys()),
            'total_depth': self._calculate_max_depth(tree),
            'directory_patterns': {},
            'common_folder_names': {}
        }
        
        # Analysera vanliga mappnamn
        self._collect_folder_names(tree, analysis['common_folder_names'])
        
        # Sortera efter frekvens
        analysis['common_folder_names'] = dict(
            sorted(analysis['common_folder_names'].items(), 
                  key=lambda x: x[1], reverse=True)
        )
        
        return analysis
    

    
    def _analyze_naming_patterns(self, tree: Dict) -> Dict:
        """Analysera namngivningspatterns i filnamn"""
        
        patterns = {
            'date_patterns': {},
            'separator_patterns': {},
            'structure_patterns': {},
            'extension_patterns': {}
        }
        
        def analyze_files_in_node(node):
            for file_info in node.get('files', []):
                filename = file_info['name']
                
                # Analysera datum-patterns
                date_matches = re.findall(r'\d{6}|\d{8}', filename)
                for match in date_matches:
                    pattern_key = f"date_{len(match)}_digits"
                    if pattern_key not in patterns['date_patterns']:
                        patterns['date_patterns'][pattern_key] = 0
                    patterns['date_patterns'][pattern_key] += 1
                
                # Analysera separatorer
                if '_' in filename:
                    patterns['separator_patterns']['underscore'] = patterns['separator_patterns'].get('underscore', 0) + 1
                if '-' in filename:
                    patterns['separator_patterns']['dash'] = patterns['separator_patterns'].get('dash', 0) + 1
                
                # Analysera filextensions
                ext = file_info.get('extension', '')
                if ext:
                    patterns['extension_patterns'][ext] = patterns['extension_patterns'].get(ext, 0) + 1
            
            # Rekursivt genom barn
            for child in node.get('children', {}).values():
                analyze_files_in_node(child)
        
        analyze_files_in_node(tree)
        
        return patterns
    
    def _calculate_max_depth(self, node: Dict, current_depth: int = 0) -> int:
        """Beräkna maximalt djup i trädet"""
        
        max_depth = current_depth
        
        for child in node.get('children', {}).values():
            child_depth = self._calculate_max_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _collect_folder_names(self, node: Dict, folder_counts: Dict):
        """Samla alla mappnamn och räkna frekvens"""
        
        folder_name = node.get('name', '')
        if folder_name:
            folder_counts[folder_name] = folder_counts.get(folder_name, 0) + 1
        
        for child in node.get('children', {}).values():
            self._collect_folder_names(child, folder_counts)
    
    def _generate_recommendations(self, summary: Dict) -> List[str]:
        """Generera rekommendationer baserat på analys"""
        
        recommendations = []
        
        # Rekommendationer baserat på struktur
        if summary['structure_analysis']['total_depth'] > 6:
            recommendations.append("Mappstrukturen är mycket djup (>6 nivåer) - kan påverka prestanda")
        
        # Rekommendationer baserat på namngivning
        naming = summary['naming_patterns']
        if naming['separator_patterns'].get('underscore', 0) > naming['separator_patterns'].get('dash', 0):
            recommendations.append("Underscore (_) är vanligaste separatorn - bra för systemkompatibilitet")
        
        # Rekommendationer för filantal
        total_files = summary['statistics']['total_files']
        if total_files > 100000:
            recommendations.append(f"Stort antal filer ({total_files:,}) - överväg indexering i mindre delar")
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description='Enhanced Träd-indexer med progressbar och återupptagning')
    
    parser.add_argument('path', help='Sökväg att scanna')
    parser.add_argument('--output', '-o', help='Output JSON-fil')
    parser.add_argument('--summary', '-s', help='Skapa sammanfattningsrapport')
    parser.add_argument('--extensions', nargs='*', help='Inkludera bara dessa filextensions (t.ex. .jpg .cr3)')
    parser.add_argument('--exclude', nargs='*', help='Exkludera patterns (regex)')
    parser.add_argument('--foto-only', action='store_true', help='Bara foto/video-filer')
    parser.add_argument('--no-resume', action='store_true', help='Starta från början (ignorera checkpoint)')
    parser.add_argument('--checkpoint-interval', type=int, default=1000, help='Spara checkpoint var N kataloger (default: 1000)')
    
    args = parser.parse_args()
    
    # Setup output files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = args.output or f"tree_structure_{timestamp}.json"
    
    extensions = None
    if args.foto_only:
        extensions = [
            '.cr2', '.cr3', '.nef', '.arw', '.dng', '.iiq', '.3fr',  # RAW
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.psd', '.ai',  # Standard
            '.mp4', '.mov', '.avi', '.r3d', '.braw', '.mxf'  # Video
        ]
    elif args.extensions:
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions]
    
    exclude_patterns = args.exclude or None
    
    # Kör enhanced scanning
    indexer = EnhancedTreeIndexer()
    
    try:
        print(f"🚀 Enhanced Tree Indexer - startad")
        if not HAS_TQDM:
            print("💡 Tips: Installera 'tqdm' för visuell progressbar: pip install tqdm")
        
        tree_data = indexer.scan_directory_tree(
            args.path,
            output_file,
            extensions,
            exclude_patterns,
            resume=not args.no_resume,
            checkpoint_interval=args.checkpoint_interval
        )
        
        # Skapa sammanfattning
        summary_file = args.summary or f"tree_summary_{timestamp}.json"
        summary = indexer.create_summary_report(tree_data, summary_file)
        
        print(f"\n📋 SLUTRESULTAT:")
        print(f"   📁 Rot-mappar: {len(summary['structure_analysis']['root_directories'])}")
        print(f"   📏 Max djup: {summary['structure_analysis']['total_depth']} nivåer")
        print(f"   🗂️ Filtyper: {len(summary['statistics']['file_extensions'])}")
        
        print(f"\n✅ Färdigt! Filer skapade:")
        print(f"   📄 Träd-struktur: {output_file}")
        print(f"   📊 Sammanfattning: {summary_file}")
        
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