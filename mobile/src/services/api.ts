/**
 * API service layer for DiverseFocus-IA mobile app.
 *
 * Handles authentication token management, all API calls to the
 * gateway, and provides typed response interfaces.
 */

import axios, { type AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, API_TIMEOUT_MS } from '../config';

const TOKEN_KEY = '@diversefocus_token';

// ── Response types ─────────────────────────────────────────────────────────

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}

export interface SimplifyResponse {
  simplified_text: string;
  level: string;
  original_length: number;
  simplified_length: number;
}

export interface TranscriptResponse {
  transcript: string;
  language: string;
  segments: Array<{ start: number; end: number; text: string }>;
}

export interface UserProfile {
  user_id: string;
  username: string;
  email: string | null;
  preferences: Record<string, unknown>;
  created_at: string;
}

export interface UpdateProfilePayload {
  username?: string;
  email?: string;
  preferences?: Record<string, unknown>;
}

export interface Task {
  id: number;
  user_id: string;
  task_type: string;
  content: string;
  result: string | null;
  created_at: string;
}

// ── Axios instance ─────────────────────────────────────────────────────────

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT_MS,
  headers: { 'Content-Type': 'application/json' },
});

// Attach token to every request automatically
axiosInstance.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Token helpers ──────────────────────────────────────────────────────────

async function saveToken(token: string): Promise<void> {
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

async function clearToken(): Promise<void> {
  await AsyncStorage.removeItem(TOKEN_KEY);
}

async function getStoredToken(): Promise<string | null> {
  return AsyncStorage.getItem(TOKEN_KEY);
}

// ── API methods ────────────────────────────────────────────────────────────

async function login(username: string, password: string): Promise<AuthTokenResponse> {
  const response = await axiosInstance.post<AuthTokenResponse>('/api/v1/auth/login', {
    username,
    password,
  });
  await saveToken(response.data.access_token);
  return response.data;
}

async function logout(): Promise<void> {
  await clearToken();
}

async function simplifyText(text: string, level: string = 'medium'): Promise<SimplifyResponse> {
  const response = await axiosInstance.post<SimplifyResponse>('/api/v1/ai/simplify', {
    text,
    level,
  });
  return response.data;
}

async function transcribeAudio(fileUri: string, fileName: string): Promise<TranscriptResponse> {
  const formData = new FormData();
  formData.append('file', {
    uri: fileUri,
    name: fileName,
    type: 'audio/mpeg',
  } as unknown as Blob);

  const response = await axiosInstance.post<TranscriptResponse>(
    '/api/v1/ai/transcribe',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return response.data;
}

async function getProfile(): Promise<UserProfile> {
  const response = await axiosInstance.get<UserProfile>('/api/v1/user/profile');
  return response.data;
}

async function updateProfile(payload: UpdateProfilePayload): Promise<UserProfile> {
  const response = await axiosInstance.put<UserProfile>('/api/v1/user/profile', payload);
  return response.data;
}

async function getTasks(): Promise<Task[]> {
  const response = await axiosInstance.get<Task[]>('/api/v1/user/tasks');
  return response.data;
}

async function createTask(
  task_type: string,
  content: string,
  result?: string,
): Promise<Task> {
  const response = await axiosInstance.post<Task>('/api/v1/user/tasks', {
    task_type,
    content,
    result,
  });
  return response.data;
}

// ── Exported API object ────────────────────────────────────────────────────

export const api = {
  login,
  logout,
  simplifyText,
  transcribeAudio,
  getProfile,
  updateProfile,
  getTasks,
  createTask,
  getStoredToken,
};
