import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Text,
  Button,
  Input,
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
  Dropdown,
  Option,
  SearchBox,
} from '@fluentui/react-components';
import {
  Search20Regular,
  Document20Regular,
  Filter20Regular,
  Storage20Regular,
  Person20Regular,
  FolderOpen20Regular,
  ChevronRight20Regular,
} from '@fluentui/react-icons';

import { fetchDisks as getDisks, searchFiles } from '../../utils/api';

const useStyles = makeStyles({
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.padding('24px'),
    // På mobil: mindre padding
    '@media (max-width: 768px)': {
      ...shorthands.padding('16px'),
    },
  },
  
  searchHeader: {
    marginBottom: '24px',
    // På mobil: mindre margin
    '@media (max-width: 768px)': {
      marginBottom: '16px',
    },
  },
  
  searchForm: {
    display: 'flex',
    justifyContent: "center",
    gap: '12px',
    marginBottom: '16px',
    alignItems: 'end',
    // På mobil: stack vertikalt
    '@media (max-width: 768px)': {
      flexDirection: 'column',
      alignItems: 'stretch',
      gap: '8px',
    },
  },
  
  searchInput: {
    flex: 1,
    width: '1000px',
    maxWidth: '100%',
    // På mobil: full bredd
    '@media (max-width: 768px)': {
      width: '100%',
    },
  },
  
  filters: {
    display: 'flex',
    justifyContent: "center",
    gap: '12px',
    flexWrap: 'wrap',
    alignItems: 'center',
    marginBottom: '16px',
    // På mobil: mindre gap
    '@media (max-width: 768px)': {
      gap: '8px',
    },
  },
  
  filterDropdown: {
    minWidth: '150px',
    // På mobil: mindre bredd
    '@media (max-width: 768px)': {
      minWidth: '120px',
      fontSize: tokens.fontSizeBase200,
    },
  },
  
  results: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  
  // Desktop: Grid view
  grid: {
    flex: 1,
    overflow: 'auto',
    display: 'flex',
    flexDirection: 'column',
    // Dölj på mobil
    '@media (max-width: 768px)': {
      display: 'none',
    },
  },
  
  // Mobile: List view
  mobileList: {
    flex: 1,
    overflow: 'auto',
    display: 'none',
    flexDirection: 'column',
    gap: '8px',
    // Visa bara på mobil
    '@media (max-width: 768px)': {
      display: 'flex',
    },
  },
  
  // Mobile result item
  mobileResultItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    ...shorthands.padding('12px', '16px'),
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    cursor: 'pointer',
    minHeight: '64px', // Touch-friendly
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
  
  fileIcon: {
    fontSize: '24px',
    flexShrink: 0,
    color: tokens.colorBrandForeground1,
  },
  
  fileContent: {
    flex: 1,
    minWidth: 0, // Allow text truncation
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  
  fileName: {
    fontWeight: tokens.fontWeightSemibold,
    fontSize: tokens.fontSizeBase300,
    lineHeight: tokens.lineHeightBase300,
    
    // Truncate long names
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  
  fileDetails: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flexWrap: 'wrap',
  },
  
  fileInfo: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
    fontFamily: 'monospace',
  },
  
  filePath: {
    fontSize: tokens.fontSizeBase100,
    color: tokens.colorNeutralForeground3,
    fontFamily: 'monospace',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    maxWidth: '200px',
  },
  
  mobileBadge: {
    fontSize: tokens.fontSizeBase100,
  },
  
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '200px',
  },
  
  noResults: {
    textAlign: 'center',
    ...shorthands.padding('48px', '24px'),
    color: tokens.colorNeutralForeground2,
    // På mobil: mindre padding
    '@media (max-width: 768px)': {
      ...shorthands.padding('32px', '16px'),
    },
  },
  
  stats: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...shorthands.padding('12px', '0'),
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    marginBottom: '16px',
    // På mobil: stack vertikalt om nödvändigt
    '@media (max-width: 480px)': {
      flexDirection: 'column',
      alignItems: 'flex-start',
      gap: '8px',
    },
  },
  
  pathCell: {
    fontFamily: 'monospace',
    fontSize: '12px',
    color: tokens.colorNeutralForeground2,
  },
});

