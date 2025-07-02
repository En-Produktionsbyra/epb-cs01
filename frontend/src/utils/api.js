import axios from 'axios';

// FIXAD VERSION - garanterat rätt API URL
const getApiBaseUrl = () => {
  const currentHost = window.location.hostname;
  const protocol = window.location.protocol;
  
  console.log('🌐 Current location:', {
    hostname: currentHost,
    protocol: protocol,
    full: window.location.href
  });
  
  let apiUrl;
  
  if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
    // Development - direkt till port 8000
    apiUrl = 'http://localhost:8000';
  } else {
    // Production - använd /api/ path
    apiUrl = `${protocol}//${currentHost}/api`;
  }
  
  console.log('🔗 Calculated API URL:', apiUrl);
  return apiUrl;
};

// API Base URL
const API_BASE = getApiBaseUrl();

console.log('=== API Configuration ===');
console.log('Frontend URL:', window.location.origin);
console.log('API Base URL:', API_BASE);
console.log('========================');

// Axios instance
const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor med detaljerad logging
api.interceptors.request.use(
  (config) => {
    const fullUrl = `${config.baseURL}${config.url}`;
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${fullUrl}`);
    return config;
  },
  (error) => {
    console.error('🚨 API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor med bättre felhantering
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    console.log('📄 Response data:', response.data);
    return response;
  },
  (error) => {
    console.error('🚨 API Response Error Details:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      fullUrl: `${error.config?.baseURL}${error.config?.url}`
    });
    
    // Specifika felmeddelanden
    if (error.code === 'ERR_NETWORK') {
      console.error('❌ NÄTVERKSFEL - Kan inte ansluta till:', API_BASE);
      console.error('💡 Kontrollera att backend körs på denna URL');
    } else if (error.response?.status === 0) {
      console.error('❌ CORS-FEL eller server ej tillgänglig');
      console.error('💡 Kontrollera CORS-inställningar i backend');
    }
    
    return Promise.reject(error);
  }
);

// Test connection function med detaljerad feedback
export const testConnection = async () => {
  try {
    console.log('🔍 Testing connection to:', API_BASE);
    
    const response = await api.get('/health');
    console.log('✅ Backend connection OK:', response.data);
    
    // Test även disks endpoint
    try {
      const disksResponse = await api.get('/disks');
      console.log('✅ Disks endpoint OK:', disksResponse.data.length, 'disks found');
    } catch (disksError) {
      console.warn('⚠️ Disks endpoint failed:', disksError.message);
    }
    
    return true;
  } catch (error) {
    console.error('❌ Backend connection failed:', error.message);
    console.error('🔧 Tried to connect to:', API_BASE);
    console.error('💡 Possible solutions:');
    console.error('   1. Check that backend is running');
    console.error('   2. Check CORS settings');
    console.error('   3. Check network connectivity');
    return false;
  }
};

/**
 * Hämta alla hårddiskar
 */
export const fetchDisks = async () => {
  try {
    console.log('📁 Fetching disks...');
    const response = await api.get('/disks');
    console.log('✅ Disks fetched successfully:', response.data.length, 'disks');
    return response.data;
  } catch (error) {
    console.error('❌ Failed to fetch disks:', error.message);
    throw new Error(`Kunde inte hämta diskar: ${error.message}`);
  }
};

/**
 * Hämta information om en specifik hårddisk
 */
export const fetchDisk = async (diskId) => {
  try {
    console.log('💿 Fetching disk:', diskId);
    const response = await api.get(`/disks/${diskId}`);
    console.log('✅ Disk info fetched:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Failed to fetch disk:', diskId, error.message);
    throw new Error(`Kunde inte hämta disk ${diskId}: ${error.message}`);
  }
};

/**
 * Hämta filer från en hårddisk
 */
export const fetchDiskFiles = async (diskId, { page = 1, per_page = 100, path = null } = {}) => {
  try {
    const params = { page, per_page };
    if (path) params.path = path;
    
    console.log('📄 Fetching files for disk:', diskId, 'params:', params);
    const response = await api.get(`/disks/${diskId}/files`, { params });
    console.log('✅ Files fetched:', response.data.files?.length, 'files');
    return response.data;
  } catch (error) {
    console.error('❌ Failed to fetch files:', diskId, error.message);
    throw new Error(`Kunde inte hämta filer från ${diskId}: ${error.message}`);
  }
};

/**
 * Browse directory (ny snabb metod)
 */
export const browseDirectory = async (diskId, path = null) => {
  try {
    const params = path ? { path } : {};
    
    console.log('🗂️ Browsing directory:', diskId, 'path:', path || 'ROOT');
    const response = await api.get(`/disks/${diskId}/browse`, { params });
    console.log('✅ Directory browsed:', response.data.items?.length, 'items');
    return response.data;
  } catch (error) {
    console.error('❌ Failed to browse directory:', diskId, path, error.message);
    throw new Error(`Kunde inte bläddra i mapp: ${error.message}`);
  }
};

/**
 * Sök efter filer
 */
export const searchFiles = async ({
  q,
  page = 1,
  per_page = 50,
  client = null,
  project = null,
  file_type = null,
  disk_id = null
} = {}) => {
  try {
    const params = { q, page, per_page };
    if (client) params.client = client;
    if (project) params.project = project;
    if (file_type) params.file_type = file_type;
    if (disk_id) params.disk_id = disk_id;
    
    console.log('🔍 Searching files:', params);
    const response = await api.get('/search', { params });
    console.log('✅ Search completed:', response.data.files?.length, 'results');
    return response.data;
  } catch (error) {
    console.error('❌ Search failed:', error.message);
    throw new Error(`Sökning misslyckades: ${error.message}`);
  }
};

/**
 * Hämta systemstatistik
 */
export const fetchStats = async () => {
  try {
    console.log('📊 Fetching stats...');
    const response = await api.get('/stats');
    console.log('✅ Stats fetched:', response.data);
    return response.data;
  } catch (error) {
    console.warn('⚠️ Could not fetch stats:', error.message);
    return null;
  }
};

/**
 * Kontrollera om en disk redan finns (duplicate check)
 */
export const checkDuplicate = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('🔍 Checking for duplicate:', file.name);
    const response = await api.post('/upload/check-duplicate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    console.log('✅ Duplicate check result:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Duplicate check failed:', error.message);
    throw new Error(`Duplicate check misslyckades: ${error.message}`);
  }
};

/**
 * Ladda upp hårddisk-paket - GAMLA SYNKRONA METODEN
 */
export const Red = async (file, onUploadProgress = null) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('📤 Uploading file (sync):', file.name);
    const response = await api.post('/upload/json-index', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onUploadProgress,
    });
    
    console.log('✅ Upload successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Upload failed:', error.message);
    throw new Error(`Upload misslyckades: ${error.message}`);
  }
};

/**
 * Ladda upp hårddisk-paket - NY ASYNKRONA METODEN MED PROGRESS OCH REPLACE
 */
export const uploadDiskPackageAsync = async (file, replaceExisting = false) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    // VIKTIGT: Lägg till replace_existing som form parameter
    if (replaceExisting) {
      formData.append('replace_existing', 'true');
    }
    
    console.log('📤 Uploading file (async):', file.name, 'Replace existing:', replaceExisting);
    const response = await api.post('/upload/json-index-async', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    console.log('✅ Upload started:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Upload failed:', error.message);
    throw new Error(`Upload misslyckades: ${error.message}`);
  }
};

/**
 * Anslut till progress stream via Server-Sent Events
 */
export const connectToProgressStream = (taskId, onProgress, onComplete, onError) => {
  const eventSource = new EventSource(`${API_BASE}/upload/progress/${taskId}`);
  
  console.log('📡 Connecting to progress stream:', taskId);
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      console.log('📈 Progress update:', data);
      
      // Hantera olika meddelanden
      if (data.status === 'connected') {
        console.log('✅ EventSource connected');
        return;
      }
      
      if (data.status === 'heartbeat' || data.status === 'waiting') {
        console.log('💓 Heartbeat:', data.message);
        return;
      }
      
      if (data.status === 'finished' || data.status === 'timeout') {
        console.log('🏁 Progress stream finished:', data.status);
        eventSource.close();
        return;
      }
      
      // Anropa progress callback för riktiga progress updates
      if (data.step && onProgress) {
        onProgress(data);
      }
      
      // Hantera slutresultat
      if (data.step === 'complete' && data.result) {
        console.log('✅ Import complete:', data.result);
        if (onComplete) {
          onComplete(data.result);
        }
        eventSource.close();
      } else if (data.step === 'error') {
        console.error('❌ Import error:', data.message);
        if (onError) {
          onError(new Error(data.message));
        }
        eventSource.close();
      }
      
    } catch (err) {
      console.error('❌ Error parsing progress data:', err);
      if (onError) {
        onError(err);
      }
    }
  };
  
  eventSource.onerror = (error) => {
    console.error('❌ EventSource error:', error);
    eventSource.close();
    if (onError) {
      onError(new Error('Anslutningsfel under import'));
    }
  };
  
  eventSource.onopen = () => {
    console.log('🔌 EventSource connection opened');
  };
  
  // Returnera eventSource så att den kan stängas manuellt
  return eventSource;
};

/**
 * Hämta upload status för en task
 */
export const getUploadStatus = async (taskId) => {
  try {
    console.log('📊 Getting upload status:', taskId);
    const response = await api.get(`/upload/status/${taskId}`);
    console.log('✅ Status fetched:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Failed to get status:', taskId, error.message);
    throw new Error(`Kunde inte hämta status: ${error.message}`);
  }
};

// Testa anslutning när modulen laddas
testConnection();

export default api;