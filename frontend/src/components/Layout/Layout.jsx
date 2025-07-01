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
  useId,
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
  Navigation20Regular,
  Settings20Regular,
  Home20Regular,
} from "@fluentui/react-icons";

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    width: '100vw',
    backgroundColor: tokens.colorNeutralBackground1,
  },
  
  // Mobile Header (bara synlig på mobil)
  mobileHeader: {
    display: 'none',
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    ...shorthands.padding('12px', '16px'),
    alignItems: 'center',
    gap: '12px',
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    '@media (max-width: 768px)': {
      display: 'flex',
    },
  },
  
  mobileTitle: {
    flex: 1,
    fontWeight: tokens.fontWeightSemibold,
    fontSize: tokens.fontSizeBase300,
    color: tokens.colorNeutralForegroundOnBrand,
  },
  
  hamburgerButton: {
    backgroundColor: 'transparent',
    border: 'none',
    color: tokens.colorNeutralForegroundOnBrand,
    '&:hover': {
      backgroundColor: tokens.colorBrandBackgroundHover,
    },
  },
  
  // Main content area
  content: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
  },
  
  // Navigation styles
  navDrawer: {
    position: 'relative',
    zIndex: 1000,
    // Desktop: alltid synlig
    '@media (min-width: 769px)': {
      position: 'relative',
    },
    // Mobile: overlay
    '@media (max-width: 768px)': {
      position: 'fixed',
      top: '56px', // Under mobile header
      left: 0,
      height: 'calc(100vh - 56px)',
      boxShadow: tokens.shadow16,
    },
  },
  
  navDrawerClosed: {
    '@media (max-width: 768px)': {
      transform: 'translateX(-100%)',
      transition: 'transform 0.3s ease',
    },
  },
  
  navDrawerOpen: {
    '@media (max-width: 768px)': {
      transform: 'translateX(0)',
      transition: 'transform 0.3s ease',
    },
  },
  
  // Main content
  main: {
    flex: 1,
    overflow: 'auto',
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding('24px'),
    // På mobil: fyll hela bredden
    '@media (max-width: 768px)': {
      width: '100%',
      ...shorthands.padding('16px'),
    },
  },
  
  // Overlay för mobil när meny är öppen
  overlay: {
    display: 'none',
    '@media (max-width: 768px)': {
      display: 'block',
      position: 'fixed',
      top: '56px',
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      zIndex: 999,
    },
  },
  
  // Navigation items
  navItem: {
    minHeight: '44px', // Touch-friendly
    ...shorthands.margin('2px', '0'),
  },
  
  activeNavItem: {
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
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
  
  // Mobile navigation state
  const [isMobile, setIsMobile] = useState(false);
  const [isNavOpen, setIsNavOpen] = useState(false);
  
  // Detect mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      if (!mobile) {
        setIsNavOpen(true); // Desktop: alltid öppen
      } else {
        setIsNavOpen(false); // Mobile: börja stängd
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  // Stäng meny när route ändras (på mobil)
  useEffect(() => {
    if (isMobile) {
      setIsNavOpen(false);
    }
  }, [location.pathname, isMobile]);
  
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
  
  const toggleNav = () => {
    setIsNavOpen(!isNavOpen);
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
    <div className={styles.container}>
      {/* Mobile Header */}
      <div className={styles.mobileHeader}>
        <div 
          className={styles.hamburgerButton}
          onClick={toggleNav}
          role="button"
          tabIndex={0}
          aria-label="Öppna navigation"
          onKeyDown={(e) => e.key === 'Enter' && toggleNav()}
        >
          <Hamburger />
        </div>
        <Text className={styles.mobileTitle}>
          {getPageTitle()}
        </Text>
      </div>
      
      {/* Overlay för mobil */}
      {isMobile && isNavOpen && (
        <div className={styles.overlay} onClick={() => setIsNavOpen(false)} />
      )}
      
      <div className={styles.content}>
        {/* Navigation Drawer */}
        <NavDrawer
          open={isNavOpen}
          type={isMobile ? "overlay" : "inline"}
          className={`${styles.navDrawer} ${
            isNavOpen ? styles.navDrawerOpen : styles.navDrawerClosed
          }`}
          style={{
            width: isNavOpen ? '280px' : '0px',
            minWidth: isNavOpen ? '280px' : '0px',
          }}
        >
          <NavDrawerHeader>
            <AppItem
              icon={<PersonCircle32Regular />}
              as="div"
            >
              <Text weight="semibold">Cold Storage</Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
                Filhanterare
              </Text>
            </AppItem>
          </NavDrawerHeader>

          <NavDrawerBody>
            {/* Search i navigation */}
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
            
            {/* Main Navigation - Använd as="div" för att undvika nested buttons */}
            <NavItem 
              as="div"
              className={`${styles.navItem} ${isActive('/dashboard') ? styles.activeNavItem : ''}`}
              onClick={() => handleNavItemClick('/dashboard')}
              icon={<Dashboard />}
              value="dashboard"
            >
              Dashboard
            </NavItem>
            
            <NavItem 
              as="div"
              className={`${styles.navItem} ${isActive('/search') || isActive('/') ? styles.activeNavItem : ''}`}
              onClick={() => handleNavItemClick('/')}
              icon={<SearchIcon />}
              value="search"
            >
              Sök filer
            </NavItem>
            
            <NavItem
              as="div"
              className={`${styles.navItem} ${isActive('/upload') ? styles.activeNavItem : ''}`}
              onClick={() => handleNavItemClick('/upload')}
              icon={<Upload />}
              value="upload"
            >
              Ladda upp
            </NavItem>
            
            <NavDivider />
            
            <NavSectionHeader>Verktyg</NavSectionHeader>
            
            <NavItem 
              as="div"
              className={styles.navItem}
              icon={<Storage20Regular />} 
              value="disks"
              onClick={() => handleNavItemClick('/dashboard')}
            >
              Hårddiskar
            </NavItem>
            
            <NavItem 
              as="div"
              className={styles.navItem}
              icon={<Settings20Regular />} 
              value="settings"
            >
              Inställningar
            </NavItem>
          </NavDrawerBody>
        </NavDrawer>
        
        {/* Main Content */}
        <main className={styles.main}>
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;