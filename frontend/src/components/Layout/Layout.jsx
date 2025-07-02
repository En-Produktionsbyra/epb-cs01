import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Tab,
  TabList,
  Card,
  CardHeader,
  Text,
  tokens
} from '@fluentui/react-components';
import {
  Search24Regular,
  CloudArrowUp24Regular,
  FolderOpen24Regular,
  Home24Regular,
  Settings24Regular
} from '@fluentui/react-icons';

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const getActiveTab = () => {
    const path = location.pathname;
    if (path === '/') return 'search';
    if (path.startsWith('/dashboard')) return 'dashboard';
    if (path.startsWith('/disks')) return 'browse';
    if (path.startsWith('/search')) return 'search';
    if (path.startsWith('/upload')) return 'upload';
    if (path.startsWith('/manage') || path.startsWith('/admin')) return 'manage';
    return 'search';
  };

  const handleTabChange = (event, data) => {
    switch (data.value) {
      case 'search':
        navigate('/');
        break;
      case 'dashboard':
        navigate('/dashboard');
        break;
      case 'browse':
        navigate('/dashboard'); // För nu, kan ändras senare
        break;
      case 'upload':
        navigate('/upload');
        break;
      case 'manage':
        navigate('/manage');
        break;
      default:
        navigate('/');
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: tokens.colorNeutralBackground2
    }}>
      {/* Header */}
      <Card style={{ 
        borderRadius: 0,
        borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
        marginBottom: 0
      }}>
        <CardHeader
          header={
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center',
              width: '100%'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <FolderOpen24Regular style={{ fontSize: '24px', color: tokens.colorBrandForeground1 }} />
                <Text size={600} weight="semibold">Cold Storage</Text>
              </div>
              
              {/* Navigation Tabs */}
              <TabList
                selectedValue={getActiveTab()}
                onTabSelect={handleTabChange}
                size="medium"
              >
                <Tab value="search" icon={<Search24Regular />}>
                  Sök
                </Tab>
                <Tab value="dashboard" icon={<Home24Regular />}>
                  Dashboard
                </Tab>
                <Tab value="upload" icon={<CloudArrowUp24Regular />}>
                  Ladda upp
                </Tab>
                <Tab value="manage" icon={<Settings24Regular />}>
                  Hantera
                </Tab>
              </TabList>
            </div>
          }
        />
      </Card>

      {/* Main Content */}
      <main style={{ 
        padding: 0,
        minHeight: 'calc(100vh - 80px)'
      }}>
        {children}
      </main>
    </div>
  );
};

export default Layout;