# run.py (detta är den nya huvudfilen att köra)

import sys
import os
import logging

# Importera från de nya modulerna
from main_indexer import OptimizedTreeIndexer, HAS_TQDM
from label_generator import HAS_LABEL_SUPPORT, generate_disk_label, ask_for_customer_level # ask_for_customer_level behövs här
from cli_parser import parse_arguments
from utils import setup_logging # Antar att setup_logging nu finns i utils.py

# Konfigurera loggning tidigt
logger = logging.getLogger(__name__)

def main():
    args = parse_arguments()
    
    # Sätt upp loggning baserat på CLI-argument
    setup_logging(level=getattr(logging, args['log_level']))
    
    logger.info(f"🚀 Optimized Tree Indexer för Cold Storage v2")
    logger.info(f"📏 Max djup: {args['max_depth']} nivåer")
    logger.info(f"🔗 Följer symlänkar: {args['follow_symlinks']}")
    
    if not HAS_TQDM:
        logger.warning("💡 Tips: Installera 'tqdm' för visuell progressbar: pip install tqdm")
    if not HAS_LABEL_SUPPORT and not args['no_label']:
        logger.warning("💡 Tips: Installera 'qrcode[pil] pillow' för automatisk label-generering.")
    
    indexer = OptimizedTreeIndexer(max_depth=args['max_depth'], follow_symlinks=args['follow_symlinks'])
    
    try:
        tree_data = indexer.scan_directory_tree(
            args['path'],
            args['output_file'],
            args['include_extensions'],
            args['exclude_patterns'],
            resume=not args['no_resume'],
            checkpoint_interval=args['checkpoint_interval']
        )
        
        # Generera disk-label efter scanning
        main_label_file = None
        header_label_file = None
        if not args['no_label']:
            if not HAS_LABEL_SUPPORT:
                logger.warning("⚠️ Label-generering ej tillgänglig - installera dependencies:")
                logger.warning("   pip install qrcode[pil] pillow")
            else:
                try:
                    # Använd safe_name för URL och en mer läsbar version för display
                    disk_name_display = os.path.basename(args['path'].rstrip(os.sep)) or 'Unknown Disk'
                    # Format för display: "Disk Name" istället för "Disk_Name"
                    disk_name_display = disk_name_display.replace('_', ' ').title() 
                    
                    logger.info(f"🏷️ Försöker skapa etiketter för: '{disk_name_display}' (bas-URL: {args['disk_safe_name']})")
                    
                    # Passera tree_data direkt till generate_disk_label
                    main_label_file, header_label_file = generate_disk_label(disk_name_display, tree_data, args['output_file'], args['disk_safe_name'])
                    
                    if main_label_file and os.path.exists(main_label_file):
                        logger.info(f"✅ Huvudetikett skapad framgångsrikt: {main_label_file}")
                    else:
                        logger.error("❌ Huvudetikett kunde inte skapas.")
                    
                    if header_label_file and os.path.exists(header_label_file):
                        logger.info(f"✅ Header-etikett skapad framgångsrikt: {header_label_file}")
                    else:
                        logger.error("❌ Header-etikett kunde inte skapas.")
                        
                except Exception as e:
                    logger.error(f"❌ Fel vid etikettgenerering: {e}", exc_info=True) # Logga full traceback
        else:
            logger.info("⏭️ Hoppar över etikettgenerering (--no-label).")
        
        logger.info(f"\n📋 SLUTRESULTAT:")
        logger.info(f"   📁 Mappar: {tree_data['statistics']['total_directories']:,}")
        logger.info(f"   📄 Filer: {tree_data['statistics']['total_files']:,}")
        logger.info(f"   📏 Max djup: {tree_data['statistics']['max_depth']} nivåer")
        logger.info(f"   🗂️ Unika filtyper: {len(tree_data['statistics']['file_types'])}")
        
        if tree_data['statistics'].get('errors_warnings'):
            logger.warning(f"❗ Varningar/Fel under scanning: {len(tree_data['statistics']['errors_warnings'])} st.")
            for err in tree_data['statistics']['errors_warnings'][:5]: # Visa max 5 fel
                logger.warning(f"   - {err}")
            if len(tree_data['statistics']['errors_warnings']) > 5:
                logger.warning(f"   ... och {len(tree_data['statistics']['errors_warnings']) - 5} fler varningar/fel.")

        logger.info(f"\n✅ Färdigt! Optimerad för Cold Storage v2 import:")
        logger.info(f"   📄 JSON-utdata: {args['output_file']}")
        if main_label_file and os.path.exists(main_label_file):
            logger.info(f"   🏷️  Huvudetikett: {main_label_file}")
        if header_label_file and os.path.exists(header_label_file):
            logger.info(f"   🏷️  Headeretikett: {header_label_file}")
        elif not args['no_label']:
            logger.warning(f"   ⚠️  Etiketter kunde inte skapas.")
        logger.info(f"💡 Ladda upp JSON-filen via Cold Storage web-interface för full funktionalitet.")
        
    except KeyboardInterrupt:
        logger.info(f"\n⚠️ Scanning avbruten av användaren - checkpoint sparad för återupptagning.")
        logger.info(f"💡 Kör samma kommando igen för att fortsätta från checkpoint.")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Ett kritiskt fel inträffade: {e}")
        sys.exit(1)
    except NotADirectoryError as e:
        logger.error(f"Ett kritiskt fel inträffade: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Ett oväntat och kritiskt fel inträffade under programkörningen: {e}", exc_info=True)
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()