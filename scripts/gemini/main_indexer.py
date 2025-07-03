# main_indexer.py

import os
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import re
from collections import deque
import logging

# Importera från de nya modulerna
from file_types import determine_file_type
from constants import DEFAULT_INCLUDE_EXTENSIONS, DEFAULT_EXCLUDE_PATTERNS, EXCLUDED_ROOT_FOLDERS
from utils import setup_logging
from label_generator import HAS_LABEL_SUPPORT, ask_for_customer_level, generate_disk_label # ask_for_customer_level är inte direkt kopplad hit längre

# Progressbar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

logger = logging.getLogger(__name__)

class OptimizedTreeIndexer:
    def __init__(self, max_depth: int, follow_symlinks: bool = False):
        self.version = "2.4.1"  # Uppdaterad version efter förbättringar
        self.checkpoint_file = None
        self.progress_bar = None
        self.max_depth = max_depth
        self.follow_symlinks = follow_symlinks # NY: för att hantera symlänkar
        self.tree_data = None # Initiera här för att säkerställa att den alltid finns

    def _should_exclude_directory(self, dir_path: str, root_path: str, exclude_regexes: List[re.Pattern]) -> bool:
        """Gemensam logik för om en mapp ska exkluderas."""
        
        # Nivå 0 filtrering - exkludera problematiska root-mappar
        if dir_path == root_path or os.path.dirname(dir_path) == root_path:
            base_name = os.path.basename(dir_path)
            if base_name in EXCLUDED_ROOT_FOLDERS:
                logger.debug(f"Exkluderar rotmapp '{base_name}' ({dir_path})")
                return True
        
        for pattern in exclude_regexes:
            if pattern.search(dir_path):
                logger.debug(f"Exkluderar sökväg '{dir_path}' matchar mönster '{pattern.pattern}'")
                return True
        return False

    def _should_include_file(self, file_name: str, include_extensions: List[str]) -> bool:
        """Kontrollerar om filen ska inkluderas baserat på filändelse."""
        if not include_extensions:
            return True # Inkludera alla om ingen specifik lista finns
        
        _, ext = os.path.splitext(file_name)
        return ext.lower() in include_extensions

    def _save_checkpoint(self, processed_paths: set):
        """Sparar nuvarande tillstånd till en checkpoint-fil."""
        if not self.checkpoint_file or not self.tree_data: # Kontrollera att tree_data finns
            return
        
        checkpoint_data = {
            'processed_paths': list(processed_paths),
            'tree_data': self.tree_data # Spara hela tree_data
        }
        
        try:
            # Skapa output-katalog om den inte finns
            checkpoint_dir = os.path.dirname(self.checkpoint_file)
            if checkpoint_dir and not os.path.exists(checkpoint_dir):
                os.makedirs(checkpoint_dir)

            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            
            logger.info(f"💾 Checkpoint sparad: {len(processed_paths):,} kataloger, {self.tree_data['statistics']['total_files']:,} filer.")
                
        except Exception as e:
            logger.error(f"⚠️ Kunde inte spara checkpoint: {self.checkpoint_file} - {e}", exc_info=True)

    def _load_checkpoint(self) -> Tuple[set, Dict]:
        """Försöker ladda från en checkpoint-fil."""
        if not self.checkpoint_file or not os.path.exists(self.checkpoint_file):
            return set(), None
        
        try:
            with open(self.checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)
            
            processed_paths = set(checkpoint_data.get('processed_paths', []))
            loaded_tree_data = checkpoint_data.get('tree_data', None)
            
            if loaded_tree_data:
                logger.info(f"✅ Återupptar från checkpoint: {len(processed_paths):,} kataloger, {loaded_tree_data['statistics']['total_files']:,} filer.")
                return processed_paths, loaded_tree_data
            else:
                logger.warning("Checkpoint-fil saknar träd-data, börjar om.")
                return set(), None
        except Exception as e:
            logger.error(f"❌ Kunde inte ladda checkpoint: {self.checkpoint_file} - {e}. Börjar om.", exc_info=True)
            return set(), None

    def _count_total_directories(self, root_path: str, exclude_regexes: List[re.Pattern]) -> int:
        """
        Räkna totalt antal kataloger (för progressbar) med djup-begränsning och exkludering.
        Beaktar symlänkar för att undvika dubbelräkning och loopar.
        """
        total = 0
        stack = [(root_path, 0)] # (path, depth)
        visited_real_paths = set() # För att hålla koll på realpath för att hantera symlänkar
        
        # Se till att errors_warnings finns i statistik-dikten
        if self.tree_data and 'statistics' in self.tree_data and 'errors_warnings' not in self.tree_data['statistics']:
            self.tree_data['statistics']['errors_warnings'] = []

        while stack:
            current_path, current_depth = stack.pop()
            
            if current_depth > self.max_depth:
                continue # Hoppa över om djupet överskrids
            
            real_current_path = os.path.realpath(current_path)
            if real_current_path in visited_real_paths:
                continue # Hoppa över redan räknad fysisk sökväg (symlänk eller dubblett)
            
            if self._should_exclude_directory(current_path, root_path, exclude_regexes):
                continue # Hoppa över exkluderade mappar
            
            try:
                visited_real_paths.add(real_current_path) # Markera som besökt
                total += 1 # Räkna denna katalog
                
                # Om vi inte är för djupt, lägg till underkataloger i stacken
                if current_depth < self.max_depth:
                    for item in os.listdir(current_path):
                        item_path = os.path.join(current_path, item)
                        
                        if os.path.islink(item_path) and not self.follow_symlinks:
                            logger.debug(f"Hoppar över symlänk (follow_symlinks=False): {item_path}")
                            continue # Hoppa över symlänkar om inte aktiverat

                        if self._should_exclude_directory(item_path, root_path, exclude_regexes):
                            continue
                        
                        if os.path.isdir(item_path):
                            stack.append((item_path, current_depth + 1))
                            
            except PermissionError:
                logger.warning(f"Ingen åtkomst för att räkna mappar i: {current_path}")
                total += 1 
                if self.tree_data and 'statistics' in self.tree_data:
                    self.tree_data['statistics']['errors_warnings'].append(f"Permission denied: {current_path}")
                continue
            except OSError as e:
                logger.warning(f"OS-fel vid räkning av mappar i {current_path}: {e}")
                total += 1 
                if self.tree_data and 'statistics' in self.tree_data:
                    self.tree_data['statistics']['errors_warnings'].append(f"OS Error '{e}': {current_path}")
                continue
            except Exception as e:
                logger.error(f"Oväntat fel vid räkning av mappar i {current_path}: {e}", exc_info=True)
                total += 1 
                if self.tree_data and 'statistics' in self.tree_data:
                    self.tree_data['statistics']['errors_warnings'].append(f"Unexpected error '{e}': {current_path}")
                continue
    
        return total

    def _scan_level_by_level(self, root_path: str, exclude_regexes: List[re.Pattern],
                            include_extensions: List[str], checkpoint_interval: int,
                            resumed_from_checkpoint: bool, processed_paths: set):
        """Skannar katalogträdet nivå för nivå för att hantera minnes- och prestandaproblem."""
        
        # Räkna totalt antal kataloger för progressbar
        logger.info("Scanning av katalogstruktur för att beräkna totalt antal mappar (detta kan ta en stund för stora träd)...")
        total_dirs = self._count_total_directories(root_path, exclude_regexes)
        logger.info(f"Hittade {total_dirs:,} mappar att scanna.")

        # Initiera progressbar om tqdm är tillgängligt
        if HAS_TQDM:
            self.progress_bar = tqdm(total=total_dirs, unit="dirs", desc="Skannar")
            if processed_paths:
                self.progress_bar.update(len(processed_paths)) # Återställ progressbar om återupptagen
        
        # Använd deque för effektiv FIFO-hantering
        queue = deque([(root_path, 0, self.tree_data['tree'])]) # Använder self.tree_data här

        dirs_scanned_since_checkpoint = 0

        while queue:
            current_path, current_depth, current_node = queue.popleft()

            if current_path in processed_paths:
                if self.progress_bar:
                    self.progress_bar.set_postfix_str(f"Skipping {os.path.basename(current_path)} (processed)")
                continue

            if current_depth > self.max_depth:
                processed_paths.add(current_path)
                if self.progress_bar:
                    self.progress_bar.update(1)
                    self.progress_bar.set_postfix_str(f"Max depth reached for {os.path.basename(current_path)}")
                continue

            if self._should_exclude_directory(current_path, root_path, exclude_regexes):
                processed_paths.add(current_path)
                if self.progress_bar:
                    self.progress_bar.update(1)
                    self.progress_bar.set_postfix_str(f"Excluded: {os.path.basename(current_path)}")
                continue

            # Uppdatera statistik för totalt antal kataloger
            if current_path != root_path: # Rotmappen räknades redan av _count_total_directories
                self.tree_data['statistics']['total_directories'] += 1
            
            # Uppdatera max djup
            if current_depth > self.tree_data['statistics']['max_depth']:
                self.tree_data['statistics']['max_depth'] = current_depth

            files_in_dir = []
            
            try:
                with os.scandir(current_path) as entries:
                    for entry in entries:
                        if entry.is_dir(follow_symlinks=self.follow_symlinks):
                            # Lägg till underkataloger i kön
                            child_node = {}
                            current_node[entry.name] = child_node
                            queue.append((entry.path, current_depth + 1, child_node))
                        elif entry.is_file(follow_symlinks=self.follow_symlinks):
                            if self._should_include_file(entry.name, include_extensions):
                                file_size = entry.stat().st_size
                                file_extension = os.path.splitext(entry.name)[1].lower()
                                file_type = determine_file_type(file_extension)
                                
                                files_in_dir.append({
                                    "name": entry.name,
                                    "size": file_size,
                                    "extension": file_extension,
                                    "type": file_type
                                })
                                # Uppdatera statistik
                                self.tree_data['statistics']['total_files'] += 1
                                self.tree_data['statistics']['total_size'] += file_size
                                self.tree_data['statistics']['file_types'][file_type] = \
                                    self.tree_data['statistics']['file_types'].get(file_type, 0) + 1
                                
            except PermissionError:
                logger.warning(f"Ingen åtkomst till: {current_path}")
                self.tree_data['statistics']['errors_warnings'].append(f"Permission denied: {current_path}")
            except FileNotFoundError: # Kan hända om en mapp tas bort under scanning
                logger.warning(f"Mapp hittades inte under scanning: {current_path}")
                self.tree_data['statistics']['errors_warnings'].append(f"Directory not found: {current_path}")
            except OSError as e:
                logger.error(f"OS-fel i {current_path}: {e}")
                self.tree_data['statistics']['errors_warnings'].append(f"OS Error '{e}': {current_path}")
            except Exception as e:
                logger.error(f"Oväntat fel i {current_path}: {e}", exc_info=True)
                self.tree_data['statistics']['errors_warnings'].append(f"Unexpected error '{e}': {current_path}")

            if files_in_dir:
                current_node['files'] = files_in_dir

            processed_paths.add(current_path)
            dirs_scanned_since_checkpoint += 1

            if self.progress_bar:
                self.progress_bar.update(1)
                self.progress_bar.set_postfix_str(f"Files: {len(files_in_dir)} (Total: {self.tree_data['statistics']['total_files']:,})")

            # Spara checkpoint periodvis
            if checkpoint_interval > 0 and dirs_scanned_since_checkpoint >= checkpoint_interval:
                self._save_checkpoint(processed_paths)
                dirs_scanned_since_checkpoint = 0 # Återställ räknare

        if self.progress_bar:
            self.progress_bar.close()

    def scan_directory_tree(self, root_path: str, output_file: str,
                            include_extensions: List[str] = None,
                            exclude_patterns: List[str] = None,
                            resume: bool = True, checkpoint_interval: int = 1000) -> Dict:
        """
        Scannar en katalog och bygger en JSON-struktur.
        Implementerar checkpointing och återupptagning.
        """
        logger.info(f"Scanning '{root_path}' (Max djup: {self.max_depth}, Följ symlänkar: {self.follow_symlinks})")

        self.checkpoint_file = f"{output_file}.checkpoint"
        processed_paths, loaded_tree_data = set(), None
        resume_successful = False

        if resume:
            processed_paths, loaded_tree_data = self._load_checkpoint()
            if loaded_tree_data:
                self.tree_data = loaded_tree_data # Ladda in checkpoint-data i self.tree_data
                resume_successful = True
            else:
                logger.info("Ingen giltig checkpoint hittades eller kunde laddas. Börjar ny scanning.")
        
        # Initiera self.tree_data om den inte laddades från checkpoint
        if not self.tree_data:
            exclude_patterns_str = exclude_patterns if exclude_patterns else DEFAULT_EXCLUDE_PATTERNS
            if isinstance(exclude_patterns_str, list):
                exclude_patterns_str = [re.compile(p) for p in exclude_patterns_str]

            self.tree_data = { # Initiera self.tree_data här
                "metadata": {
                    "version": self.version,
                    "disk_name": Path(root_path).name,
                    "scan_date": datetime.now().isoformat(),
                    "root_path": root_path,
                    "max_depth": self.max_depth,
                    "follow_symlinks": self.follow_symlinks,
                    "include_extensions": include_extensions,
                    "exclude_patterns": [p.pattern for p in exclude_patterns_str] if exclude_patterns_str else [],
                    "resumed_from_checkpoint": resume_successful
                },
                "tree": {},
                "statistics": {
                    "total_directories": 0,
                    "total_files": 0,
                    "total_size": 0,
                    "max_depth": 0,
                    "file_types": {},
                    "errors_warnings": []
                }
            }
        else: # Om återupptagen, uppdatera metadata för den nya scanningen
            self.tree_data['metadata']['scan_date'] = datetime.now().isoformat()
            self.tree_data['metadata']['resumed_from_checkpoint'] = resume_successful
            logger.info("Återupptagen scanning - använder befintlig träddata från checkpoint.")


        if exclude_patterns:
            compiled_exclude_regexes = [re.compile(p) for p in exclude_patterns]
        else:
            compiled_exclude_regexes = [re.compile(p) for p in DEFAULT_EXCLUDE_PATTERNS]

        try:
            self._scan_level_by_level(
                root_path,
                compiled_exclude_regexes,
                include_extensions if include_extensions else DEFAULT_INCLUDE_EXTENSIONS,
                checkpoint_interval,
                resume_successful,
                processed_paths
            )
            # Spara en sista checkpoint efter att scanningen är klar
            self._save_checkpoint(processed_paths)
            
            # Ta bort checkpoint-filen om allt gick bra
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                logger.info(f"🗑️ Checkpoint-fil borttagen: {self.checkpoint_file}")

        except Exception as e:
            logger.error(f"❌ Ett oväntat fel inträffade under scanningen: {e}", exc_info=True)
            self._save_checkpoint(processed_paths) # Försök spara checkpoint vid fel
            raise # Kasta om felet så att main-funktionen kan hantera det

        self._save_tree_data(self.tree_data, output_file)
        return self.tree_data # Returnera den slutgiltiga self.tree_data

    def _save_tree_data(self, tree_data: Dict, output_file: str):
        """Spara träd-data till fil."""
        
        logger.info(f"💾 Sparar träd-data till: {output_file}")
        
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(output_file)
            logger.info(f"✅ Träd-data sparad ({file_size / 1024 / 1024:.2f} MB).")
                
        except Exception as e:
            logger.error(f"❌ Fel vid sparande av JSON-fil: {output_file} - {e}", exc_info=True)