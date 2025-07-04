# run.py - Slutgiltig, korrekt version

import sys
import os
import logging

from main_indexer import OptimizedTreeIndexer, HAS_TQDM
from label_generator import HAS_LABEL_SUPPORT, generate_disk_label, ask_for_customer_level
from cli_parser import parse_arguments
from utils import setup_logging

logger = logging.getLogger(__name__)

def main():
    args = parse_arguments()
    
    setup_logging(level=getattr(logging, args['log_level']))
    
    logger.info(f"🚀 Optimized Tree Indexer för Cold Storage v2")
    logger.info(f"📏 Max djup: {args['max_depth']} nivåer")
    logger.info(f"🔗 Följer symlänkar: {args['follow_symlinks']}\"")
    
    if not HAS_TQDM:
        logger.warning("💡 Tips: Installera 'tqdm' för visuell progressbar: pip install tqdm")
    
    if not HAS_LABEL_SUPPORT and not args['no_label']:
        logger.warning("💡 Tips: Installera 'qrcode[pil] pillow' för automatisk label-generering.")
    
    indexer = OptimizedTreeIndexer(max_depth=args['max_depth'], follow_symlinks=args['follow_symlinks'])
    
    try:
        # scan_directory_tree returnerar nu den inkapslade 'scan_info' strukturen
        tree_data = indexer.scan_directory_tree(
            args['path'],
            args['output_file'],
            args['include_extensions'],
            args['exclude_patterns'],
            args['no_resume']
        )
        
        main_label_file = None
        header_label_file = None

        if not args['no_label'] and HAS_LABEL_SUPPORT:
            # Calculate total_size_gb before the function call
            total_size_bytes = tree_data['statistics']['total_size']
            total_size_gb = total_size_bytes / (1024**3) # Convert bytes to GB
            main_label_file, header_label_file = generate_disk_label(
                disk_name=tree_data.get('tree', {}).get('name', os.path.basename(args['path'])), # Safer way to get disk name
                tree_data=tree_data, # <--- NYTT: Skicka hela tree_data hit
                output_file=args['output_file'],
                disk_safe_name=args['disk_safe_name'],
            )
        else:
            logger.info("ℹ️ Etikettgenerering hoppades över.")

        # *** KORRIGERING HÄR ***
        # Använd .get() för att säkert hämta listan med fel/varningar.
        # Om nyckeln 'errors_warnings' inte finns, returnerar .get() en tom lista [].
        errors_and_warnings = tree_data.get('scan_info', {}).get('errors_warnings', [])
        
        if errors_and_warnings:
            logger.warning(f"⚠️ Scan klar med {len(errors_and_warnings)} varningar/fel:")
            for i, err in enumerate(errors_and_warnings[:5]):
                logger.warning(f"   - {err}")
            if len(errors_and_warnings) > 5:
                logger.warning(f"   ... och {len(errors_and_warnings) - 5} fler varningar/fel.")

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
        logger.error(f"Ett kritiskt fel inträffade: {e} - Sökvägen är inte en giltig katalog.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ett oväntat fel inträffade: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()