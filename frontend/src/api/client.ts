import axios from 'axios'
import type { AxiosInstance } from 'axios'

const API_BASE = import.meta.env.PROD ? '/api' : '/api'

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
client.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// Response interceptor
client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default client

// API endpoints
export const api = {
  // File browsing
  browseFiles: (path: string = '') =>
    client.get('/files/browse', { params: { path } }),

  validatePath: (path: string) =>
    client.get('/files/validate-path', { params: { path } }),

  // Transcode operations
  startTranscode: (data: {
    input_path: string
    output_path?: string
    output_dir?: string
    metadata?: MetadataConfig
  }) =>
    client.post('/transcode/start', data),

  getTranscodeProgress: (taskId: number) =>
    client.get(`/transcode/progress/${taskId}`, {
      responseType: 'text',
      headers: { 'Accept': 'text/event-stream' }
    }),

  getTasks: (limit: number = 50) =>
    client.get('/transcode/tasks', { params: { limit } }),

  getTask: (taskId: number) =>
    client.get(`/transcode/tasks/${taskId}`),

  cancelTask: (taskId: number) =>
    client.delete(`/transcode/tasks/${taskId}`),

  // Settings operations
  getSettings: () =>
    client.get('/settings/'),

  updateSettings: (settings: any) =>
    client.post('/settings/', settings),

  getSchedulerStatus: () =>
    client.get('/settings/scheduler/status'),

  startScheduler: () =>
    client.post('/settings/scheduler/start'),

  stopScheduler: () =>
    client.post('/settings/scheduler/stop'),

  scanNow: () =>
    client.post('/settings/scheduler/scan-now'),

  clearScanHistory: () =>
    client.delete('/settings/scan-history')
}

// Types
export interface FileInfo {
  path: string
  name: string
  size: number
  extension: string
  is_dir: boolean
  modified?: number
}

export interface DirectoryInfo {
  path: string
  files: FileInfo[]
  parent?: string
  error?: string
}

export interface MetadataConfig {
  title?: string
  author?: string
  album?: string
  year?: number
  comment?: string
  description?: string
  copyright?: string
  genre?: string
  custom?: Record<string, string>
}

export interface Task {
  id: number
  input_path: string
  output_path: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  error?: string
  created_at: string
  completed_at?: string
  metadata?: MetadataConfig
}

export interface TranscodeSettings {
  output_dir: string
  delete_source: boolean
  auto_scan_enabled: boolean
  auto_scan_interval: number
  scan_input_dir: string
  metadata_title?: string
  metadata_author?: string
  metadata_album?: string
  metadata_year?: number
  metadata_comment?: string
  metadata_description?: string
  metadata_copyright?: string
  metadata_genre?: string
  metadata_custom?: string
  scanned_files: string[]
}

export interface SchedulerStatus {
  running: boolean
  enabled: boolean
  interval: number
  scan_dir: string
  scanned_count: number
}
