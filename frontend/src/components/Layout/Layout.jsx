import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Tab,
  TabList,
  Card,
  CardHeader,
  Text,
  Button,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  tokens,
  makeStyles,
  shorthands
} from '@fluentui/react-components';
import {
  Search24Regular,
  CloudArrowUp24Regular,
  FolderOpen24Regular,
  Home24Regular,
  Settings24Regular,
  Navigation24Regular
} from '@fluentui/react-icons';

// Minimal CSS tillägg för mobil
const useStyles = makeStyles({
  // Dölj tabs på mycket små skärmar
  tabNavigation: {
    '@media (max-width: 480px)': {
      display: 'none',
    },
  },
  
  // Visa mobilmeny bara på små skärmar
  mobileMenu: {
    display: 'none',
    '@media (max-width: 480px)': {
      display: 'block',
    },
  },
  
  // Touch-friendly meny items
  menuItem: {
    minHeight: '44px',
    ...shorthands.padding('12px', '16px'),
  },
});

const Layout = ({ children }) => {
  const styles = useStyles();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobile, setIsMobile] = useState(false);

  // Detektera mobil
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 480);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

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

  const handleMobileNavigation = (route) => {
    navigate(route);
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: tokens.colorNeutralBackground2
    }}>
      {/* Header - exakt samma som din ursprungliga */}
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
              
              {/* Desktop Navigation Tabs */}
              <div className={styles.tabNavigation}>
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

              {/* Mobile Menu - bara synlig på små skärmar */}
              <div className={styles.mobileMenu}>
                <Menu>
                  <MenuTrigger>
                    <Button
                      appearance="subtle"
                      icon={<Navigation24Regular />}
                      style={{ minHeight: '44px', minWidth: '44px' }}
                    >
                      Meny
                    </Button>
                  </MenuTrigger>
                  
                  <MenuPopover>
                    <MenuList>
                      <MenuItem 
                        className={styles.menuItem}
                        icon={<Search24Regular />}
                        onClick={() => handleMobileNavigation('/')}
                      >
                        Sök
                      </MenuItem>
                      <MenuItem 
                        className={styles.menuItem}
                        icon={<Home24Regular />}
                        onClick={() => handleMobileNavigation('/dashboard')}
                      >
                        Dashboard
                      </MenuItem>
                      <MenuItem 
                        className={styles.menuItem}
                        icon={<CloudArrowUp24Regular />}
                        onClick={() => handleMobileNavigation('/upload')}
                      >
                        Ladda upp
                      </MenuItem>
                      <MenuItem 
                        className={styles.menuItem}
                        icon={<Settings24Regular />}
                        onClick={() => handleMobileNavigation('/manage')}
                      >
                        Hantera
                      </MenuItem>
                    </MenuList>
                  </MenuPopover>
                </Menu>
              </div>
            </div>
          }
        />
      </Card>

      {/* Main Content - exakt samma som din ursprungliga */}
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