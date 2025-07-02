import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Text,
  Button,
  Card,
  Spinner,
  makeStyles,
  tokens,
  shorthands,
  typographyStyles,
} from '@fluentui/react-components';
import {
  Storage20Regular,
  Document20Regular,
  ChartMultiple20Regular,
  Database20Regular,
  HardDrive20Regular,
  FolderOpen20Regular,
  ArrowClockwise20Regular,
  ChevronRight20Regular,
} from '@fluentui/react-icons';
import { fetchDisks as getDisks } from '../../utils/api';

const useStyles = makeStyles({
  header: {
    marginBottom: '24px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '32px',
  },
  statCard: {
    textAlign: 'center',
    ...shorthands.padding('20px'),
  },
  statValue: {
    fontSize: '28px',
    fontWeight: '600',
    color: tokens.colorBrandForeground1,
    marginBottom: '8px',
  },
  statIcon: {
    fontSize: '24px',
    marginBottom: '8px',
    color: tokens.colorBrandForeground1,
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '16px',
  },
  disksGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
    gap: '16px',
  },
  diskCard: {
    cursor: 'pointer',
    transition: 'transform 0.2s ease',
    '&:hover': {
      transform: 'translateY(-2px)',
    },
  },
  diskHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '12px',
  },
  diskStats: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '12px',
  },
  diskStat: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  diskActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    marginTop: '16px',
  },
  title: typographyStyles.title2,
  titleLarge: typographyStyles.display,
});

const Dashboard = () => {
  const styles = useStyles();
  const navigate = useNavigate();
  const [disks, setDisks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDisks();
  }, []);

  const fetchDisks = async () => {
    setLoading(true);
    try {
      console.log('📊 Dashboard: Fetching disks...');
      const data = await getDisks(); // Använd din smarta API-funktion
      console.log('📊 Dashboard: Received data:', data);
      setDisks(data || []);
      setError('');
    } catch (err) {
      console.error('📊 Dashboard: Error fetching disks:', err);
      setError(err.message);
      setDisks([]); // Sätt alltid till tom array vid fel
    }
    setLoading(false);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Okänt';
    try {
      return new Date(dateString).toLocaleDateString('sv-SE');
    } catch (e) {
      return 'Okänt';
    }
  };

  // FIXAT: Använd disk.name istället för disk.disk_id
  const handleDiskClick = (diskName) => {
    console.log('📊 Dashboard: Navigating to disk:', diskName);
    navigate(`/disks/${encodeURIComponent(diskName)}`);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '60px' }}>
        <Spinner label="Laddar dashboard..." size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <Database20Regular style={{ fontSize: '48px', color: tokens.colorPaletteRedForeground1, marginBottom: '16px' }} />
        <Text size={500} weight="semibold" block style={{ marginBottom: '8px' }}>
          Anslutningsfel
        </Text>
        <Text block style={{ marginBottom: '16px' }}>Fel: {error}</Text>
        <Button 
          appearance="primary" 
          icon={<ArrowClockwise20Regular />}
          onClick={fetchDisks}
        >
          Försök igen
        </Button>
      </div>
    );
  }

  // FIXAT: Använd nya PostgreSQL fältnamn
  const totalFiles = disks.reduce((sum, disk) => sum + (disk.actual_file_count || 0), 0);
  const totalSize = disks.reduce((sum, disk) => sum + (disk.actual_total_size || 0), 0);

  return (
    <div>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <Text className={styles.titleLarge}>Dashboard</Text>
        </div>
      </div>

      {/* Stats */}
      <div className={styles.statsGrid}>
        <Card className={styles.statCard}>
          <HardDrive20Regular className={styles.statIcon} />
          <div className={styles.statValue}>{disks.length}</div>
          <Text weight="semibold">Hårddiskar</Text>
        </Card>
        
        <Card className={styles.statCard}>
          <Document20Regular className={styles.statIcon} />
          <div className={styles.statValue}>{totalFiles.toLocaleString()}</div>
          <Text weight="semibold">Filer totalt</Text>
        </Card>
        
        <Card className={styles.statCard}>
          <Database20Regular className={styles.statIcon} />
          <div className={styles.statValue}>{formatFileSize(totalSize)}</div>
          <Text weight="semibold">Total storlek</Text>
        </Card>
      </div>

      {/* Disks Section */}
      <div className={styles.sectionHeader}>
        <Storage20Regular style={{ fontSize: '40px' }} />
        <Text size={600} weight="semibold">Hårddiskar</Text>
      </div>

      {disks.length === 0 ? (
        <Card style={{ padding: '32px', textAlign: 'center' }}>
          <FolderOpen20Regular style={{ fontSize: '48px', color: tokens.colorNeutralForeground3, marginBottom: '16px' }} />
          <Text size={500} weight="semibold" block style={{ marginBottom: '8px' }}>
            Inga hårddiskar hittades
          </Text>
          <Text>Ladda upp indexeringsfiler för att börja</Text>
        </Card>
      ) : (
        <div className={styles.disksGrid}>
          {disks.map((disk) => (
            <Card 
              key={disk.id} 
              className={styles.diskCard}
              onClick={() => handleDiskClick(disk.name)}
            >
              <div style={{ padding: '16px' }}>
                <div className={styles.diskHeader}>
                  {/* FIXAT: Använd disk.name istället för disk.disk_name */}
                  <Text weight="semibold" size={500}>{disk.name}</Text>
                </div>
                
                <div className={styles.diskStats}>
                  <div className={styles.diskStat}>
                    <Document20Regular style={{ fontSize: '14px' }} />
                    {/* FIXAT: Använd actual_file_count istället för file_count */}
                    <Text size={200}>{(disk.actual_file_count || 0).toLocaleString()}</Text>
                  </div>
                  
                  <div className={styles.diskStat}>
                    <Database20Regular style={{ fontSize: '14px' }} />
                    {/* FIXAT: Använd actual_total_size istället för total_size */}
                    <Text size={200}>{formatFileSize(disk.actual_total_size)}</Text>
                  </div>
                  
                  <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
                    {/* FIXAT: Använd created_at istället för scan_date */}
                    {formatDate(disk.created_at)}
                  </Text>
                </div>

                <div className={styles.diskActions}>
                  <Button 
                    appearance="primary" 
                    size="small"
                    icon={<ChevronRight20Regular />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDiskClick(disk.name);
                    }}
                  >
                    Bläddra filer
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;