# file_types.py

def determine_file_type(extension: str) -> str:
    """Bestäm fil-kategori baserat på extension"""
    if not extension:
        return 'other'
        
    ext = extension.lower().lstrip('.')
    
    # Bilder (inklusive RAW)
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'svg',
               'cr2', 'cr3', 'nef', 'arw', 'dng', 'iiq', '3fr', 'orf', 'rw2', 'pef',
               'dpx', 'exr', 'hdr']: # Lade till fler bildformat
        return 'image'
    
    # Video
    elif ext in ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg',
                 'r3d', 'braw', 'mxf', 'prores', 'mts', 'vob', 'ts', 'ogv']: # Lade till fler videoformat
        return 'video'
    
    # Audio
    elif ext in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'aiff', 'aif', 'm4a',
                 'opus', 'mid', 'midi']: # Lade till fler ljudformat
        return 'audio'
    
    # Dokument
    elif ext in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'pages', 'ai', 'eps', 'indd', 'psd',
                  'xlsx', 'xls', 'ppt', 'pptx', 'csv', 'md', 'xml', 'json', 'yml', 'yaml']: # Lade till fler dokument/dataformat
        return 'document'
    
    # Arkiv
    elif ext in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'dmg', 'iso', 'img', 'vhd', 'vmdk']: # Lade till fler arkiv/disk-image format
        return 'archive'
    
    # Kod/Data (generell)
    elif ext in ['js', 'jsx', 'ts', 'tsx', 'html', 'css', 'py', 'java', 'cpp', 'c', 'h', 'sql',
                  'sh', 'bat', 'cmd', 'ps1', 'php', 'rb', 'go', 'rs', 'swift', 'kt', 'json', 'xml', 'yml', 'yaml']:
        return 'code_data' # Ändrade till mer generell kategori

    # Fontfiler (ny kategori)
    elif ext in ['ttf', 'otf', 'woff', 'woff2']:
        return 'font'

    # 3D-modeller/CAD (ny kategori)
    elif ext in ['obj', 'fbx', 'gltf', 'glb', 'stl', 'cad', 'dwg', 'dxf']:
        return '3d_cad'
        
    else:
        return 'other'