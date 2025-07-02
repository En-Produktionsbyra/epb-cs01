import React, { useState, useEffect, useCallback } from 'react';
import {
  Text,
  Button,
  ProgressBar,
  Card,
  tokens,
  makeStyles,
  shorthands,
  Badge,
  Divider,
  Spinner,
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
} from '@fluentui/react-components';
import {
  DocumentArrowUp20Regular,
  DocumentArrowUp20Filled,
  CloudArrowUp24Regular,
  Database24Regular,
  CheckmarkCircle24Regular,
  ErrorCircle24Regular,
  Document24Regular,
  FolderOpen24Regular,
  Info24Regular,
  bundleIcon,
} from '@fluentui/react-icons';
import { uploadDiskPackageAsync, connectToProgressStream } from '../../utils/api';

const DocumentArrowUpIcon = bundleIcon(DocumentArrowUp20Filled, DocumentArrowUp20Regular);

const useStyles = makeStyles({
  container: {
    ...shorthands.padding('24px'),
    maxWidth: '800px',
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  dropZone: {
    ...shorthands.border('2px', 'dashed', tokens.colorNeutralStroke1),
    borderRadius: tokens.borderRadiusMedium,
    ...shorthands.padding('40px'),
    textAlign: 'center',
    backgroundColor: tokens.colorNeutralBackground2,
    cursor: 'pointer',
    transition: 'all 0.2s ease-in-out',
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground1,
      borderColor: tokens.colorBrandStroke1,
      transform: 'translateY(-1px)',
      boxShadow: tokens.shadow4,
    },
    '&.dragOver': {
      backgroundColor: tokens.colorBrandBackground2,
      borderColor: tokens.colorBrandStroke1,
      borderStyle: 'solid',
      transform: 'scale(1.01)',
      boxShadow: tokens.shadow8,
    },
  },
  dropZoneContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
  },
  fileList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  fileItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    ...shorthands.padding('12px'),
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusSmall,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  fileInfo: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
  },
  progressSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  statusRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  detailedStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    ...shorthands.padding('12px'),
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusSmall,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  resultsSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
});

// Upload är nu importerad från utils/api

