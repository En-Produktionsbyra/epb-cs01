# main_indexer.py (Corrected Version)

import os
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import re
from collections import deque
import logging

from file_types import determine_file_type
from constants import DEFAULT_INCLUDE_EXTENSIONS, DEFAULT_EXCLUDE_PATTERNS, EXCLUDED_ROOT_FOLDERS

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

logger = logging.getLogger(__name__)

class OptimizedTreeIndexer:
    def __init__(self, max_depth: int, follow_symlinks: bool = False):
        self.version = "2.5.1" # Version updated to reflect fix
        self.checkpoint_file = None
        self.progress_bar = None
        self.max_depth = max_depth
        self.follow_symlinks = follow_symlinks
        self.tree_data = None
        self.start_time = None

    def _should_exclude_directory(self, dir_path: str, root_path: str, exclude_regexes: List[re.Pattern]) -> bool:
        """Determines if a directory should be excluded from the scan."""
        base_name = os.path.basename(dir_path)
        if base_name in EXCLUDED_ROOT_FOLDERS:
            return True
        if any(regex.search(dir_path) for regex in exclude_regexes):
            return True
        return False

    def _count_total_directories(self, root_path: str, exclude_regexes: List[re.Pattern]) -> int:
        """Counts directories for tqdm, respecting depth and exclusions."""
        count = 0
        q = deque([(root_path, 0)])
        visited = set()
        
        while q:
            path, depth = q.popleft()
            
            if path in visited:
                continue
            visited.add(path)
            
            if depth > self.max_depth:
                continue

            if self._should_exclude_directory(path, root_path, exclude_regexes):
                continue
            
            count += 1
            
            if depth < self.max_depth:
                try:
                    for entry in os.scandir(path):
                        if entry.is_dir(follow_symlinks=self.follow_symlinks):
                            q.append((entry.path, depth + 1))
                except (PermissionError, OSError):
                    continue
        return count

    def _initialize_scan_data(self, root_path: str, include_extensions: List[str], exclude_patterns: List[str]) -> Tuple[Dict, set]:
        """Initializes the main data dictionary to match the target JSON structure."""
        self.start_time = datetime.now()
        tree_data = {
            'scan_info': {
                'root_path': root_path,
                'scan_date': self.start_time.isoformat(),
                'scanner': 'OptimizedTreeIndexer',
                'version': self.version,
                'max_depth': self.max_depth,
                'follow_symlinks': self.follow_symlinks,
                'include_extensions': include_extensions,
                'exclude_patterns': exclude_patterns,
                'optimized_for': 'Cold Storage v2 with directories table'
            },
            'statistics': {
                'total_files': 0,
                'total_directories': 0,
                'total_size': 0,
                'file_extensions': {},
                'file_types': {},
                'max_depth': 0,
                'largest_file': {'name': '', 'size': 0},
                'scan_duration_seconds': 0,
                'directory_depth_distribution': {},
                'errors_warnings': []
            },
            'tree': {
                'type': 'directory',
                'name': os.path.basename(root_path) or root_path,
                'path': root_path,
                'relative_path': '',
                'parent_path': None,
                'depth': 0,
                'children': {},
                'files': [],
                'metadata': {
                    'depth': 0,
                    'file_count': 0,
                    'subdirectory_count': 0,
                    'total_size': 0
                }
            }
        }
        processed_paths = set()
        return tree_data, processed_paths

    def scan_directory_tree(self, root_path: str, output_file: str, include_extensions: List[str], exclude_patterns: List[str], no_resume: bool) -> Dict:
        """Scans the directory tree and builds the detailed JSON structure."""
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Root path does not exist: {root_path}")

        exclude_regexes = [re.compile(p, re.IGNORECASE) for p in (exclude_patterns or DEFAULT_EXCLUDE_PATTERNS)]
        self.checkpoint_file = output_file.replace('.json', '_checkpoint.pkl')

        if not no_resume and os.path.exists(self.checkpoint_file):
            logger.info("Resuming from checkpoint...")
            self.tree_data, processed_paths, self.start_time = self._load_checkpoint()
        else:
            logger.info("Starting a new scan...")
            self.tree_data, processed_paths = self._initialize_scan_data(root_path, include_extensions, exclude_patterns)

        # Pre-count directories for an accurate progress bar
        total_dirs = 0
        if HAS_TQDM:
            logger.info("Counting directories for progress bar...")
            total_dirs = self._count_total_directories(root_path, exclude_regexes)
            logger.info(f"Found {total_dirs:,} directories to process.")
        
        # Setup progress bar
        if HAS_TQDM:
            self.progress_bar = tqdm(
                total=total_dirs,
                desc="Scanning...",
                unit=" dirs",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
            )
        
        q = deque([(self.tree_data['tree'], 0)]) # Queue stores (node, depth)
        
        try:
            while q:
                current_node, depth = q.popleft()
                current_path = current_node['path']

                if current_path in processed_paths:
                    continue

                if depth > self.max_depth:
                    continue

                # Update statistics before processing
                if current_path not in processed_paths:
                    stats = self.tree_data['statistics']
                    stats['total_directories'] += 1
                    stats['max_depth'] = max(stats['max_depth'], depth)
                    stats['directory_depth_distribution'][depth] = stats['directory_depth_distribution'].get(depth, 0) + 1
                
                if self.progress_bar:
                    self.progress_bar.update(1)
                    self.progress_bar.set_postfix_str(f"Files: {self.tree_data['statistics']['total_files']:,}, Dir: ...{current_path[-30:]}")

                try:
                    for entry in os.scandir(current_path):
                        entry_path = entry.path
                        if self._should_exclude_directory(entry_path, root_path, exclude_regexes):
                            continue
                        
                        if entry.is_dir(follow_symlinks=self.follow_symlinks):
                            child_node = {
                                'type': 'directory',
                                'name': entry.name,
                                'path': entry_path,
                                'relative_path': os.path.relpath(entry_path, root_path),
                                'parent_path': current_node['relative_path'],
                                'depth': depth + 1,
                                'children': {}, 'files': [],
                                'metadata': {'depth': depth + 1, 'file_count': 0, 'subdirectory_count': 0, 'total_size': 0}
                            }
                            current_node['children'][entry.name] = child_node
                            current_node['metadata']['subdirectory_count'] += 1
                            if depth + 1 <= self.max_depth:
                                q.append((child_node, depth + 1))
                        
                        elif entry.is_file(follow_symlinks=self.follow_symlinks):
                            self._process_file(entry, current_node, root_path)

                except PermissionError as e:
                    logger.warning(f"Permission denied: {current_path}")
                    self.tree_data['statistics']['errors_warnings'].append(str(e))
                except Exception as e:
                    logger.error(f"Error scanning {current_path}: {e}")
                    self.tree_data['statistics']['errors_warnings'].append(str(e))
                
                processed_paths.add(current_path)
                if self.tree_data['statistics']['total_directories'] % 500 == 0:
                    self._save_checkpoint(processed_paths)

        except KeyboardInterrupt:
            logger.warning("Scan interrupted by user. Saving checkpoint.")
            self._save_checkpoint(processed_paths)
            raise
        finally:
            if self.progress_bar:
                self.progress_bar.close()

        end_time = datetime.now()
        self.tree_data['statistics']['scan_duration_seconds'] = (end_time - self.start_time).total_seconds()
        self._save_tree_data(self.tree_data, output_file)
        
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        
        return self.tree_data

    def _process_file(self, entry: os.DirEntry, parent_node: Dict, root_path: str):
        file_ext = Path(entry.name).suffix.lower()
        include_exts = self.tree_data['scan_info']['include_extensions']

        if include_exts and file_ext not in include_exts:
            return

        try:
            file_stat = entry.stat()
            file_size = file_stat.st_size
            file_type = determine_file_type(file_ext)

            file_info = {
                'name': entry.name,
                'path': entry.path,
                'relative_path': os.path.relpath(entry.path, root_path),
                'parent_directory': parent_node['relative_path'],
                'extension': file_ext,
                'size': file_size,
                'type': file_type,
                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            }
            parent_node['files'].append(file_info)
            parent_node['metadata']['file_count'] += 1
            parent_node['metadata']['total_size'] += file_size

            stats = self.tree_data['statistics']
            stats['total_files'] += 1
            stats['total_size'] += file_size
            stats['file_extensions'][file_ext] = stats['file_extensions'].get(file_ext, 0) + 1
            stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1

            if file_size > stats['largest_file']['size']:
                stats['largest_file']['name'] = entry.path
                stats['largest_file']['size'] = file_size

        except (OSError, IOError) as e:
            logger.warning(f"Could not process file {entry.path}: {e}")
            self.tree_data['statistics']['errors_warnings'].append(f"File error: {entry.path} - {e}")
            
    def _save_checkpoint(self, processed_paths: set):
        checkpoint_data = {'tree_data': self.tree_data, 'processed_paths': processed_paths, 'start_time': self.start_time}
        try:
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            logger.debug(f"Checkpoint saved at {datetime.now().isoformat()}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self) -> Tuple[Dict, set, datetime]:
        try:
            with open(self.checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)
            logger.info("Successfully loaded checkpoint.")
            return checkpoint_data['tree_data'], checkpoint_data['processed_paths'], checkpoint_data['start_time']
        except Exception as e:
            logger.warning(f"Could not load checkpoint, starting new scan. Reason: {e}")
            root_path = self.tree_data['scan_info']['root_path'] if self.tree_data else ''
            include_exts = self.tree_data['scan_info']['include_extensions'] if self.tree_data else []
            exclude_pats = self.tree_data['scan_info']['exclude_patterns'] if self.tree_data else []
            tree_data, processed_paths = self._initialize_scan_data(root_path, include_exts, exclude_pats)
            return tree_data, processed_paths, self.start_time
            
    def _save_tree_data(self, tree_data: Dict, output_file: str):
        logger.info(f"Saving data to {output_file}...")
        try:
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Successfully saved JSON output to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save JSON file: {e}")