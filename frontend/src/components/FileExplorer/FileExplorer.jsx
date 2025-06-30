import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Text,
  Button,
  Spinner,
  Badge,
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
} from '@fluentui/react-components';
import {
  Storage20Regular,
  Document20Regular,
  Folder20Regular,
  ArrowLeft20Regular,
  FolderOpen20Regular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '16px',
    ...shorthands.padding('12px', '16px'),
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
  },
  breadcrumbContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  diskInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  content: {
    flex: 1,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  grid: {
    flex: 1,
    overflow: 'auto',
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

  // Extrahera nuvarande sökväg från URL
  const currentPath = location.pathname.includes('/browse/') 
    ? decodeURIComponent(location.pathname.split('/browse/')[1] || '')
    : '';

  useEffect(() => {
    if (diskId) {
      fetchDiskInfo();
      fetchDirectoryContents();
    }
  }, [diskId, currentPath]);

  const fetchDiskInfo = async () => {
    try {
      const response = await fetch(`http://localhost:8000/disks/${diskId}`);
      const data = await response.json();
      setDisk(data);
    } catch (err) {
      setError(`Kunde inte hämta disk info: ${err.message}`);
    }
  };

  const fetchDirectoryContents = async () => {
    setLoading(true);
    setError('');
    
    try {
      console.log(`⚡ Ultra-fast fetch for path: "${currentPath}"`);
      
      // Använd nya snabba browse-endpoint
      const params = new URLSearchParams();
      if (currentPath) {
        params.append('path', currentPath);
      }
      
      const response = await fetch(`http://localhost:8000/disks/${diskId}/browse?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`⚡ Got ${data.items?.length || 0} items instantly!`);
      
      setItems(data.items || []);
      
    } catch (err) {
      setError(`Kunde inte hämta kataloginnehåll: ${err.message}`);
      setItems([]);
    }
    
    setLoading(false);
  };

  const handleFolderClick = (folderName) => {
    const newPath = currentPath ? `${currentPath}/${folderName}` : folderName;
    navigate(`/disks/${diskId}/browse/${encodeURIComponent(newPath)}`);
  };

  const handleBreadcrumbClick = (path) => {
    if (path === '') {
      navigate(`/disks/${diskId}`);
    } else {
      navigate(`/disks/${diskId}/browse/${encodeURIComponent(path)}`);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '-';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('sv-SE');
  };

  const truncateText = (text, maxLength = 40) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // Breadcrumb items
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

  // DataGrid kolumner
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
            {truncateText(item.filename)}
            {item.type === 'folder' && item.file_count > 0 && (
              <Text size={200} style={{ marginLeft: '8px', color: tokens.colorNeutralForeground3 }}>
                ({item.file_count} filer)
              </Text>
            )}
          </Text>
        </TableCellLayout>
      ),
    }),
    createTableColumn({
      columnId: 'size',
      compare: (a, b) => (a.file_size || 0) - (b.file_size || 0),
      renderHeaderCell: () => 'Storlek',
      renderCell: (item) => (
        <Text style={{ textAlign: 'right', fontFamily: 'monospace' }}>
          {formatFileSize(item.file_size)}
        </Text>
      ),
    }),
    createTableColumn({
      columnId: 'type',
      renderHeaderCell: () => 'Typ',
      renderCell: (item) => (
        <Text>
          {item.type === 'folder' ? 'Mapp' : 
           item.filename?.split('.').pop()?.toUpperCase() || 'Fil'}
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
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spinner label="Laddar mapp..." size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '32px' }}>
        <Text style={{ color: tokens.colorPaletteRedForeground1 }}>{error}</Text>
        <br />
        <Button 
          appearance="primary" 
          onClick={fetchDirectoryContents}
          style={{ marginTop: '16px' }}
        >
          Försök igen
        </Button>
      </div>
    );
  }

  const folders = items.filter(item => item.type === 'folder');
  const files = items.filter(item => item.type === 'file');

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.breadcrumbContainer}>
          <Button
            appearance="subtle"
            icon={<ArrowLeft20Regular />}
            onClick={() => window.history.back()}
          >
            Tillbaka
          </Button>
          
          <Breadcrumb>
            {breadcrumbItems.map((item, index) => (
              <React.Fragment key={index}>
                <BreadcrumbItem>
                  <Button
                    appearance="subtle"
                    icon={index === 0 ? <Storage20Regular /> : <Folder20Regular />}
                    disabled={item.isLast}
                    onClick={() => handleBreadcrumbClick(item.path)}
                  >
                    {item.text}
                  </Button>
                </BreadcrumbItem>
                {index < breadcrumbItems.length - 1 && <BreadcrumbDivider />}
              </React.Fragment>
            ))}
          </Breadcrumb>
        </div>
        
        <div className={styles.diskInfo}>
          <Badge appearance="filled" color="brand">
            {folders.length} mappar
          </Badge>
          <Badge appearance="filled" color="success">
            {files.length} filer
          </Badge>
          <Badge appearance="tint">
            Total: {disk?.actual_file_count?.toLocaleString() || '0'} filer
          </Badge>
        </div>
      </div>

      {/* File/Folder Grid */}
      <div className={styles.content}>
        {items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <FolderOpen20Regular style={{ fontSize: '48px', color: tokens.colorNeutralForeground3, marginBottom: '16px' }} />
            <Text>Mappen är tom</Text>
          </div>
        ) : (
          <DataGrid
            items={items}
            columns={columns}
            sortable
            className={styles.grid}
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
                  style={{ cursor: item.type === 'folder' ? 'pointer' : 'default' }}
                  onClick={() => {
                    if (item.type === 'folder') {
                      handleFolderClick(item.filename);
                    }
                  }}
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
        )}
      </div>
    </div>
  );
};

export default FileExplorer;