const Upload = () => {
  const styles = useStyles();
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentStatus, setCurrentStatus] = useState('');
  const [currentStep, setCurrentStep] = useState('');
  const [detailedProgress, setDetailedProgress] = useState('');
  const [results, setResults] = useState([]);
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (selectedFiles) => {
    setFiles(selectedFiles);
    setResults([]);
  };

  const handleInputChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    handleFileSelect(selectedFiles);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/json' || file.name.endsWith('.json')
    );
    if (droppedFiles.length > 0) {
      handleFileSelect(droppedFiles);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
    return `${Math.round(bytes / (1024 * 1024))} MB`;
  };

  const uploadFiles = async () => {
    setUploading(true);
    setUploadProgress(0);
    setResults([]);
    setCurrentStatus('Startar upload...');
    setDetailedProgress('');

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      try {
        setCurrentStatus(`Startar upload av ${file.name}...`);
        
        // Starta upload och få task ID
        const uploadResponse = await uploadDiskPackageAsync(file);
        
        if (uploadResponse.success && uploadResponse.task_id) {
          setCurrentStatus(`Upload startad för ${file.name}, följer progress...`);
          
          // Anslut till progress stream med callbacks
          const eventSource = connectToProgressStream(
            uploadResponse.task_id,
            // onProgress callback
            (progressData) => {
              setUploadProgress(progressData.progress || 0);
              setCurrentStatus(progressData.message || '');
              setCurrentStep(progressData.step || '');
              setDetailedProgress(progressData.details || '');
            },
            // onComplete callback
            (result) => {
              setResults(prev => [...prev, {
                file: file.name,
                status: 'success',
                message: result.message,
                details: `Importerade ${result.files_imported} filer, ${result.directories_created} mappar`,
                data: result
              }]);
              setUploading(false);
            },
            // onError callback
            (error) => {
              setResults(prev => [...prev, {
                file: file.name,
                status: 'error',
                message: error.message,
                details: 'Import misslyckades'
              }]);
              setUploading(false);
            }
          );
          
          // Vänta på att denna fil ska bli klar
          await new Promise((resolve) => {
            const checkComplete = () => {
              if (!uploading || currentStep === 'complete' || currentStep === 'error') {
                resolve();
              } else {
                setTimeout(checkComplete, 500);
              }
            };
            
            // Timeout efter 5 minuter
            setTimeout(() => {
              eventSource.close();
              resolve();
            }, 300000);
            
            checkComplete();
          });
          
        } else {
          throw new Error('Upload misslyckades');
        }
        
      } catch (err) {
        setResults(prev => [...prev, {
          file: file.name,
          status: 'error',
          message: err.message,
          details: 'Upload eller processning misslyckades'
        }]);
      }
    }

    if (currentStep !== 'complete') {
      setCurrentStatus(`Slutförde ${files.length} fil(er).`);
      setUploading(false);
    }
  };

  const getStatusIcon = () => {
    switch (currentStep) {
      case 'parsing':
      case 'extracting':
        return <Info24Regular />;
      case 'preparing':
      case 'creating_disk':
        return <CloudArrowUp24Regular />;
      case 'importing':
      case 'directories':
        return <Database24Regular />;
      case 'complete':
        return <CheckmarkCircle24Regular />;
      case 'error':
        return <ErrorCircle24Regular />;
      default:
        return <DocumentArrowUpIcon />;
    }
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <DocumentArrowUpIcon />
        <Text as="h1" size={900} weight="bold">
          Ladda upp hårddisk-paket
        </Text>
      </div>
      
      {/* Description */}
      <MessageBar intent="info">
        <MessageBarBody>
          <MessageBarTitle>Information</MessageBarTitle>
          Välj eller dra JSON-filer som innehåller hårddisk-indexering för import till databasen.
        </MessageBarBody>
      </MessageBar>

      {/* Drop Zone */}
      <div 
        className={`${styles.dropZone} ${dragOver ? 'dragOver' : ''}`}
        onClick={() => document.getElementById('fileInput').click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        aria-label="Klicka för att välja filer eller dra och släpp JSON-filer här"
      >
        <input
          id="fileInput"
          type="file"
          multiple
          accept=".json,application/json"
          onChange={handleInputChange}
          style={{ display: 'none' }}
          aria-hidden="true"
        />
        <div className={styles.dropZoneContent}>
          <FolderOpen24Regular 
            primaryFill={dragOver ? tokens.colorBrandForeground1 : tokens.colorNeutralForeground2}
          />
          <Text size={500} weight="semibold">
            {dragOver ? 'Släpp filerna här' : 'Klicka här eller dra JSON-filer'}
          </Text>
          <Text size={300}>
            Stöder flera filer samtidigt (.json format)
          </Text>
        </div>
      </div>

      {/* Selected Files */}
      {files.length > 0 && (
        <Card>
          <div style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <Document24Regular />
              <Text size={400} weight="semibold">
                Valda filer
              </Text>
              <Badge size="small" appearance="filled" color="brand">
                {files.length}
              </Badge>
            </div>
            
            <Divider />
            
            <div className={styles.fileList} style={{ marginTop: '16px' }}>
              {files.map((file, index) => (
                <div key={index} className={styles.fileItem}>
                  <Document24Regular />
                  <div className={styles.fileInfo}>
                    <Text size={300} weight="medium">
                      {file.name}
                    </Text>
                    <Text size={200}>
                      {formatFileSize(file.size)}
                    </Text>
                  </div>
                </div>
              ))}
            </div>
            
            <Button
              appearance="primary"
              size="large"
              onClick={uploadFiles}
              disabled={uploading}
              icon={uploading ? <Spinner size="tiny" /> : <CloudArrowUp24Regular />}
              style={{ marginTop: '16px', width: '100%' }}
            >
              {uploading ? 'Processar...' : 'Starta upload'}
            </Button>
          </div>
        </Card>
      )}

      {/* Progress */}
      {uploading && (
        <Card>
          <div className={styles.progressSection} style={{ padding: '20px' }}>
            <ProgressBar 
              value={uploadProgress} 
              max={100}
              shape="rounded"
              thickness="large"
            />
            
            <div className={styles.statusRow}>
              {getStatusIcon()}
              <Text size={400} weight="medium">
                {currentStatus}
              </Text>
            </div>
            
            {detailedProgress && (
              <div className={styles.detailedStatus}>
                <Info24Regular />
                <Text size={300}>
                  {detailedProgress}
                </Text>
              </div>
            )}
            
            <Text size={300} weight="medium">
              {Math.round(uploadProgress)}% genomfört
            </Text>
          </div>
        </Card>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className={styles.resultsSection}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <CheckmarkCircle24Regular />
            <Text size={500} weight="semibold">
              Resultat
            </Text>
          </div>
          
          {results.map((result, index) => (
            <MessageBar
              key={index}
              intent={result.status === 'success' ? 'success' : 'error'}
            >
              <MessageBarBody>
                <MessageBarTitle>
                  {result.file}
                </MessageBarTitle>
                <div>
                  <Text size={300} style={{ display: 'block', marginBottom: '4px' }}>
                    {result.message}
                  </Text>
                  {result.details && (
                    <Text size={200}>
                      {result.details}
                    </Text>
                  )}
                </div>
              </MessageBarBody>
            </MessageBar>
          ))}
        </div>
      )}
    </div>
  );
};

export default Upload;