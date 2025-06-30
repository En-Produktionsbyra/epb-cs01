import React, { useState, useCallback } from 'react';
import {
  Text,
  Button,
  Card,
  ProgressBar,
  makeStyles,
  tokens,
  shorthands,
  Badge,
} from '@fluentui/react-components';
import {
  CloudArrowUp20Regular,
  Document20Regular,
  CheckmarkCircle20Regular,
  ErrorCircle20Regular,
  Folder20Regular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.padding('24px'),
  },
  header: {
    marginBottom: '32px',
  },
  uploadArea: {
    borderTopWidth: '2px',
    borderRightWidth: '2px',
    borderBottomWidth: '2px',
    borderLeftWidth: '2px',
    borderTopStyle: 'dashed',
    borderRightStyle: 'dashed',
    borderBottomStyle: 'dashed',
    borderLeftStyle: 'dashed',
    borderTopColor: tokens.colorNeutralStroke2,
    borderRightColor: tokens.colorNeutralStroke2,
    borderBottomColor: tokens.colorNeutralStroke2,
    borderLeftColor: tokens.colorNeutralStroke2,
    borderRadius: '8px',
    ...shorthands.padding('48px', '24px'),
    textAlign: 'center',
    marginBottom: '24px',
    cursor: 'pointer',
    transitionProperty: 'all',
    transitionDuration: '0.2s',
    transitionTimingFunction: 'ease',
    '&:hover': {
      borderTopColor: tokens.colorBrandStroke1,
      borderRightColor: tokens.colorBrandStroke1,
      borderBottomColor: tokens.colorBrandStroke1,
      borderLeftColor: tokens.colorBrandStroke1,
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
    '&.dragover': {
      borderTopColor: tokens.colorBrandStroke1,
      borderRightColor: tokens.colorBrandStroke1,
      borderBottomColor: tokens.colorBrandStroke1,
      borderLeftColor: tokens.colorBrandStroke1,
      backgroundColor: tokens.colorBrandBackground2,
    },
  },
  uploadIcon: {
    fontSize: '48px',
    color: tokens.colorNeutralForeground3,
    marginBottom: '16px',
  },
  fileInput: {
    display: 'none',
  },
  uploadProgress: {
    marginTop: '16px',
  },
  results: {
    marginTop: '24px',
  },
  resultCard: {
    marginBottom: '12px',
    ...shorthands.padding('16px'),
  },
  success: {
    color: tokens.colorPaletteGreenForeground1,
  },
  error: {
    color: tokens.colorPaletteRedForeground1,
  },
  filePreview: {
    backgroundColor: tokens.colorNeutralBackground3,
    ...shorthands.padding('16px'),
    borderRadius: '8px',
    marginTop: '16px',
    fontFamily: 'monospace',
    fontSize: '12px',
    maxHeight: '200px',
    overflow: 'auto',
  },
});

