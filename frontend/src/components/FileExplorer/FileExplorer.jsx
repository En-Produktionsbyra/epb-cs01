import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Text,
  Button,
  Spinner,
  Badge,
  Card,
  makeStyles,
  tokens,
  shorthands,
  DataGrid,
  DataGridHeader,
  DataGridHeaderCell,
  DataGridBody,
  DataGridRow,
  DataGridCell,
  TableCellLayout,
  createTableColumn,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbDivider,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogBody,
  Divider,
} from '@fluentui/react-components';
import {
  Storage20Regular,
  Document20Regular,
  Folder20Regular,
  ArrowLeft20Regular,
  FolderOpen20Regular,
  Warning20Regular,
  CheckmarkCircle20Regular,
  ChevronDown20Regular,
  Navigation20Regular,
  MoreHorizontal20Regular,
  Info20Regular,
  Calendar20Regular,
  Person20Regular,
  Tag20Regular,
  Shield20Regular,
  Dismiss20Regular,
} from '@fluentui/react-icons';
import { fetchDisk, browseDirectory } from '../../utils/api';

const useStyles = makeStyles({
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  
  // Mobile-first header
  header: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    marginBottom: '16px',
    ...shorthands.padding('12px', '16px'),
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    
    // Desktop: horizontal layout
    '@media (min-width: 769px)': {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
  },
  
  // Navigation row (back button + breadcrumb)
  navigationRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    minHeight: '44px', // Touch-friendly
  },
  
  // Stats row (badges)
  statsRow: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
    alignItems: 'center',
    
    // Desktop: align right
    '@media (min-width: 769px)': {
      justifyContent: 'flex-end',
    },
  },
  
  // Compact breadcrumb for mobile
  breadcrumb: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    flex: 1,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
    minWidth: 0, // Allow shrinking
    
    // Desktop: larger font
    '@media (min-width: 769px)': {
      fontSize: tokens.fontSizeBase300,
    },
  },
  
  breadcrumbButton: {
    backgroundColor: 'transparent',
    border: 'none',
    color: tokens.colorBrandForeground1,
    cursor: 'pointer',
    ...shorthands.padding('4px', '8px'),
    borderRadius: tokens.borderRadiusSmall,
    maxWidth: '100%', // Don't exceed container
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
  
  // Content area
  content: {
    flex: 1,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  
  // Mobile: List view
  mobileList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    overflow: 'auto',
    ...shorthands.padding('0', '16px'),
    
    // Desktop: hide mobile list
    '@media (min-width: 769px)': {
      display: 'none',
    },
  },
  
  // Desktop: Grid view
  desktopGrid: {
    flex: 1,
    overflow: 'auto',
    display: 'none',
    
    // Desktop: show grid
    '@media (min-width: 769px)': {
      display: 'flex',
      flexDirection: 'column',
    },
  },
  
  // File/folder item for mobile
  mobileItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    ...shorthands.padding('12px', '16px'),
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    cursor: 'pointer',
    minHeight: '56px', // Touch-friendly
    transition: 'all 0.2s ease',
    
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground1Hover,
      transform: 'translateY(-1px)',
      boxShadow: tokens.shadow4,
    },
    
    '&:active': {
      transform: 'translateY(0)',
    },
  },
  
  itemIcon: {
    fontSize: '24px',
    flexShrink: 0,
  },
  
  itemContent: {
    flex: 1,
    minWidth: 0, // Allow text truncation
  },
  
  itemName: {
    fontWeight: tokens.fontWeightSemibold,
    lineHeight: tokens.lineHeightBase300,
    marginBottom: '2px',
    
    // Truncate long names
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  
  itemDetails: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  
  // Path navigation menu
  pathMenu: {
    maxHeight: '300px',
    overflow: 'auto',
  },
  
  pathMenuItem: {
    minHeight: '44px',
    ...shorthands.padding('8px', '12px'),
  },
  
  // Loading and error states
  centerContent: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '200px',
    flexDirection: 'column',
    gap: '16px',
    textAlign: 'center',
    ...shorthands.padding('32px'),
  },
  
  errorCard: {
    marginBottom: '16px',
    ...shorthands.padding('16px'),
    backgroundColor: tokens.colorPaletteRedBackground1,
    borderLeft: `4px solid ${tokens.colorPaletteRedForeground1}`,
  },

  // File details dialog
  fileDialog: {
    minWidth: '90vw',
    maxWidth: '95vw',
    
    // Desktop: larger dialog
    '@media (min-width: 769px)': {
      minWidth: '500px',
      maxWidth: '600px',
    },
  },

  fileHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px',
  },

  fileIcon: {
    fontSize: '32px',
    flexShrink: 0,
  },

  fileName: {
    flex: 1,
    fontWeight: tokens.fontWeightSemibold,
    fontSize: tokens.fontSizeBase400,
    wordBreak: 'break-word',
  },

  detailsGrid: {
    display: 'grid',
    gap: '16px',
  },

  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '12px',
    ...shorthands.padding('8px', '0'),
  },

  detailLabel: {
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground2,
    minWidth: '100px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },

  detailValue: {
    flex: 1,
    textAlign: 'right',
    wordBreak: 'break-word',
    fontFamily: 'monospace',
    fontSize: tokens.fontSizeBase200,
  },

  badgeContainer: {
    display: 'flex',
    gap: '6px',
    flexWrap: 'wrap',
    justifyContent: 'flex-end',
  },

  copyButton: {
    fontSize: tokens.fontSizeBase100,
    minHeight: '24px',
    ...shorthands.padding('2px', '8px'),
  },
});

