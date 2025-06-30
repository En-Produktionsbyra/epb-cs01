import axios from 'axios';

// API Base URL
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Axios instance
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('🚨 API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('🚨 API Response Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// API Functions

/**
 * Hämta alla hårddiskar
 */
export const fetchDisks = async () => {
  try {
    const response = await api.get('/disks');
    return response.data;
  } catch (error) {
    throw new Error(`Kunde inte hämta diskar: ${error.message}`);
  }
};

/**
 * Hämta information om en specifik hårddisk
 */
export const fetchDisk = async (diskId) => {
  try {
    const response = await api.get(`/disks/${diskId}`);
    return response.data;
  } catch (error) {
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
    
    const response = await api.get(`/disks/${diskId}/files`, { params });
    return response.data;
  } catch (error) {
    throw new Error(`Kunde inte hämta filer från ${diskId}: ${error.message}`);
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
    
    const response = await api.get('/search', { params });
    return response.data;
  } catch (error) {
    throw new Error(`Sökning misslyckades: ${error.message}`);
  }
};

/**
 * Hämta systemstatistik
 */
export const fetchStats = async () => {
  try {
    const response = await api.get('/stats');
    return response.data;
  } catch (error) {
    console.warn('Kunde inte hämta statistik:', error.message);
    return null;
  }
};

/**
 * Ladda upp hårddisk-paket
 */
export const uploadDiskPackage = async (file, onUploadProgress = null) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onUploadProgress,
    });
    
    return response.data;
  } catch (error) {
    throw new Error(`Upload misslyckades: ${error.message}`);
  }
};

export default api;