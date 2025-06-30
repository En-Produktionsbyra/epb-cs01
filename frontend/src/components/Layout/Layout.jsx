import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import {
  Home20Regular,
  FolderOpen20Regular,
  Storage20Regular,
  Navigation20Regular,
} from '@fluentui/react-icons';
import {
  AppItem,
  Hamburger,
  NavCategory,
  NavCategoryItem,
  NavDivider,
  NavDrawer,
  NavDrawerBody,
  NavDrawerHeader,
  NavItem,
  NavSectionHeader,
  NavSubItem,
  NavSubItemGroup,
} from "@fluentui/react-components";

import {
  shorthands,
  Button,
  Input,
  Toolbar,
  ToolbarButton,
  ToolbarDivider,
  Label,
  Radio,
  RadioGroup,
  Switch,
  Tooltip,
  makeStyles,
  tokens,
  useId,
  useRestoreFocusTarget,
} from "@fluentui/react-components";
import {
  Board20Filled,
  Board20Regular,
  BoxMultiple20Filled,
  BoxMultiple20Regular,
  DataArea20Filled,
  DataArea20Regular,
  DocumentBulletListMultiple20Filled,
  DocumentBulletListMultiple20Regular,
  HeartPulse20Filled,
  HeartPulse20Regular,
  MegaphoneLoud20Filled,
  MegaphoneLoud20Regular,
  NotePin20Filled,
  NotePin20Regular,
  People20Filled,
  People20Regular,
  PeopleStar20Filled,
  PeopleStar20Regular,
  Person20Filled,
  PersonLightbulb20Filled,
  PersonLightbulb20Regular,
  Person20Regular,
  PersonSearch20Filled,
  PersonSearch20Regular,
  PreviewLink20Filled,
  PreviewLink20Regular,
  bundleIcon,
  PersonCircle32Regular,
  ImageSearch20Regular,
  ImageSearch20Filled,
  Search20Regular,
  Search20Filled,
  ArrowUpload20Regular,
  ArrowUpload20Filled,
} from "@fluentui/react-icons";

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    overflow: "hidden",
    height: '100vh',
    width: '100vw',
    backgroundColor: tokens.colorNeutralBackground1,
  },
  header: {
    backgroundColor: tokens.colorNeutralBackground2,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    ...shorthands.padding('12px', '16px'),
  },
  toolbar: {
    justifyContent: 'space-between',
  },
  searchContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flex: 1,
    maxWidth: '400px',
    marginLeft: '16px',
  },
  searchInput: {
    flex: 1,
  },
  content: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
  },
  sidebar: {
    minWidth: '260px',
    backgroundColor: tokens.colorNeutralBackground3,
    borderRight: `1px solid ${tokens.colorNeutralStroke2}`,
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.padding('16px', '8px'),
  },
  main: {
    flex: 1,
    overflow: 'auto',
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding('24px'),
  },
  navButton: {
    justifyContent: 'flex-start',
    width: '100%',
    ...shorthands.margin('2px', '0'),
  },
  activeNavButton: {
    backgroundColor: tokens.colorBrandBackground2,
  },
  root: {
    overflow: "hidden",
    display: "flex",
    height: '100vh',
    width: '100vw',
  },
  nav: {
    minWidth: "260px",
  },
  field: {
    display: "flex",
    marginTop: "4px",
    marginLeft: "8px",
    flexDirection: "column",
    gridRowGap: tokens.spacingVerticalS,
  },
});
const Dashboard = bundleIcon(Board20Filled, Board20Regular);
const Upload = bundleIcon(ArrowUpload20Filled, ArrowUpload20Regular);
const Search = bundleIcon(Search20Filled, Search20Regular);
const Person = bundleIcon(Person20Filled, Person20Regular);
const ImageSearch = bundleIcon(ImageSearch20Filled, ImageSearch20Regular);

const EmployeeSpotlight = bundleIcon(
  PersonLightbulb20Filled,
  PersonLightbulb20Regular
);
const PerformanceReviews = bundleIcon(
  PreviewLink20Filled,
  PreviewLink20Regular
);
const JobPostings = bundleIcon(NotePin20Filled, NotePin20Regular);
const Interviews = bundleIcon(People20Filled, People20Regular);
const HealthPlans = bundleIcon(HeartPulse20Filled, HeartPulse20Regular);
const TrainingPrograms = bundleIcon(BoxMultiple20Filled, BoxMultiple20Regular);
const CareerDevelopment = bundleIcon(PeopleStar20Filled, PeopleStar20Regular);
const Analytics = bundleIcon(DataArea20Filled, DataArea20Regular);
const Reports = bundleIcon(
  DocumentBulletListMultiple20Filled,
  DocumentBulletListMultiple20Regular
);

const Layout = ({ children }) => {
  const styles = useStyles();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = React.useState('');

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const isActive = (path) => {
    return location.pathname === path;
  };


  const typeLableId = useId("type-label");
  const linkLabelId = useId("link-label");
  const multipleLabelId = useId("multiple-label");

  const [isOpen, setIsOpen] = React.useState(true);
  const [enabledLinks, setEnabledLinks] = React.useState(true);
  const [isMultiple, setIsMultiple] = React.useState(true);

  // Tabster prop used to restore focus to the navigation trigger for overlay nav drawers
  const restoreFocusTargetAttributes = useRestoreFocusTarget();

  const linkDestination = enabledLinks ? "https://www.bing.com" : "";

  return (
    
    <div className={styles.root}>
          
      <NavDrawer
        open={isOpen}
        type="inline"
        className={styles.nav}
      >
        <NavDrawerHeader>

          <AppItem
            icon={<PersonCircle32Regular />}
            onClick={() => navigate('/')} 
          >
            En Cold Storage
          </AppItem>
          {/* <div className={styles.searchContainer}>
            <Input
              className={styles.searchInput}
              placeholder="Sök efter filer, projekt, kunder..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyPress}
            />
            <Button
              appearance="primary"
              icon={<Search20Regular />}
              onClick={handleSearch}
            >
              Sök
            </Button>
          </div> */}
        </NavDrawerHeader>

        <NavDrawerBody>
          <NavItem onClick={() => navigate('/dashboard')} icon={<Dashboard />} value="1">
            Dashboard
          </NavItem>
          <NavItem onClick={() => navigate('/')} icon={<ImageSearch />} value="2">
            Sök filer
          </NavItem>
          <NavItem
            onClick={() => navigate('/upload')}
            icon={<Upload />}
            value="3"
          >
            Upload
          </NavItem>
          
          <NavSectionHeader>Admin</NavSectionHeader>
          <NavItem icon={<Interviews />} value="4">
            Kommer snart
          </NavItem>
          <NavItem icon={<Interviews />} value="5">
            Kommer snart
          </NavItem>
          
          <NavDivider />

          <NavItem icon={<Analytics />} value="6">
            Ladda ner Scriptet
          </NavItem>
        </NavDrawerBody>
      </NavDrawer>
      <div className={styles.content}>
        <main className={styles.main}>
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;