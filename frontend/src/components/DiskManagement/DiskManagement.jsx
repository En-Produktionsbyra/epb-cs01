import React, { useState, useEffect } from 'react';
import {
  Text,
  Button,
  Card,
  CardHeader,
  CardPreview,
  CardFooter,
  Badge,
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
  Spinner,
  Table,
  TableHeader,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  tokens
} from '@fluentui/react-components';
import {
  Delete24Regular,
  Warning24Regular,
  CheckmarkCircle24Regular,
  Dismiss24Regular,
  Storage24Regular,
  DocumentFolder24Regular,
  CalendarLtr24Regular
} from '@fluentui/react-icons';

// Använd din befintliga API!
import { fetchDisks } from '../../utils/api';
import api from '../../utils/api';

const DiskManagement = () => {
  const [disks, setDisks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [diskToDelete, setDiskToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteSuccess, setDeleteSuccess] = useState('');

  useEffect(() => {
    loadDisks();
  }, []);

  const loadDisks = async () => {
    setLoading(true);
    setError('');
    
    try {
      console.log('🔍 Loading disks using api.js...');
      const data = await fetchDisks(); // Använd din befintliga funktion!
      console.log('✅ Disks loaded successfully:', data);
      setDisks(data);
    } catch (err) {
      console.error('❌ Failed to load disks:', err);
      setError(err.message);
    }
    
    setLoading(false);
  };

  const handleDeleteClick = (disk) => {
    setDiskToDelete(disk);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!diskToDelete) return;
    
    setIsDeleting(true);
    setError('');
    
    try {
      console.log('🗑️ Deleting disk:', diskToDelete.name);
      
      // Använd din API-instans för delete
      const response = await api.delete(`/disks/${encodeURIComponent(diskToDelete.name)}`);
      
      console.log('✅ Delete successful:', response.data);
      
      // Visa framgångsmeddelande
      setDeleteSuccess(`Disk "${diskToDelete.name}" har raderats framgångsrikt.`);
      
      // Uppdatera listan
      await loadDisks();
      
      // Stäng dialog
      setDeleteDialogOpen(false);
      setDiskToDelete(null);
      
      // Ta bort framgångsmeddelandet efter 5 sekunder
      setTimeout(() => setDeleteSuccess(''), 5000);
      
    } catch (err) {
      console.error('❌ Delete failed:', err);
      setError(`Kunde inte radera disk: ${err.message}`);
    }
    
    setIsDeleting(false);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setDiskToDelete(null);
  };

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      // Hantera olika datum-format
      let date;
      if (typeof dateString === 'string') {
        // Om det är en ISO string
        if (dateString.includes('T')) {
          date = new Date(dateString);
        } else {
          // Om det är ett annat format
          date = new Date(dateString);
        }
      } else {
        date = new Date(dateString);
      }
      
      // Kontrollera om datumet är giltigt
      if (isNaN(date.getTime())) {
        console.warn('⚠️ Invalid date:', dateString);
        return dateString; // Returnera originalsträngen om den inte kan parsas
      }
      
      return date.toLocaleDateString('sv-SE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.warn('⚠️ Date formatting error:', error, 'for date:', dateString);
      return dateString || '-';
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'imported':
        return <Badge appearance="filled" color="success">Importerad</Badge>;
      case 'active':
        return <Badge appearance="filled" color="success">Aktiv</Badge>;
      case 'error':
        return <Badge appearance="filled" color="danger">Fel</Badge>;
      default:
        return <Badge appearance="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '400px',
        gap: '16px'
      }}>
        <Spinner size="large" />
        <Text size={500}>Laddar diskar...</Text>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <Storage24Regular />
          <Text size={700} weight="bold">Hantera Diskar</Text>
        </div>
        <Text>Översikt och hantering av alla importerade diskar i systemet.</Text>
      </div>

      {/* Success Message */}
      {deleteSuccess && (
        <MessageBar intent="success" style={{ marginBottom: '16px' }}>
          <MessageBarBody>
            <MessageBarTitle>Framgång!</MessageBarTitle>
            {deleteSuccess}
          </MessageBarBody>
          <Button
            appearance="transparent"
            icon={<Dismiss24Regular />}
            onClick={() => setDeleteSuccess('')}
          />
        </MessageBar>
      )}

      {/* Error Message */}
      {error && (
        <MessageBar intent="error" style={{ marginBottom: '16px' }}>
          <MessageBarBody>
            <MessageBarTitle>Fel uppstod</MessageBarTitle>
            {error}
          </MessageBarBody>
          <Button
            appearance="transparent"
            icon={<Dismiss24Regular />}
            onClick={() => setError('')}
          />
        </MessageBar>
      )}

      {/* Statistics */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '16px', 
        marginBottom: '24px' 
      }}>
        <Card>
          <CardHeader
            header={<Text weight="semibold">Totalt antal diskar</Text>}
            description={<Text size={900} weight="bold">{disks.length}</Text>}
          />
        </Card>
        
        <Card>
          <CardHeader
            header={<Text weight="semibold">Totalt antal filer</Text>}
            description={
              <Text size={900} weight="bold">
                {disks.reduce((sum, disk) => sum + (disk.actual_file_count || 0), 0).toLocaleString()}
              </Text>
            }
          />
        </Card>
        
        <Card>
          <CardHeader
            header={<Text weight="semibold">Total storlek</Text>}
            description={
              <Text size={900} weight="bold">
                {formatFileSize(disks.reduce((sum, disk) => sum + (disk.actual_total_size || 0), 0))}
              </Text>
            }
          />
        </Card>
      </div>

      {/* Disks Table */}
      <Card>
        <CardHeader header={<Text weight="semibold">Alla Diskar</Text>} />
        <div style={{ overflowX: 'auto' }}>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Namn</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Antal filer</TableHeaderCell>
                <TableHeaderCell>Storlek</TableHeaderCell>
                <TableHeaderCell>Skapad</TableHeaderCell>
                <TableHeaderCell>Åtgärder</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {disks.map((disk) => (
                <TableRow key={disk.id}>
                  <TableCell>
                    <div>
                      <Text weight="semibold">{disk.name}</Text>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                        <DocumentFolder24Regular style={{ fontSize: '14px', color: tokens.colorNeutralForeground2 }} />
                        <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
                          ID: {disk.id}
                        </Text>
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    {getStatusBadge(disk.status)}
                  </TableCell>
                  
                  <TableCell>
                    <Text>{(disk.actual_file_count || 0).toLocaleString()}</Text>
                  </TableCell>
                  
                  <TableCell>
                    <Text>{formatFileSize(disk.actual_total_size)}</Text>
                  </TableCell>
                  
                  <TableCell>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CalendarLtr24Regular style={{ fontSize: '14px', color: tokens.colorNeutralForeground2 }} />
                      <Text size={200}>{formatDate(disk.created_at)}</Text>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <Button
                      appearance="subtle"
                      icon={<Delete24Regular />}
                      onClick={() => handleDeleteClick(disk)}
                      style={{ color: tokens.colorPaletteRedForeground1 }}
                    >
                      Ta bort
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        
        {disks.length === 0 && (
          <div style={{ 
            padding: '48px', 
            textAlign: 'center',
            color: tokens.colorNeutralForeground2 
          }}>
            <Storage24Regular style={{ fontSize: '48px', marginBottom: '16px' }} />
            <Text>Inga diskar hittades</Text>
          </div>
        )}
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={(event, data) => setDeleteDialogOpen(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Warning24Regular style={{ color: tokens.colorPaletteRedForeground1 }} />
                Bekräfta borttagning
              </div>
            </DialogTitle>
            <DialogContent>
              <div style={{ marginBottom: '16px' }}>
                <Text>
                  Är du säker på att du vill ta bort disken <strong>"{diskToDelete?.name}"</strong>?
                </Text>
              </div>
              
              <MessageBar intent="warning">
                <MessageBarBody>
                  <MessageBarTitle>Varning!</MessageBarTitle>
                  Detta kommer permanent radera:
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    <li>Alla {(diskToDelete?.actual_file_count || 0).toLocaleString()} filer i databasen</li>
                    <li>All katalogstruktur</li>
                    <li>All metadata för denna disk</li>
                  </ul>
                  Denna åtgärd kan inte ångras!
                </MessageBarBody>
              </MessageBar>
            </DialogContent>
            <DialogActions>
              <DialogTrigger disableButtonEnhancement>
                <Button 
                  appearance="secondary"
                  onClick={handleDeleteCancel}
                  disabled={isDeleting}
                >
                  Avbryt
                </Button>
              </DialogTrigger>
              <Button
                appearance="primary"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
                icon={isDeleting ? <Spinner size="tiny" /> : <Delete24Regular />}
                style={{ 
                  backgroundColor: tokens.colorPaletteRedBackground3,
                  borderColor: tokens.colorPaletteRedBorder2
                }}
              >
                {isDeleting ? 'Raderar...' : 'Ta bort disk'}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  );
};

export default DiskManagement;