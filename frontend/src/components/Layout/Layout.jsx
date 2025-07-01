import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppItem,
  Hamburger,
  NavDrawer,
  NavDrawerBody,
  NavDrawerHeader,
  NavItem,
  NavSectionHeader,
  NavDivider,
  Button,
  Input,
  Text,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import {
  Board20Filled,
  Board20Regular,
  Search20Filled,
  Search20Regular,
  ArrowUpload20Filled,
  ArrowUpload20Regular,
  PersonCircle32Regular,
  bundleIcon,
  Storage20Regular,
  Settings20Regular,
} from "@fluentui/react-icons";

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    width: '100vw',
  },
  
  // Mobile header - endast synlig på små skärmar
  mobileHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    ...shorthands.padding('12px', '16px'),
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    borderBottom: `1px solid ${tokens.colorBrandStroke1}`,
    // Dölj på desktop
    '@media (min-width: 768px)': {
      display: 'none',
    },
  },
  
  hamburgerButton: {
    backgroundColor: 'transparent',
    border: 'none',
    color: tokens.colorNeutralForegroundOnBrand,
    cursor: 'pointer',
    ...shorthands.padding('8px'),
    borderRadius: tokens.borderRadiusSmall,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    '&:hover': {
      backgroundColor: tokens.colorBrandBackgroundHover,
    },
  },
  
  mobileTitle: {
    fontWeight: tokens.fontWeightSemibold,
    fontSize: tokens.fontSizeBase300,
  },
  
  // Main content wrapper
  contentWrapper: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  
  // Navigation drawer
  navDrawer: {
    // På desktop: fast bredd sidebar
    '@media (min-width: 768px)': {
      position: 'relative',
      width: '280px',
      minWidth: '280px',
    },
  },
  
  // Main content area
  mainContent: {
    flex: 1,
    overflow: 'auto',
    ...shorthands.padding('24px'),
    // På mobil: mindre padding
    '@media (max-width: 767px)': {
      ...shorthands.padding('16px'),
    },
  },
  
  // Search container i navigation
  searchContainer: {
    ...shorthands.padding('8px'),
    ...shorthands.margin('8px', '0'),
  },
  
  searchInput: {
    width: '100%',
    marginBottom: '8px',
  },
  
  // Navigation items
  navItem: {
    minHeight: '44px',
    ...shorthands.margin('2px', '0'),
  },
});

// Bundle icons
const Dashboard = bundleIcon(Board20Filled, Board20Regular);
const SearchIcon = bundleIcon(Search20Filled, Search20Regular);
const Upload = bundleIcon(ArrowUpload20Filled, ArrowUpload20Regular);

const Layout = ({ children }) => {
  const styles = useStyles();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const [isNavOpen, setIsNavOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  
  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      
      // På desktop: alltid öppen, på mobil: stängd som default
      if (!mobile) {
        setIsNavOpen(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  // Stäng nav när man navigerar på mobil
  useEffect(() => {
    if (isMobile) {
      setIsNavOpen(false);
    }
  }, [location.pathname]);
  
  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
      if (isMobile) setIsNavOpen(false);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };
  
  const isActive = (path) => {
    if (path === '/search' && location.pathname === '/') return true;
    return location.pathname === path;
  };
  
  const handleNavItemClick = (path) => {
    navigate(path);
    if (isMobile) setIsNavOpen(false);
  };
  
  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Sök filer';
      case '/search': return 'Sök filer';
      case '/dashboard': return 'Dashboard';
      case '/upload': return 'Upload';
      default:
        if (location.pathname.startsWith('/disks/')) return 'Filhanterare';
        return 'Cold Storage';
    }
  };

  return (
    <div className={styles.root}>
      {/* Mobile Header - endast synlig på mobil */}
      <div className={styles.mobileHeader}>
        <button 
          className={styles.hamburgerButton}
          onClick={() => setIsNavOpen(!isNavOpen)}
          aria-label="Växla navigation"
        >
          <Hamburger />
        </button>
        <Text className={styles.mobileTitle}>
          {getPageTitle()}
        </Text>
      </div>
      
      {/* Main Content Wrapper */}
      <div className={styles.contentWrapper}>
        {/* Navigation Drawer */}
        <NavDrawer
          open={isNavOpen}
          type={isMobile ? "overlay" : "inline"}
          onOpenChange={(event, data) => setIsNavOpen(data.open)}
          className={styles.navDrawer}
        >
          <NavDrawerHeader>
            <AppItem icon={<PersonCircle32Regular />}>
              <div>
                <Text weight="semibold">Cold Storage</Text>
                <br />
                <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
                  Filhanterare
                </Text>
              </div>
            </AppItem>
          </NavDrawerHeader>

          <NavDrawerBody>
            {/* Search */}
            <div className={styles.searchContainer}>
              <Input
                className={styles.searchInput}
                placeholder="Sök filer..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleKeyPress}
                contentBefore={<SearchIcon />}
                size="small"
              />
              <Button
                appearance="primary"
                onClick={handleSearch}
                disabled={!searchQuery.trim()}
                size="small"
                style={{ width: '100%' }}
              >
                Sök
              </Button>
            </div>
            
            <NavDivider />
            
            {/* Main Navigation */}
            <NavItem 
              className={styles.navItem}
              onClick={() => handleNavItemClick('/dashboard')}
              icon={<Dashboard />}
              value="dashboard"
            >
              Dashboard
            </NavItem>
            
            <NavItem 
              className={styles.navItem}
              onClick={() => handleNavItemClick('/')}
              icon={<SearchIcon />}
              value="search"
            >
              Sök filer
            </NavItem>
            
            <NavItem
              className={styles.navItem}
              onClick={() => handleNavItemClick('/upload')}
              icon={<Upload />}
              value="upload"
            >
              Ladda upp
            </NavItem>
            
            <NavDivider />
            
            <NavSectionHeader>Verktyg</NavSectionHeader>
            
            <NavItem 
              className={styles.navItem}
              icon={<Storage20Regular />} 
              onClick={() => handleNavItemClick('/dashboard')}
              value="disks"
            >
              Hårddiskar
            </NavItem>
            
            <NavItem 
              className={styles.navItem}
              icon={<Settings20Regular />} 
              value="settings"
            >
              Inställningar
            </NavItem>
          </NavDrawerBody>
        </NavDrawer>
        
        {/* Main Content */}
        <main className={styles.mainContent}>
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;