const Upload = () => {
  const styles = useStyles();
  const [dragOver, setDragOver] = useState(false);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [results, setResults] = useState([]);
  const [previewData, setPreviewData] = useState(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  }, []);

  const handleFileSelect = useCallback((e) => {
    const selectedFiles = Array.from(e.target.files);
    handleFiles(selectedFiles);
  }, []);

  const handleFiles = (fileList) => {
    // Filtrera bara JSON-filer
    const jsonFiles = fileList.filter(file => 
      file.name.toLowerCase().endsWith('.json') || 
      file.type === 'application/json'
    );

    if (jsonFiles.length === 0) {
      alert('Endast JSON-filer accepteras');
      return;
    }

    setFiles(jsonFiles);
    
    // Preview första filen
    if (jsonFiles.length > 0) {
      previewFile(jsonFiles[0]);
    }
  };

  const previewFile = async (file) => {
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      setPreviewData(data);
    } catch (err) {
      console.error('Kunde inte läsa fil:', err);
      setPreviewData({ error: 'Ogiltig JSON-fil' });
    }
  };

  const uploadFiles = async () => {
    setUploading(true);
    setUploadProgress(0);
    setResults([]);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('http://localhost:8000/upload/json-index', {
          method: 'POST',
          body: formData,
        });

        const result = await response.json();

        if (response.ok) {
          setResults(prev => [...prev, {
            file: file.name,
            status: 'success',
            message: `Importerade ${result.files_imported} filer från ${result.disk_name}`,
            data: result
          }]);
        } else {
          setResults(prev => [...prev, {
            file: file.name,
            status: 'error',
            message: result.detail || 'Upload misslyckades'
          }]);
        }
      } catch (err) {
        setResults(prev => [...prev, {
          file: file.name,
          status: 'error',
          message: err.message
        }]);
      }

      setUploadProgress(((i + 1) / files.length) * 100);
    }

    setUploading(false);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <Text size={700} weight="bold" block style={{ marginBottom: '8px' }}>
          <CloudArrowUp20Regular style={{ marginRight: '8px' }} />
          Ladda upp hårddisk-index
        </Text>
        <Text>Ladda upp JSON-filer från indexering-scriptet för att importera nya hårddiskar</Text>
      </div>

      {/* Upload Area */}
      <div
        className={`${styles.uploadArea} ${dragOver ? 'dragover' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById('fileInput').click()}
      >
        <CloudArrowUp20Regular className={styles.uploadIcon} />
        <Text size={500} weight="semibold" block style={{ marginBottom: '8px' }}>
          Dra och släpp JSON-filer här
        </Text>
        <Text>eller klicka för att välja filer</Text>
        <Text size={200} style={{ marginTop: '8px', color: tokens.colorNeutralForeground2 }}>
          Accepterar .json filer från SimpleTreeIndexer
        </Text>
      </div>

      <input
        id="fileInput"
        type="file"
        multiple
        accept=".json,application/json"
        className={styles.fileInput}
        onChange={handleFileSelect}
      />

      {/* Selected Files */}
      {files.length > 0 && (
        <Card className={styles.resultCard}>
          <Text weight="semibold" block style={{ marginBottom: '12px' }}>
            Valda filer ({files.length}):
          </Text>
          {files.map((file, index) => (
            <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Document20Regular />
              <Text>{file.name}</Text>
              <Badge appearance="tint" size="small">
                {formatFileSize(file.size)}
              </Badge>
            </div>
          ))}
          
          <div style={{ marginTop: '16px' }}>
            <Button
              appearance="primary"
              onClick={uploadFiles}
              disabled={uploading}
            >
              {uploading ? 'Laddar upp...' : 'Ladda upp och importera'}
            </Button>
          </div>
        </Card>
      )}

      {/* Upload Progress */}
      {uploading && (
        <div className={styles.uploadProgress}>
          <Text style={{ marginBottom: '8px' }}>
            Laddar upp... {Math.round(uploadProgress)}%
          </Text>
          <ProgressBar value={uploadProgress / 100} />
        </div>
      )}

      {/* Preview */}
      {previewData && !previewData.error && (
        <Card className={styles.resultCard}>
          <Text weight="semibold" block style={{ marginBottom: '12px' }}>
            Förhandsvisning:
          </Text>
          <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
            <Badge appearance="filled" color="brand">
              <Folder20Regular style={{ marginRight: '4px' }} />
              {previewData.statistics?.total_directories || 0} mappar
            </Badge>
            <Badge appearance="filled" color="success">
              <Document20Regular style={{ marginRight: '4px' }} />
              {previewData.statistics?.total_files || 0} filer
            </Badge>
            <Badge appearance="tint">
              Skannad: {previewData.scan_info?.scan_date?.split('T')[0]}
            </Badge>
          </div>
          
          <div className={styles.filePreview}>
            <strong>Root path:</strong> {previewData.scan_info?.root_path}<br/>
            <strong>Scanner:</strong> {previewData.scan_info?.scanner} v{previewData.scan_info?.version}<br/>
            <strong>Filtyper:</strong> {Object.entries(previewData.statistics?.file_extensions || {}).map(([ext, count]) => `${ext}: ${count}`).join(', ')}<br/>
            <strong>Första mappar:</strong> {Object.keys(previewData.tree?.children || {}).slice(0, 5).join(', ')}
          </div>
        </Card>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className={styles.results}>
          <Text weight="semibold" block style={{ marginBottom: '16px' }}>
            Resultat:
          </Text>
          {results.map((result, index) => (
            <Card key={index} className={styles.resultCard}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {result.status === 'success' ? (
                  <CheckmarkCircle20Regular className={styles.success} />
                ) : (
                  <ErrorCircle20Regular className={styles.error} />
                )}
                <div>
                  <Text weight="semibold">{result.file}</Text>
                  <Text block size={200}>{result.message}</Text>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Upload;