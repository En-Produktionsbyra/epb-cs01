/**
 * Formatera filstorlek till läsbart format
 */
export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
};

/**
 * Formatera datum till läsbart format
 */
export const formatDate = (dateString) => {
  if (!dateString) return 'Okänt datum';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('sv-SE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch (error) {
    return 'Ogiltigt datum';
  }
};

/**
 * Formatera datetime till kort format
 */
export const formatDateTime = (dateString) => {
  if (!dateString) return 'Okänt';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleString('sv-SE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return 'Ogiltigt datum';
  }
};

/**
 * Få filtyp-ikon baserat på filtyp
 */
export const getFileIcon = (filename, mimeType) => {
  if (!filename) return 'Document';
  
  const ext = filename.split('.').pop()?.toLowerCase();
  
  // Bilder
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'].includes(ext)) {
    return 'Photo2';
  }
  
  // Video
  if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(ext)) {
    return 'Video';
  }
  
  // Audio
  if (['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma'].includes(ext)) {
    return 'Music';
  }
  
  // Dokument
  if (['pdf'].includes(ext)) {
    return 'PDF';
  }
  
  if (['doc', 'docx'].includes(ext)) {
    return 'WordDocument';
  }
  
  if (['xls', 'xlsx'].includes(ext)) {
    return 'ExcelDocument';
  }
  
  if (['ppt', 'pptx'].includes(ext)) {
    return 'PowerPointDocument';
  }
  
  // Text
  if (['txt', 'rtf', 'md'].includes(ext)) {
    return 'TextDocument';
  }
  
  // Kod
  if (['js', 'jsx', 'ts', 'tsx', 'html', 'css', 'json', 'xml', 'yml', 'yaml'].includes(ext)) {
    return 'Code';
  }
  
  // Arkiv
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return 'ZipFolder';
  }
  
  // Mappar
  if (!ext) {
    return 'Folder';
  }
  
  return 'Document';
};

/**
 * Hämta färg baserat på filtyp
 */
export const getFileColor = (filename) => {
  if (!filename) return 'neutral';
  
  const ext = filename.split('.').pop()?.toLowerCase();
  
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'].includes(ext)) {
    return 'brand';
  }
  
  if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(ext)) {
    return 'danger';
  }
  
  if (['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma'].includes(ext)) {
    return 'success';
  }
  
  if (['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'].includes(ext)) {
    return 'warning';
  }
  
  return 'neutral';
};

/**
 * Trunkera lång text
 */
export const truncateText = (text, maxLength = 50) => {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * Formatera sökväg för visning
 */
export const formatPath = (path) => {
  if (!path) return '/';
  
  // Ta bort leading slash och ersätt med "/"
  return path.startsWith('/') ? path : `/${path}`;
};

/**
 * Extrahera mappnamn från sökväg
 */
export const getDirectoryName = (path) => {
  if (!path || path === '/') return 'Root';
  
  const parts = path.split('/').filter(Boolean);
  return parts[parts.length - 1] || 'Root';
};