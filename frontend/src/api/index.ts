import axios from 'axios';

const API_BASE_URL = typeof import.meta !== 'undefined' && import.meta.env.VITE_API_URL 
  ? import.meta.env.VITE_API_URL 
  : '/api/v1';

// Создаём axios инстанс
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем токен к запросам
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Обработка ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// Auth API
// ============================================================================

export interface RegisterData {
  email: string;
  password: string;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export const authAPI = {
  register: (data: RegisterData) =>
    api.post<AuthResponse>('/auth/register', data),

  login: (data: LoginData) =>
    api.post<AuthResponse>('/auth/token', 
      new URLSearchParams({ username: data.username, password: data.password }),
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      }
    ),
};

// ============================================================================
// Files API
// ============================================================================

export interface UploadResponse {
  file_id: string;
  filename: string;
  size_bytes: number;
  duplicate: boolean;
}

export interface DownloadResponse {
  download_url: string;
  filename: string;
  expires_in: number;
}

export const filesAPI = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<UploadResponse>('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  download: (fileId: string) =>
    api.get<DownloadResponse>(`/files/download/${fileId}`),
};

// ============================================================================
// Conversions API
// ============================================================================

export type ConversionStatus = 'pending' | 'processing' | 'done' | 'failed';

export interface ConversionCreate {
  file_id: string;
  target_format: string;
}

export interface ConversionResponse {
  job_id: string;
  status: ConversionStatus;
  target_format: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: ConversionStatus;
  target_format: string;
  result_file_id: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export const conversionsAPI = {
  create: (data: ConversionCreate) =>
    api.post<ConversionResponse>('/conversions/', data),

  getStatus: (jobId: string) =>
    api.get<JobStatusResponse>(`/conversions/${jobId}`),
};

// ============================================================================
// Types
// ============================================================================

export type SupportedFormat =
  | 'docx'
  | 'xlsx'
  | 'pptx'
  | 'rtf'
  | 'html'
  | 'png'
  | 'jpeg'
  | 'txt';

export const FORMAT_LABELS: Record<SupportedFormat, string> = {
  docx: 'Word Document',
  xlsx: 'Excel Spreadsheet',
  pptx: 'PowerPoint Presentation',
  rtf: 'Rich Text Format',
  html: 'HTML Document',
  png: 'PNG Image',
  jpeg: 'JPEG Image',
  txt: 'Plain Text',
};

export const FORMAT_ICONS: Record<SupportedFormat, string> = {
  docx: '📄',
  xlsx: '📊',
  pptx: '📈',
  rtf: '📝',
  html: '🌐',
  png: '🖼️',
  jpeg: '🖼️',
  txt: '📋',
};