const FileExplorer = () => {
  const styles = useStyles();
  const { diskId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [disk, setDisk] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isMobile, setIsMobile] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showFileDialog, setShowFileDialog] = useState(false);

  // Extract current path from URL
  const currentPath = location.pathname.includes('/browse/') 
    ? decodeURIComponent(location.pathname.split('/browse/')[1] || '')
    : '';

  // Detect mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    if (diskId) {
      fetchDiskInfo();
      fetchDirectoryContents();
    }
  }, [diskId, currentPath]);

  const fetchDiskInfo = async () => {
    try {
      const data = await fetchDisk(diskId);
      setDisk(data);
    } catch (err) {
      setError(`Kunde inte hämta disk info: ${err.message}`);
    }
  };

  const fetchDirectoryContents = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await browseDirectory(diskId, currentPath || null);
      setItems(data.items || []);
    } catch (err) {
      setError(`Kunde inte hämta kataloginnehåll: ${err.message}`);
      setItems([]);
    }
    
    setLoading(false);
  };

  const handleItemClick = (item) => {
    if (item.type === 'folder') {
      const newPath = currentPath ? `${currentPath}/${item.filename}` : item.filename;
      navigate(`/disks/${diskId}/browse/${encodeURIComponent(newPath)}`);
    } else {
      // For files, show details dialog
      setSelectedFile(item);
      setShowFileDialog(true);
    }
  };

  const handlePathNavigation = (path) => {
    if (path === '') {
      navigate(`/disks/${diskId}`);
    } else {
      navigate(`/disks/${diskId}/browse/${encodeURIComponent(path)}`);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Okänt';
    try {
      return new Date(dateString).toLocaleDateString('sv-SE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Okänt';
    }
  };

  const getFileTypeIcon = (filename, mimeType) => {
    const ext = filename?.split('.').pop()?.toLowerCase();
    const mime = mimeType?.toLowerCase() || '';
    
    // Video files
    if (mime.startsWith('video/') || ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'].includes(ext)) {
      return '🎬';
    }
    // Image files
    if (mime.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)) {
      return '🖼️';
    }
    // Audio files
    if (mime.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg'].includes(ext)) {
      return '🎵';
    }
    // Archive files
    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(ext)) {
      return '📦';
    }
    // Document files
    if (['pdf', 'doc', 'docx', 'txt', 'rtf'].includes(ext)) {
      return '📄';
    }
    // Spreadsheet files
    if (['xls', 'xlsx', 'csv'].includes(ext)) {
      return '📊';
    }
    // Presentation files
    if (['ppt', 'pptx'].includes(ext)) {
      return '📈';
    }
    
    return '📄'; // Default
  };

  const copyToClipboard = async (text) => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        // Optionally show a toast/notification here
      } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  // Build the full path for display
  const getFullPath = (item) => {
    if (!item) return '';
    
    // Construct full path from current location + filename
    const basePath = currentPath ? `${currentPath}/${item.filename}` : item.filename;
    return basePath;
  };

  // Get display path (just the directory)
  const getDisplayPath = () => {
    return currentPath || '/';
  };

  // Generate breadcrumb items
  const breadcrumbItems = React.useMemo(() => {
    const items = [{ text: disk?.disk_name || diskId, path: '' }];
    
    if (currentPath) {
      const pathParts = currentPath.split('/').filter(Boolean);
      let buildPath = '';
      
      pathParts.forEach((part, index) => {
        buildPath += (buildPath ? '/' : '') + part;
        items.push({
          text: part,
          path: buildPath,
          isLast: index === pathParts.length - 1
        });
      });
    }
    
    return items;
  }, [disk, diskId, currentPath]);

  // Mobile-friendly breadcrumb display with smart truncation
  const getMobileBreadcrumb = () => {
    if (breadcrumbItems.length <= 1) {
      const text = breadcrumbItems[0]?.text || diskId;
      // Truncate disk name if too long
      return text.length > 20 ? `${text.substring(0, 17)}...` : text;
    }
    
    const current = breadcrumbItems[breadcrumbItems.length - 1];
    const root = breadcrumbItems[0].text;
    
    // Truncate current folder name if too long
    const truncatedCurrent = current.text.length > 25 
      ? `${current.text.substring(0, 22)}...` 
      : current.text;
    
    // Truncate root name if too long
    const truncatedRoot = root.length > 15 
      ? `${root.substring(0, 12)}...` 
      : root;
    
    if (breadcrumbItems.length === 2) {
      // Just root and current: "Root / Current"
      return `${truncatedRoot} / ${truncatedCurrent}`;
    }
    
    // Long path: always show "Root / ... / Current" regardless of length
    return `${truncatedRoot} / ... / ${truncatedCurrent}`;
  };

  // Desktop DataGrid columns
  const columns = [
    createTableColumn({
      columnId: 'name',
      compare: (a, b) => {
        if (a.type !== b.type) {
          return a.type === 'folder' ? -1 : 1;
        }
        return a.filename.localeCompare(b.filename);
      },
      renderHeaderCell: () => 'Namn',
      renderCell: (item) => (
        <TableCellLayout
          media={React.createElement(
            item.type === 'folder' ? Folder20Regular : Document20Regular, 
            { 
              style: { 
                fontSize: '16px', 
                color: item.type === 'folder' 
                  ? tokens.colorPaletteBlueForeground1 
                  : tokens.colorBrandForeground1 
              } 
            }
          )}
        >
          <Text weight={item.type === 'folder' ? 'semibold' : 'regular'}>
            {item.filename}
          </Text>
        </TableCellLayout>
      ),
    }),
    createTableColumn({
      columnId: 'size',
      compare: (a, b) => (a.file_size || 0) - (b.file_size || 0),
      renderHeaderCell: () => 'Storlek',
      renderCell: (item) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {item.type === 'folder' ? 'Mapp' : formatFileSize(item.file_size)}
        </Text>
      ),
    }),
    createTableColumn({
      columnId: 'modified',
      compare: (a, b) => new Date(a.modified_date || 0) - new Date(b.modified_date || 0),
      renderHeaderCell: () => 'Ändrad',
      renderCell: (item) => (
        <Text>{formatDate(item.modified_date)}</Text>
      ),
    }),
  ];

  if (loading) {
    return (
      <div className={styles.centerContent}>
        <Spinner label="Laddar katalog..." size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <Card className={styles.errorCard}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Warning20Regular style={{ color: tokens.colorPaletteRedForeground1 }} />
            <Text weight="semibold" style={{ color: tokens.colorPaletteRedForeground1 }}>
              Fel
            </Text>
          </div>
          <Text style={{ marginTop: '8px' }}>{error}</Text>
          <Button 
            appearance="primary" 
            onClick={fetchDirectoryContents}
            style={{ marginTop: '12px' }}
          >
            Försök igen
          </Button>
        </Card>
      </div>
    );
  }

  const folders = items.filter(item => item.type === 'folder');
  const files = items.filter(item => item.type === 'file');

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        {/* Navigation Row */}
        <div className={styles.navigationRow}>
          <Button
            appearance="subtle"
            icon={<ArrowLeft20Regular />}
            onClick={() => {
              if (currentPath) {
                const parentPath = currentPath.split('/').slice(0, -1).join('/');
                handlePathNavigation(parentPath);
              } else {
                navigate('/dashboard');
              }
            }}
            style={{ minHeight: '44px', minWidth: '44px' }}
          >
            {isMobile ? '' : 'Tillbaka'}
          </Button>
          
          {/* Mobile: Compact breadcrumb with dropdown */}
          {isMobile ? (
            <div className={styles.breadcrumb}>
              <Menu>
                <MenuTrigger>
                  <Button
                    appearance="subtle"
                    className={styles.breadcrumbButton}
                    iconAfter={breadcrumbItems.length > 1 ? <ChevronDown20Regular /> : null}
                  >
                    {getMobileBreadcrumb()}
                  </Button>
                </MenuTrigger>
                <MenuPopover>
                  <MenuList className={styles.pathMenu}>
                    {breadcrumbItems.map((item, index) => (
                      <MenuItem
                        key={index}
                        className={styles.pathMenuItem}
                        onClick={() => handlePathNavigation(item.path)}
                        disabled={item.isLast}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          {index === 0 ? <Storage20Regular /> : <Folder20Regular />}
                          <Text>{item.text}</Text>
                          {item.isLast && <Text>(nuvarande)</Text>}
                        </div>
                      </MenuItem>
                    ))}
                  </MenuList>
                </MenuPopover>
              </Menu>
            </div>
          ) : (
            /* Desktop: Original Fluent UI Breadcrumb */
            <Breadcrumb style={{ flex: 1 }}>
              {breadcrumbItems.map((item, index) => (
                <React.Fragment key={index}>
                  <BreadcrumbItem>
                    <div 
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '4px',
                        cursor: item.isLast ? 'default' : 'pointer',
                        opacity: item.isLast ? 0.6 : 1,
                        padding: '4px 8px',
                        borderRadius: tokens.borderRadiusSmall,
                      }}
                      onClick={() => !item.isLast && handlePathNavigation(item.path)}
                    >
                      {index === 0 ? <Storage20Regular /> : <Folder20Regular />}
                      {item.text}
                    </div>
                  </BreadcrumbItem>
                  {index < breadcrumbItems.length - 1 && <BreadcrumbDivider />}
                </React.Fragment>
              ))}
            </Breadcrumb>
          )}
        </div>
        
        {/* Stats Row */}
        <div className={styles.statsRow}>
          <Badge appearance="filled" color="brand" size={isMobile ? "medium" : "small"}>
            {folders.length} mappar
          </Badge>
          <Badge appearance="filled" color="success" size={isMobile ? "medium" : "small"}>
            {files.length} filer
          </Badge>
          {disk?.actual_file_count && (
            <Badge appearance="tint" size={isMobile ? "medium" : "small"}>
              Total: {disk.actual_file_count.toLocaleString()}
            </Badge>
          )}
        </div>
      </div>

      {/* Content */}
      <div className={styles.content}>
        {items.length === 0 ? (
          <div className={styles.centerContent}>
            <FolderOpen20Regular style={{ fontSize: '48px', color: tokens.colorNeutralForeground3 }} />
            <Text size={500} weight="semibold">
              Mappen är tom
            </Text>
          </div>
        ) : (
          <>
            {/* Mobile: List View */}
            <div className={styles.mobileList}>
              {items.map((item, index) => (
                <div
                  key={`${item.type}-${item.filename}-${index}`}
                  className={styles.mobileItem}
                  onClick={() => handleItemClick(item)}
                >
                  <div className={styles.itemIcon}>
                    {item.type === 'folder' ? (
                      <Folder20Regular style={{ color: tokens.colorPaletteBlueForeground1 }} />
                    ) : (
                      <Document20Regular style={{ color: tokens.colorBrandForeground1 }} />
                    )}
                  </div>
                  
                  <div className={styles.itemContent}>
                    <div className={styles.itemName}>
                      {item.filename}
                    </div>
                    <div className={styles.itemDetails}>
                      {item.type === 'folder' ? (
                        <Text>Mapp</Text>
                      ) : (
                        <>
                          {formatFileSize(item.file_size) && (
                            <Text>{formatFileSize(item.file_size)}</Text>
                          )}
                          {formatDate(item.modified_date) && (
                            <Text>{formatDate(item.modified_date)}</Text>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  
                  {item.type === 'folder' && (
                    <ChevronDown20Regular 
                      style={{ 
                        transform: 'rotate(-90deg)', 
                        color: tokens.colorNeutralForeground2 
                      }} 
                    />
                  )}
                </div>
              ))}
            </div>

            {/* Desktop: Grid View */}
            <div className={styles.desktopGrid}>
              <DataGrid
                items={items}
                columns={columns}
                sortable
                getRowId={(item, index) => `${item.type}-${item.filename}-${index}`}
              >
                <DataGridHeader>
                  <DataGridRow>
                    {({ renderHeaderCell }) => (
                      <DataGridHeaderCell>
                        {renderHeaderCell()}
                      </DataGridHeaderCell>
                    )}
                  </DataGridRow>
                </DataGridHeader>
                <DataGridBody>
                  {({ item, rowId }) => (
                    <DataGridRow 
                      key={rowId}
                      style={{ cursor: item.type === 'folder' ? 'pointer' : 'pointer' }}
                      onClick={() => handleItemClick(item)}
                    >
                      {({ renderCell }) => (
                        <DataGridCell>
                          {renderCell(item)}
                        </DataGridCell>
                      )}
                    </DataGridRow>
                  )}
                </DataGridBody>
              </DataGrid>
            </div>
          </>
        )}
      </div>

      {/* File Details Dialog */}
      <Dialog open={showFileDialog} onOpenChange={(event, data) => setShowFileDialog(data.open)}>
        <DialogSurface className={styles.fileDialog}>
          <DialogTitle>
            <div className={styles.fileHeader}>
              <div className={styles.fileIcon}>
                {selectedFile && getFileTypeIcon(selectedFile.filename, selectedFile.mime_type)}
              </div>
              <div className={styles.fileName}>
                {selectedFile?.filename}
              </div>
              <Button
                appearance="subtle"
                icon={<Dismiss20Regular />}
                onClick={() => setShowFileDialog(false)}
                aria-label="Stäng"
              />
            </div>
          </DialogTitle>
          
          <DialogBody>
            <DialogContent>
              {selectedFile && (
                <div className={styles.detailsGrid}>
                  {/* File Size */}
                  <div className={styles.detailRow}>
                    <div className={styles.detailLabel}>
                      <Info20Regular />
                      Storlek
                    </div>
                    <div className={styles.detailValue}>
                      {formatFileSize(selectedFile.file_size)}
                    </div>
                  </div>

                  {/* File Type & MIME */}
                  {selectedFile.file_type && (
                    <div className={styles.detailRow}>
                      <div className={styles.detailLabel}>
                        <Tag20Regular />
                        Filtyp
                      </div>
                      <div className={styles.detailValue}>
                        {selectedFile.file_type}
                        {selectedFile.mime_type && (
                          <Text style={{ display: 'block', fontSize: tokens.fontSizeBase100, color: tokens.colorNeutralForeground2 }}>
                            {selectedFile.mime_type}
                          </Text>
                        )}
                      </div>
                    </div>
                  )}

                  {/* File Path */}
                  <div className={styles.detailRow}>
                    <div className={styles.detailLabel}>
                      <Navigation20Regular />
                      Sökväg
                    </div>
                    <div className={styles.detailValue}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Text style={{ flex: 1, fontSize: tokens.fontSizeBase100 }}>
                          {getDisplayPath()}
                        </Text>
                        <Button
                          appearance="subtle"
                          size="small"
                          className={styles.copyButton}
                          onClick={() => copyToClipboard(getDisplayPath())}
                        >
                          Kopiera
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Full Path */}
                  <div className={styles.detailRow}>
                    <div className={styles.detailLabel}>
                      <Navigation20Regular />
                      Fullständig sökväg
                    </div>
                    <div className={styles.detailValue}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Text style={{ flex: 1, fontSize: tokens.fontSizeBase100 }}>
                          {getFullPath(selectedFile)}
                        </Text>
                        <Button
                          appearance="subtle"
                          size="small"
                          className={styles.copyButton}
                          onClick={() => copyToClipboard(getFullPath(selectedFile))}
                        >
                          Kopiera
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Created Date */}
                  {selectedFile.created_date && (
                    <div className={styles.detailRow}>
                      <div className={styles.detailLabel}>
                        <Calendar20Regular />
                        Skapad
                      </div>
                      <div className={styles.detailValue}>
                        {formatDate(selectedFile.created_date)}
                      </div>
                    </div>
                  )}

                  {/* Modified Date */}
                  {selectedFile.modified_date && (
                    <div className={styles.detailRow}>
                      <div className={styles.detailLabel}>
                        <Calendar20Regular />
                        Ändrad
                      </div>
                      <div className={styles.detailValue}>
                        {formatDate(selectedFile.modified_date)}
                      </div>
                    </div>
                  )}

                  <Divider />

                  {/* Client & Project */}
                  {(selectedFile.client || selectedFile.project) && (
                    <div className={styles.detailRow}>
                      <div className={styles.detailLabel}>
                        <Person20Regular />
                        Organisation
                      </div>
                      <div className={styles.badgeContainer}>
                        {selectedFile.client && (
                          <Badge appearance="tint" color="success" size="small">
                            {selectedFile.client}
                          </Badge>
                        )}
                        {selectedFile.project && (
                          <Badge appearance="tint" color="warning" size="small">
                            {selectedFile.project}
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Keywords */}
                  {selectedFile.keywords && (
                    <div className={styles.detailRow}>
                      <div className={styles.detailLabel}>
                        <Tag20Regular />
                        Nyckelord
                      </div>
                      <div className={styles.detailValue}>
                        {selectedFile.keywords}
                      </div>
                    </div>
                  )}

                  {/* Checksum - only show if available */}
                  {selectedFile.checksum && (
                    <div className={styles.detailRow}>
                      <div className={styles.detailLabel}>
                        <Shield20Regular />
                        Checksumma
                      </div>
                      <div className={styles.detailValue}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Text style={{ flex: 1, fontSize: tokens.fontSizeBase100, fontFamily: 'monospace' }}>
                            {selectedFile.checksum}
                          </Text>
                          <Button
                            appearance="subtle"
                            size="small"
                            className={styles.copyButton}
                            onClick={() => copyToClipboard(selectedFile.checksum)}
                          >
                            Kopiera
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Disk Info */}
                  <Divider />
                  <div className={styles.detailRow}>
                    <div className={styles.detailLabel}>
                      <Storage20Regular />
                      Hårddisk
                    </div>
                    <div className={styles.detailValue}>
                      <Badge appearance="filled" color="brand" size="small">
                        {disk?.disk_name || diskId}
                      </Badge>
                    </div>
                  </div>
                </div>
              )}
            </DialogContent>
          </DialogBody>

          <DialogActions>
            <Button appearance="primary" onClick={() => setShowFileDialog(false)}>
              Stäng
            </Button>
          </DialogActions>
        </DialogSurface>
      </Dialog>
    </div>
  );
};

export default FileExplorer;