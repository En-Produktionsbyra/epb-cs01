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
} from '@fluentui/react-components';
import {
  Search20Regular,
  Document20Regular,
  Filter20Regular,
  Storage20Regular,
  Person20Regular,
  FolderOpen20Regular,
} from '@fluentui/react-icons';

import { fetchDisks as getDisks, searchFiles } from '../../utils/api';

const useStyles = makeStyles({
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.padding('24px'),
  },
  searchHeader: {
    marginBottom: '24px',
  },
  searchForm: {
    display: 'flex',
    gap: '12px',
    marginBottom: '16px',
    alignItems: 'end',
  },
  searchInput: {
    flex: 1,
    maxWidth: '400px',
  },
  filters: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
    alignItems: 'center',
    marginBottom: '16px',
  },
  filterDropdown: {
    minWidth: '150px',
  },
  results: {
    flex: 1,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  grid: {
    flex: 1,
    overflow: 'auto',
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
  },
  stats: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...shorthands.padding('12px', '0'),
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    marginBottom: '16px',
  },
  resultCard: {
    marginBottom: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    '&:hover': {
      transform: 'translateY(-1px)',
      boxShadow: tokens.shadow4,
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

  // Hämta diskar för filter
  useEffect(() => {
    loadDisks(); // Istället för fetchDisks
  }, []);

  // Synka URL med state
  useEffect(() => {
    const urlQuery = searchParams.get('q') || '';
    if (urlQuery !== query) {
      setQuery(urlQuery);
      if (urlQuery.length >= 3) {
        performSearch(urlQuery);
      }
    }
  }, [searchParams]);

  
  const loadDisks = async () => {
    try {
      const data = await getDisks();
      setDisks(data || []);
    } catch (err) {
      console.error('Kunde inte hämta diskar:', err);
      setDisks([]);
    }
  };

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
    // Navigera till filen i FileExplorer
    if (file.disk_id) {
      const path = file.file_path || '';
      if (path) {
        navigate(`/disks/${file.disk_id}/browse/${encodeURIComponent(path)}`);
      } else {
        navigate(`/disks/${file.disk_id}`);
      }
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
    // Förenklad - bara Document-ikon för nu
    return Document20Regular;
  };

  // DataGrid kolumner
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

  // Extrahera unika kunder och projekt från diskar
  const uniqueClients = [...new Set(disks.flatMap(d => d.top_clients?.map(c => c.client) || []))];
  const uniqueProjects = [...new Set(disks.flatMap(d => d.top_projects?.map(p => p.project) || []))];

  return (
    <div className={styles.container}>
      {/* Search Header */}
      <div className={styles.searchHeader}>
        <Text size={700} weight="bold" block style={{ marginBottom: '8px' }}>
          <Search20Regular style={{ marginRight: '8px' }} />
          Sök filer
        </Text>
        <Text>Sök efter filer, kunder, projekt eller filtyper</Text>
        
        <div className={styles.searchForm}>
          <Input
            className={styles.searchInput}
            placeholder="Skriv sökterm (minst 3 tecken)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyPress}
            contentBefore={<Search20Regular />}
          />
          <Button
            appearance="primary"
            onClick={handleSearch}
            disabled={!query.trim() || query.length < 3 || loading}
          >
            {loading ? 'Söker...' : 'Sök'}
          </Button>
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

            {/* Results Grid */}
            {results.length === 0 ? (
              <div className={styles.noResults}>
                <Search20Regular style={{ fontSize: '48px', marginBottom: '16px' }} />
                <Text size={500} weight="semibold" block style={{ marginBottom: '8px' }}>
                  Inga resultat hittades
                </Text>
                <Text>Prova att ändra din sökterm eller justera filtren</Text>
              </div>
            ) : (
              <DataGrid
                items={results}
                columns={columns}
                sortable
                className={styles.grid}
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
            )}
          </>
        )}

        {!hasSearched && (
          <div className={styles.noResults}>
            <Search20Regular style={{ fontSize: '64px', marginBottom: '16px', color: tokens.colorNeutralForeground3 }} />
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