# cli_parser.py

import argparse
import os
import re
import logging # Lägg till denna rad

logger = logging.getLogger(__name__) # Lägg till denna rad

from constants import DEFAULT_INCLUDE_EXTENSIONS

def parse_arguments():
    """Parsar kommandoradsargument."""
    parser = argparse.ArgumentParser(
        description='Optimized Tree Indexer för Cold Storage v2',
        formatter_class=argparse.RawTextHelpFormatter # För att bevara formatering i hjälptext
    )
    
    parser.add_argument('path', 
                        help='Sökväg till katalog som ska scannas.')
    parser.add_argument('--output', '-o', 
                        help='Output JSON-filens namn. Om inte angivet, genereras ett namn baserat på sökvägen.')
    parser.add_argument('--extensions', nargs='*', 
                        help='''Inkludera bara filer med dessa filändelser (t.ex. .jpg .cr3). 
Filer utanför denna lista ignoreras.
Standard: Alla extensions i "foto-only" läget.
''')
    parser.add_argument('--exclude', nargs='*', 
                        help='''Exkludera kataloger eller filer vars fullständiga sökväg matchar något av dessa REGEX-mönster.
Exempel: "--exclude \\\\.git$ .cache" (behöver dubbla backslash i terminal)
Standard: Kända systemfiler och temporära filer.
''')
    parser.add_argument('--no-label', action='store_true', 
                        help='Hoppa över generering av fysiska etiketter (QR-kod + text).')
    parser.add_argument('--foto-only', action='store_true', 
                        help='''Begränsa scanningen till populära foto- och videoformat.
Om denna flagga används, ignoreras --extensions om det också är angivet.
''')
    parser.add_argument('--no-resume', action='store_true', 
                        help='Starta alltid scanningen från början, ignorera tidigare sparade checkpoints.')
    parser.add_argument('--checkpoint-interval', type=int, default=1000, 
                        help='Antal kataloger att processa innan en checkpoint sparas (default: 1000).')
    parser.add_argument('--max-depth', type=int, default=8, 
                        help='Maximalt djup att scanna ner i katalogstrukturen (0 för bara root, default: 8).')
    parser.add_argument('--follow-symlinks', action='store_true',
                        help='Följ symboliska länkar. VARNING: Kan leda till oändliga loopar eller dubbelräkning.')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Sätt loggnivå (default: INFO).')

    args_parsed = parser.parse_args()

    logger.debug(f"Debug cli_parser: args.path = '{args_parsed.path}'")
    
    # Förbered extensions
    extensions = None
    if args_parsed.foto_only:
        extensions = [
            '.cr2', '.cr3', '.nef', '.arw', '.dng', '.iiq', '.3fr', '.orf', '.rw2', '.pef', # RAW
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.psd', '.gif', '.bmp', '.webp', '.svg', # Standard bild
            '.mp4', '.mov', '.avi', '.r3d', '.braw', '.mxf', '.mkv', '.wmv', '.m4v' # Video
        ]
    elif args_parsed.extensions:
        # Säkerställ att extensions börjar med punkt
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args_parsed.extensions]
    else:
        # Om varken --foto-only eller --extensions är angivna, använd DEFAULT_INCLUDE_EXTENSIONS
        # Detta innebär att ALLA filer (baserat på defaultlista) inkluderas om ingen restriktion anges
        # Du kan ändra detta till att inkludera *alla* filer om du vill, genom att sätta extensions till None här.
        extensions = DEFAULT_INCLUDE_EXTENSIONS 

    # Förbered output-filnamn
    output_file = args_parsed.output
    safe_name = ""
    if not output_file:
        disk_name = os.path.basename(args_parsed.path.rstrip(os.sep)) or 'UnknownDisk'
        logger.debug(f"Debug cli_parser: disk_name = '{disk_name}'")
        safe_name = re.sub(r'[^\w\-_\.]', '_', disk_name)
        logger.debug(f"Debug cli_parser: safe_name = '{safe_name}'")
        output_file = f"{safe_name}.json"
    else:
        # Om en output-fil angavs, generera safe_name från den
        base_output_name = os.path.basename(output_file)
        safe_name = re.sub(r'[^\w\-_\.]', '_', base_output_name.replace('.json', ''))
    
    logger.debug(f"Debug cli_parser: final output_file generated = '{output_file}'")

    return {
        'path': args_parsed.path,
        'output_file': output_file,
        'include_extensions': extensions,
        # FIX FÖR 'NoneType' error: Säkerställ att exclude_patterns alltid är en lista
        'exclude_patterns': args_parsed.exclude or [], # <-- ÄNDRING HÄR
        'no_label': args_parsed.no_label,
        'no_resume': args_parsed.no_resume,
        'checkpoint_interval': args_parsed.checkpoint_interval,
        'max_depth': args_parsed.max_depth,
        'follow_symlinks': args_parsed.follow_symlinks,
        'disk_safe_name': safe_name,
        'log_level': args_parsed.log_level.upper()
    }