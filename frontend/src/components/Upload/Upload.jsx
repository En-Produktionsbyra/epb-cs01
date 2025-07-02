import React, { useState, useRef } from 'react';
import {
  Button,
  Text,
  Card,
  Badge,
  ProgressBar,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Spinner,
  tokens
} from '@fluentui/react-components';
import {
  CloudArrowUp20Regular,
  Document20Regular,
  Storage20Regular,
  CalendarLtr20Regular,
  Dismiss20Regular
} from '@fluentui/react-icons';
import { uploadDiskPackageAsync, connectToProgressStream, checkDuplicate } from '../../utils/api';

const Upload = () => {
  const [files, setFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [checkingDuplicate, setCheckingDuplicate] = useState(false); // NY STATE
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadDetails, setUploadDetails] = useState('');
  const [results, setResults] = useState([]);
  const [eventSource, setEventSource] = useState(null);
  
  // Duplicate dialog states
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState(null);
  const [fileToUpload, setFileToUpload] = useState(null);

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
    const droppedFiles = Array.from(e.dataTransfer.files);
    const jsonFiles = droppedFiles.filter(file => 
      file.name.toLowerCase().endsWith('.json') || file.type === 'application/json'
    );
    
    if (jsonFiles.length === 0) {
      alert('Endast JSON-filer accepteras');
      return;
    }
    
    setFiles(jsonFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const jsonFiles = selectedFiles.filter(file => 
      file.name.toLowerCase().endsWith('.json') || file.type === 'application/json'
    );
    
    if (jsonFiles.length === 0) {
      alert('Endast JSON-filer accepteras');
      return;
    }
    
    setFiles(jsonFiles);
  };

  const checkForDuplicates = async (file) => {
    setCheckingDuplicate(true); // STARTA LOADING
    
    try {
      const duplicateResult = await checkDuplicate(file);
      
      if (duplicateResult.duplicate_found) {
        // Duplicate found, show dialog
        setDuplicateInfo(duplicateResult);
        setFileToUpload(file);
        setDuplicateDialogOpen(true);
        return true; // Stop upload process
      }
      
      return false; // No duplicate, continue with upload
    } catch (error) {
      console.error('❌ Duplicate check failed:', error);
      // If duplicate check fails, ask user what to do
      const proceed = window.confirm(
        `Kunde inte kontrollera om filen redan finns: ${error.message}\n\nVill du fortsätta med upload ändå?`
      );
      return !proceed; // Return true to stop upload if user says no
    } finally {
      setCheckingDuplicate(false); // STOPPA LOADING
    }
  };

  const startUpload = async (file, replaceExisting = false) => {
    console.log('🚀 Starting upload process...', 'Replace existing:', replaceExisting);
    
    setUploading(true);
    setUploadProgress(0);
    setUploadStatus('Startar upload...');
    setUploadDetails('');
    setResults([]);

    try {
      // Start async upload MED replaceExisting parameter
      const uploadResult = await uploadDiskPackageAsync(file, replaceExisting);
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
          
          // Uppdaterat meddelande för ersättning
          const message = replaceExisting 
            ? `Befintlig disk ersatt: ${result.disk_name}`
            : `Framgångsrikt importerad: ${result.disk_name}`;
            
          setResults([{
            file: file.name,
            status: 'success',
            message: message,
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
    
    // Check for duplicates first (med loading state)
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

  const isProcessing = uploading || checkingDuplicate;

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
          cursor: isProcessing ? 'not-allowed' : 'pointer',
          backgroundColor: dragOver ? tokens.colorBrandBackground2 : tokens.colorNeutralBackground1,
          marginBottom: '24px',
          opacity: isProcessing ? 0.6 : 1
        }}
        onDragOver={isProcessing ? undefined : handleDragOver}
        onDragLeave={isProcessing ? undefined : handleDragLeave}
        onDrop={isProcessing ? undefined : handleDrop}
        onClick={isProcessing ? undefined : () => document.getElementById('fileInput').click()}
      >
        <CloudArrowUp20Regular style={{ 
          fontSize: '48px', 
          marginBottom: '16px', 
          color: tokens.colorBrandForeground1 
        }} />
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
        disabled={isProcessing}
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
              disabled={isProcessing}
              style={{ marginRight: '8px' }}
              icon={checkingDuplicate ? <Spinner size="tiny" /> : undefined}
            >
              {checkingDuplicate ? 'Kontrollerar...' : (uploading ? 'Laddar upp...' : 'Ladda upp')}
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

      {/* Loading State för Duplicate Check */}
      {checkingDuplicate && (
        <Card style={{ marginBottom: '24px', padding: '16px', textAlign: 'center' }}>
          <Spinner size="medium" style={{ marginBottom: '12px' }} />
          <Text weight="semibold" block style={{ marginBottom: '8px' }}>
            Kontrollerar duplicat...
          </Text>
          <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
            Söker efter befintlig disk med samma namn
          </Text>
        </Card>
      )}

      {/* Upload Progress */}
      {uploading && (
        <Card style={{ marginBottom: '24px', padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Spinner size="small" />
            <Text weight="semibold">{uploadStatus}</Text>
          </div>
          
          <ProgressBar value={uploadProgress} max={100} style={{ marginBottom: '8px' }} />
          
          <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
            {uploadDetails}
          </Text>
        </Card>
      )}

      {/* Results */}
      {results.length > 0 && (
        <Card style={{ marginBottom: '24px', padding: '16px' }}>
          <Text weight="semibold" block style={{ marginBottom: '12px' }}>
            Resultat:
          </Text>
          {results.map((result, index) => (
            <div key={index} style={{ 
              padding: '12px', 
              borderRadius: tokens.borderRadiusMedium,
              backgroundColor: result.status === 'success' 
                ? tokens.colorPaletteGreenBackground1 
                : tokens.colorPaletteRedBackground1,
              marginBottom: '8px'
            }}>
              <Text weight="semibold" style={{ 
                color: result.status === 'success' 
                  ? tokens.colorPaletteGreenForeground1 
                  : tokens.colorPaletteRedForeground1 
              }}>
                {result.status === 'success' ? '✅' : '❌'} {result.file}
              </Text>
              <Text block style={{ marginTop: '4px' }}>
                {result.message}
              </Text>
            </div>
          ))}
        </Card>
      )}

      {/* Duplicate Dialog */}
      <Dialog open={duplicateDialogOpen} onOpenChange={(event, data) => setDuplicateDialogOpen(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Storage20Regular style={{ color: tokens.colorPaletteRedForeground1 }} />
                Disk finns redan
              </div>
            </DialogTitle>
            <DialogContent>
              {duplicateInfo && (
                <div>
                  <Text block style={{ marginBottom: '16px' }}>
                    En hårddisk med samma namn finns redan:
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
                  backgroundColor: tokens.colorPaletteRedBackground3,
                  borderColor: tokens.colorPaletteRedBorder2
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