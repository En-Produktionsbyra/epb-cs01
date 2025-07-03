# constants.py

# Default file extensions (bred täckning för foto/video-arkiv)
DEFAULT_INCLUDE_EXTENSIONS = [
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

# Default exclude patterns (regex)
DEFAULT_EXCLUDE_PATTERNS = [
    r'\.DS_Store$',
    r'Thumbs\.db$', 
    r'\.tmp$',
    r'\.temp$',
    r'__MACOSX',
    r'System Volume Information',
    r'\$RECYCLE\.BIN',
    r'\.VolumeIcon',
    r'\.localized', # Vanligt på macOS för lokaliserade mappar
    r'\.Trash', # Fånga fler typer av papperskorgar
    r'\$([A-Za-z0-9_]{2})', # Exkludera Windows systemmappar som $Recycle.Bin
]

# Root folders som alltid ska exkluderas oavsett djup
EXCLUDED_ROOT_FOLDERS = [
    'Backups.backupdb',
    '.Spotlight-V100', 
    '.TemporaryItems',
    '.Trashes',
    '.fseventsd',
    '$RECYCLE.BIN',
    'System Volume Information',
]

# System- och dolda mappar som ska filtreras bort från kundlistor
SYSTEM_AND_HIDDEN_FOLDERS = {
    '.fseventsd', 
    '.Spotlight-V100', 
    '.TemporaryItems', 
    '.Trashes',
    'Backups.backupdb',
    '.DS_Store',
    '.VolumeIcon.icns',
    '.disk_label',
    '.disk_label_2x',
    '.hedge-enabled', # Specifik för Hedge programvara
    '__MACOSX',
    'System Volume Information',
    '$RECYCLE.BIN',
    'Thumbs.db',
    # Lägg till fler om du stöter på dem
}

# Standard font sökvägar för PIL (ordning av preferens)
FONT_PATHS = [
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
    "/System/Library/Fonts/Arial.ttf",      # macOS
    "C:/Windows/Fonts/arial.ttf",           # Windows
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", # Linux (vanlig)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", # Linux (annan vanlig)
]

# LABEL GENERATION SETTINGS
LABEL_DPI = 900 # Hög DPI för utskriftskvalitet
LABEL_WIDTH_MM = 50 # Bredd på etiketten i millimeter (standard för Dymo 11352 är 54x25mm, men anpassar till 50x80mm för exempel)
LABEL_HEIGHT_MM = 80 # Höjd på etiketten i millimeter

# Marginaler i millimeter (konverteras till pixlar i label_generator.py)
MARGIN_MM = 3 # 3 mm marginal runt hela etiketten

# QR Code Settings
QR_CODE_SIZE_MM = 20 # Storlek på QR-koden i millimeter (på huvudetiketten)

# Fontstorlekar (startvärden för dynamisk skalning)
DEFAULT_DISK_NAME_FONT_SIZE = 120 # Startstorlek för diskens namn (huvudetikett & header)
DEFAULT_CUSTOMER_FONT_SIZE = 40 # Startstorlek för kundlista
DEFAULT_STATS_FONT_SIZE = 25 # Startstorlek för statistik