const Search = () => {
  const styles = useStyles();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [clientFilter, setClientFilter] = useState('');
  const [projectFilter, setProjectFilter] = useState('');
  const [diskFilter, setDiskFilter] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const [disks, setDisks] = useState([]);
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Load disks for filters
  const loadDisks = async () => {
    try {
      const data = await getDisks();
      setDisks(data || []);
    } catch (err) {
      console.error('Kunde inte hämta diskar:', err);
      setDisks([]);
    }
  };

  useEffect(() => {
    loadDisks();
  }, []);

  // Sync URL with state
  useEffect(() => {
    const urlQuery = searchParams.get('q') || '';
    if (urlQuery !== query) {
      setQuery(urlQuery);
      if (urlQuery.length >= 3) {
        performSearch(urlQuery);
      }
    }
  }, [searchParams]);

  const performSearch = async (searchQuery = query) => {
    if (!searchQuery.trim() || searchQuery.length < 3) {
      setError('Sökterm måste vara minst 3 tecken');
      return;
    }

    setLoading(true);
    setError('');
    setHasSearched(true);

    try {
      const data = await searchFiles({
        q: searchQuery.trim(),
        per_page: 200,
        client: clientFilter || null,
        project: projectFilter || null,
        disk_id: diskFilter || null
      });
      setResults(data.files || []);
    } catch (err) {
      setError(err.message);
      setResults([]);
    }
    setLoading(false);
  };

  const handleSearch = () => {
    if (query.trim()) {
      setSearchParams({ q: query.trim() });
      performSearch();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleFileClick = (file) => {
    console.log('🔍 Search result clicked:', file);
    
    // Prioritera disk_name (läsbart), fallback till disk_id
    const diskIdentifier = file.disk_name || file.disk_id;
    
    if (!diskIdentifier) {
      console.error('❌ No disk identifier found in file:', file);
      alert('Kan inte hitta disk-information för denna fil');
      return;
    }
    
    // Navigera till FileExplorer med disk namn/id och sökväg
    const filePath = file.file_path || file.path || '';
    
    console.log(`🗂️ Navigation details:`, {
      diskIdentifier,
      filePath,
      filename: file.filename,
      usingDiskName: !!file.disk_name
    });
    
    if (filePath && filePath.trim() !== '') {
      // Navigera till den specifika mappen där filen finns
      console.log(`📁 Navigating to folder: ${diskIdentifier}, path: ${filePath}`);
      navigate(`/disks/${encodeURIComponent(diskIdentifier)}/browse/${encodeURIComponent(filePath)}`);
    } else {
      // Navigera till diskens root
      console.log(`💿 Navigating to disk root: ${diskIdentifier}`);
      navigate(`/disks/${encodeURIComponent(diskIdentifier)}`);
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

  const getFileIcon = (filename) => {
    const ext = filename?.split('.').pop()?.toLowerCase();
    return Document20Regular; // Simplified for now
  };

  // Desktop DataGrid columns
  const columns = [
    createTableColumn({
      columnId: 'name',
      compare: (a, b) => a.filename.localeCompare(b.filename),
      renderHeaderCell: () => 'Namn',
      renderCell: (item) => (
        <TableCellLayout
          media={React.createElement(getFileIcon(item.filename), { 
            style: { fontSize: '16px', color: tokens.colorBrandForeground1 } 
          })}
        >
          <Text weight="semibold">{truncateText(item.filename, 50)}</Text>
        </TableCellLayout>
      ),
    }),
    createTableColumn({
      columnId: 'path',
      compare: (a, b) => (a.file_path || '').localeCompare(b.file_path || ''),
      renderHeaderCell: () => 'Sökväg',
      renderCell: (item) => (
        <Text className={styles.pathCell}>
          {truncateText(item.file_path || 'Root', 60)}
        </Text>
      ),
    }),
    createTableColumn({
      columnId: 'disk',
      compare: (a, b) => (a.disk_name || '').localeCompare(b.disk_name || ''),
      renderHeaderCell: () => 'Hårddisk',
      renderCell: (item) => (
        <Badge appearance="filled" color="brand" size="small">
          {item.disk_name || item.disk_id}
        </Badge>
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
      columnId: 'client',
      compare: (a, b) => (a.client || '').localeCompare(b.client || ''),
      renderHeaderCell: () => 'Kund',
      renderCell: (item) => (
        item.client ? (
          <Badge appearance="tint" color="success" size="small">
            {item.client}
          </Badge>
        ) : (
          <Text>-</Text>
        )
      ),
    }),
    createTableColumn({
      columnId: 'project',
      compare: (a, b) => (a.project || '').localeCompare(b.project || ''),
      renderHeaderCell: () => 'Projekt',
      renderCell: (item) => (
        item.project ? (
          <Badge appearance="tint" color="warning" size="small">
            {item.project}
          </Badge>
        ) : (
          <Text>-</Text>
        )
      ),
    }),
  ];

  // Extract unique clients and projects from disks
  const uniqueClients = [...new Set(disks.flatMap(d => d.top_clients?.map(c => c.client) || []))];
  const uniqueProjects = [...new Set(disks.flatMap(d => d.top_projects?.map(p => p.project) || []))];

  return (
    <div className={styles.container}>
      {/* Search Header */}
      <div className={styles.searchHeader}>
        
        <div className={styles.searchForm}>
          <div >
        <Text size={700} weight="bold" block align="center" style={{ marginBottom: '8px' }}>
          Sök filer
        </Text>
        <Text block  align="center" >Sök efter filer, kunder, projekt eller filtyper</Text>
        <SearchBox
          className={styles.searchInput}
          placeholder="Skriv sökterm (minst 3 tecken)..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyPress}
          contentBefore={<Search20Regular />}
          size="large"                   /* nya props */
          style={{ height: '48px', fontSize: '16px' }}  /* större height/text */
          autoFocus                   /* sätter fokus direkt */
          clearButton                /* gör sökfältet sött med X-knapp */
          appearance="outline"
          onClear={() => {
            setQuery(''); setResults([]); setHasSearched(false);
          }}
        />
        </div>
        </div>

        {/* Filters */}
        <div className={styles.filters}>
          <Filter20Regular style={{ color: tokens.colorNeutralForeground2 }} />
          
          <Dropdown
            className={styles.filterDropdown}
            placeholder="Välj hårddisk"
            value={diskFilter}
            onSelectionChange={(e, data) => setDiskFilter(data.optionValue || '')}
          >
            <Option value="">Alla hårddiskar</Option>
            {disks.map(disk => (
              <Option key={disk.disk_id} value={disk.disk_id}>
                {disk.disk_name}
              </Option>
            ))}
          </Dropdown>

          <Dropdown
            className={styles.filterDropdown}
            placeholder="Välj kund"
            value={clientFilter}
            onSelectionChange={(e, data) => setClientFilter(data.optionValue || '')}
          >
            <Option value="">Alla kunder</Option>
            {uniqueClients.map(client => (
              <Option key={client} value={client}>
                {client}
              </Option>
            ))}
          </Dropdown>

          <Dropdown
            className={styles.filterDropdown}
            placeholder="Välj projekt"
            value={projectFilter}
            onSelectionChange={(e, data) => setProjectFilter(data.optionValue || '')}
          >
            <Option value="">Alla projekt</Option>
            {uniqueProjects.map(project => (
              <Option key={project} value={project}>
                {project}
              </Option>
            ))}
          </Dropdown>

          {(clientFilter || projectFilter || diskFilter) && (
            <Button
              appearance="subtle"
              onClick={() => {
                setClientFilter('');
                setProjectFilter('');
                setDiskFilter('');
              }}
            >
              Rensa filter
            </Button>
          )}
        </div>
      </div>

      {/* Results */}
      <div className={styles.results}>
        {loading && (
          <div className={styles.loading}>
            <Spinner label={`Söker efter "${query}"...`} size="large" />
          </div>
        )}

        {error && (
          <div className={styles.noResults}>
            <Text style={{ color: tokens.colorPaletteRedForeground1 }}>
              Fel vid sökning: {error}
            </Text>
          </div>
        )}

        {!loading && !error && hasSearched && (
          <>
            {/* Search Stats */}
            <div className={styles.stats}>
              <Text>
                {results.length > 0 
                  ? `${results.length.toLocaleString()} resultat för "${query}"`
                  : `Inga resultat för "${query}"`
                }
              </Text>
              {(clientFilter || projectFilter || diskFilter) && (
                <Text size={200}>
                  Filter aktiva
                </Text>
              )}
            </div>

            {/* Results */}
            {results.length === 0 ? (
              <div className={styles.noResults}>
                <Text size={500} weight="semibold" block style={{ marginBottom: '8px' }}>
                  Inga resultat hittades
                </Text>
                <Text>Prova att ändra din sökterm eller justera filtren</Text>
              </div>
            ) : (
              <>
                {/* Desktop: DataGrid */}
                <div className={styles.grid}>
                  <DataGrid
                    items={results}
                    columns={columns}
                    sortable
                    getRowId={(item, index) => `${item.disk_id}-${item.full_path}-${index}`}
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
                          style={{ cursor: 'pointer' }}
                          onClick={() => handleFileClick(item)}
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

                {/* Mobile: List View */}
                <div className={styles.mobileList}>
                  {results.map((item, index) => (
                    <div
                      key={`${item.disk_id}-${item.full_path}-${index}`}
                      className={styles.mobileResultItem}
                      onClick={() => handleFileClick(item)}
                    >
                      <div className={styles.fileIcon}>
                        <Document20Regular />
                      </div>
                      
                      <div className={styles.fileContent}>
                        <div className={styles.fileName}>
                          {item.filename}
                        </div>
                        
                        <div className={styles.fileDetails}>
                          {item.file_size && (
                            <Text className={styles.fileInfo}>
                              {formatFileSize(item.file_size)}
                            </Text>
                          )}
                          
                          {item.file_path && (
                            <Text className={styles.filePath}>
                              {item.file_path}
                            </Text>
                          )}
                          
                          {item.disk_name && (
                            <Badge appearance="filled" color="brand" size="small" className={styles.mobileBadge}>
                              {item.disk_name}
                            </Badge>
                          )}
                          
                          {item.client && (
                            <Badge appearance="tint" color="success" size="small" className={styles.mobileBadge}>
                              {item.client}
                            </Badge>
                          )}
                          
                          {item.project && (
                            <Badge appearance="tint" color="warning" size="small" className={styles.mobileBadge}>
                              {item.project}
                            </Badge>
                          )}
                        </div>
                      </div>
                      
                      <ChevronRight20Regular 
                        style={{ 
                          color: tokens.colorNeutralForeground2,
                          flexShrink: 0,
                        }} 
                      />
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}

        {!hasSearched && (
          <div className={styles.noResults}>
            <Text size={600} weight="semibold" block style={{ marginBottom: '8px' }}>
              Redo att söka
            </Text>
            <Text>Skriv minst 3 tecken för att börja söka efter filer</Text>
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;