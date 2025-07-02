import React, { useState, useCallback } from 'react';
import {
  Text,
  Button,
  Card,
  Badge,
  Spinner,
  ProgressBar,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogContent,
  DialogBody,
  DialogActions,
  MessageBar,
  MessageBarTitle,
  MessageBarBody,
  tokens
} from '@fluentui/react-components';
import {
  CloudArrowUp20Regular,
  Document20Regular,
  Checkmark20Regular,
  Dismiss20Regular,
  Warning20Regular,
  CalendarLtr20Regular,
  Storage20Regular
} from '@fluentui/react-icons';

// Import API functions
import { 
  checkDuplicate,
  uploadDiskPackageAsync, 
  connectToProgressStream 
} from '../../utils/api';

const Upload = () => {
  const [files, setFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadDetails, setUploadDetails] = useState('');
  const [results, setResults] = useState([]);
  const [eventSource, setEventSource] = useState(null);

  // Duplicate check state
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState(null);
  const [fileToUpload, setFileToUpload] = useState(null);

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
  };

  const checkForDuplicates = async (file) => {
    try {
      console.log('🔍 Checking for duplicates...');
      const duplicateResult = await checkDuplicate(file);
      
      if (duplicateResult.duplicate_found) {
        console.log('⚠️ Duplicate found:', duplicateResult);
        setDuplicateInfo(duplicateResult);
        setFileToUpload(file);
        setDuplicateDialogOpen(true);
        return true; // Duplicate found, stop upload
      } else {
        console.log('✅ No duplicate found, proceeding with upload');
        return false; // No duplicate, proceed with upload
      }
    } catch (error) {
      console.error('❌ Duplicate check failed:', error);
      // If duplicate check fails, ask user what to do
      const proceed = window.confirm(
        `Kunde inte kontrollera om filen redan finns: ${error.message}\n\nVill du fortsätta med upload ändå?`
      );
      return !proceed; // Return true to stop upload if user says no
    }
  };

  const startUpload = async (file, replaceExisting = false) => {
    console.log('🚀 Starting upload process...');
    
    setUploading(true);
    setUploadProgress(0);
    setUploadStatus('Startar upload...');
    setUploadDetails('');
    setResults([]);

    try {
      // Start async upload
      const uploadResult = await uploadDiskPackageAsync(file);
      console.log('📤 Upload started:', uploadResult);
      
      if (!uploadResult.task_id) {
        throw new Error('Inget task_id returnerades från servern');
      }

      // Connect to progress stream
      const progressConnection = connectToProgressStream(
        uploadResult.task_id,
        (progressData) => {
          console.log('📈 Progress update:', progressData);
          setUploadProgress(progressData.progress || 0);
          setUploadStatus(progressData.message || 'Laddar upp...');
          setUploadDetails(progressData.details || '');
        },
        (result) => {
          console.log('✅ Upload completed:', result);
          setUploadProgress(100);
          setUploadStatus('Upload slutförd!');
          setUploadDetails(`${result.files_imported} filer importerade`);
          setResults([{
            file: file.name,
            status: 'success',
            message: `Framgångsrikt importerad: ${result.disk_name}`,
            data: result
          }]);
          setUploading(false);
          
          // Clear files after successful upload
          setTimeout(() => {
            setFiles([]);
            setUploadProgress(0);
            setUploadStatus('');
            setUploadDetails('');
          }, 3000);
        },
        (error) => {
          console.error('❌ Upload failed:', error);
          setUploadStatus('Upload misslyckades');
          setUploadDetails(error.message);
          setResults([{
            file: file.name,
            status: 'error',
            message: error.message
          }]);
          setUploading(false);
        }
      );

      setEventSource(progressConnection);

    } catch (error) {
      console.error('❌ Upload error:', error);
      setUploadStatus('Upload misslyckades');
      setUploadDetails(error.message);
      setResults([{
        file: file.name,
        status: 'error',
        message: error.message
      }]);
      setUploading(false);
    }
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    
    const file = files[0]; // For now, handle one file at a time
    
    // Check for duplicates first
    const duplicateFound = await checkForDuplicates(file);
    
    if (!duplicateFound) {
      // No duplicate, proceed with upload
      await startUpload(file);
    }
    // If duplicate found, dialog will handle the rest
  };

  const handleDuplicateReplace = async () => {
    // User chose to replace existing disk
    setDuplicateDialogOpen(false);
    console.log('🔄 User chose to replace existing disk');
    
    if (fileToUpload) {
      await startUpload(fileToUpload, true);
    }
    
    // Clean up
    setDuplicateInfo(null);
    setFileToUpload(null);
  };

  const handleDuplicateCancel = () => {
    // User chose not to upload
    setDuplicateDialogOpen(false);
    console.log('❌ User cancelled upload due to duplicate');
    
    // Clean up
    setDuplicateInfo(null);
    setFileToUpload(null);
    setFiles([]); // Clear selected files
  };

  const cancelUpload = () => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
    setUploading(false);
    setUploadProgress(0);
    setUploadStatus('Upload avbruten');
    setUploadDetails('');
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Okänt datum';
    try {
      return new Date(dateString).toLocaleDateString('sv-SE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Okänt datum';
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Text size={700} weight="bold" block style={{ marginBottom: '8px' }}>
          <CloudArrowUp20Regular style={{ marginRight: '8px' }} />
          Ladda upp hårddisk-index
        </Text>
        <Text>Ladda upp JSON-filer från indexering-scriptet för att importera nya hårddiskar</Text>
      </div>

      {/* Upload Area */}
      <div
        style={{
          border: `2px dashed ${dragOver ? tokens.colorBrandStroke1 : tokens.colorNeutralStroke2}`,
          borderRadius: tokens.borderRadiusMedium,
          padding: '48px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: dragOver ? tokens.colorBrandBackground2 : tokens.colorNeutralBackground1,
          marginBottom: '24px'
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById('fileInput').click()}
      >
        <CloudArrowUp20Regular style={{ fontSize: '48px', marginBottom: '16px', color: tokens.colorBrandForeground1 }} />
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
        style={{ display: 'none' }}
        onChange={handleFileSelect}
      />

      {/* Selected Files */}
      {files.length > 0 && (
        <Card style={{ marginBottom: '24px', padding: '16px' }}>
          <Text weight="semibold" block style={{ marginBottom: '12px' }}>
            Valda filer ({files.length}):
          </Text>
          {files.map((file, index) => (
            <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
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
              style={{ marginRight: '8px' }}
            >
              {uploading ? 'Laddar upp...' : 'Starta upload'}
            </Button>
            
            {uploading && (
              <Button
                appearance="secondary"
                onClick={cancelUpload}
              >
                Avbryt
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* Upload Progress */}
      {uploading && (
        <Card style={{ marginBottom: '24px', padding: '16px' }}>
          <Text weight="semibold" block style={{ marginBottom: '8px' }}>
            {uploadStatus}
          </Text>
          <ProgressBar value={uploadProgress / 100} style={{ marginBottom: '8px' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <Text size={200}>{uploadDetails}</Text>
            <Text size={200}>{Math.round(uploadProgress)}%</Text>
          </div>
        </Card>
      )}

      {/* Results */}
      {results.length > 0 && (
        <Card style={{ padding: '16px' }}>
          <Text weight="semibold" block style={{ marginBottom: '12px' }}>
            Resultat:
          </Text>
          {results.map((result, index) => (
            <MessageBar
              key={index}
              intent={result.status === 'success' ? 'success' : 'error'}
              style={{ marginBottom: '8px' }}
            >
              <MessageBarBody>
                <MessageBarTitle>
                  {result.status === 'success' ? (
                    <Checkmark20Regular style={{ marginRight: '4px' }} />
                  ) : (
                    <Dismiss20Regular style={{ marginRight: '4px' }} />
                  )}
                  {result.file}
                </MessageBarTitle>
                {result.message}
                {result.data && (
                  <div style={{ marginTop: '8px', fontSize: '12px' }}>
                    {result.data.files_imported} filer, {result.data.directories_created} mappar, {result.data.total_size_mb} MB
                  </div>
                )}
              </MessageBarBody>
            </MessageBar>
          ))}
        </Card>
      )}

      {/* Duplicate Check Dialog */}
      <Dialog open={duplicateDialogOpen} onOpenChange={(event, data) => setDuplicateDialogOpen(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Warning20Regular style={{ color: tokens.colorPaletteYellowForeground1 }} />
                Hårddisk finns redan
              </div>
            </DialogTitle>
            <DialogContent>
              {duplicateInfo && (
                <div>
                  <Text block style={{ marginBottom: '16px' }}>
                    En hårddisk med namnet <strong>"{duplicateInfo.existing_disk.name}"</strong> har redan laddats upp.
                  </Text>
                  
                  <Card style={{ padding: '12px', marginBottom: '16px', backgroundColor: tokens.colorNeutralBackground2 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <Storage20Regular style={{ fontSize: '16px' }} />
                      <Text weight="semibold">{duplicateInfo.existing_disk.name}</Text>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <CalendarLtr20Regular style={{ fontSize: '14px', color: tokens.colorNeutralForeground2 }} />
                      <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
                        Laddades upp: {formatDate(duplicateInfo.existing_disk.created_at)}
                      </Text>
                    </div>
                  </Card>
                  
                  <Text block style={{ marginBottom: '16px' }}>
                    Vill du ersätta den befintliga hårddisken med den nya?
                  </Text>
                  
                  <MessageBar intent="warning">
                    <MessageBarBody>
                      <MessageBarTitle>Varning!</MessageBarTitle>
                      Om du ersätter kommer all befintlig data för denna hårddisk att raderas permanent.
                    </MessageBarBody>
                  </MessageBar>
                </div>
              )}
            </DialogContent>
            <DialogActions>
              <DialogTrigger disableButtonEnhancement>
                <Button 
                  appearance="secondary"
                  onClick={handleDuplicateCancel}
                >
                  Avbryt upload
                </Button>
              </DialogTrigger>
              <Button
                appearance="primary"
                onClick={handleDuplicateReplace}
                style={{ 
                  backgroundColor: tokens.colorPaletteYellowBackground3,
                  borderColor: tokens.colorPaletteYellowBorder2
                }}
              >
                Ersätt befintlig
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  );
};

export default Upload;