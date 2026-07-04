import { Chat, Photo, ChatPhotos, CostSummary, ChatCost, CostEntry, ChatHistory } from '../types';

const API_BASE = '/api';

export async function getChats(): Promise<Chat[]> {
  const response = await fetch(`${API_BASE}/chats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch chats: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleChat(chatId: number, enabled: boolean): Promise<Chat> {
  const response = await fetch(`${API_BASE}/chats/${chatId}/toggle`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) {
    throw new Error(`Failed to toggle chat: ${response.statusText}`);
  }
  return response.json();
}

export interface SyncResult {
  synced: number;
  total: number;
  chats: Chat[];
}

export async function syncChats(): Promise<SyncResult> {
  const response = await fetch(`${API_BASE}/chats/sync`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to sync chats: ${response.statusText}`);
  }
  return response.json();
}

// ---------------------------------------------------------------------------
// Photo API
// ---------------------------------------------------------------------------

export async function getPhotos(): Promise<{ total: number; photos: Photo[] }> {
  const response = await fetch(`${API_BASE}/photos`);
  if (!response.ok) throw new Error(`Failed to fetch photos: ${response.statusText}`);
  return response.json();
}

export async function uploadPhoto(file: File): Promise<Photo> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`${API_BASE}/photos`, { method: 'POST', body: form });
  if (!response.ok) throw new Error(`Failed to upload photo: ${response.statusText}`);
  return response.json();
}

export async function deletePhoto(filename: string): Promise<void> {
  const response = await fetch(`${API_BASE}/photos/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete photo: ${response.statusText}`);
}

export async function togglePhoto(filename: string, enabled: boolean): Promise<Photo> {
  const response = await fetch(`${API_BASE}/photos/${encodeURIComponent(filename)}/toggle`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) throw new Error(`Failed to toggle photo: ${response.statusText}`);
  return response.json();
}

export async function updatePhotoCaption(filename: string, caption: string | null): Promise<Photo> {
  const response = await fetch(`${API_BASE}/photos/${encodeURIComponent(filename)}/caption`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ caption }),
  });
  if (!response.ok) throw new Error(`Failed to update caption: ${response.statusText}`);
  return response.json();
}

// ---------------------------------------------------------------------------
// Chat photo assignment API
// ---------------------------------------------------------------------------

export async function getChatPhotos(chatId: number): Promise<ChatPhotos> {
  const response = await fetch(`${API_BASE}/chats/${chatId}/photos`);
  if (!response.ok) throw new Error(`Failed to get chat photos: ${response.statusText}`);
  return response.json();
}

export async function setChatPhotos(chatId: number, filenames: string[]): Promise<ChatPhotos> {
  const response = await fetch(`${API_BASE}/chats/${chatId}/photos`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filenames }),
  });
  if (!response.ok) throw new Error(`Failed to set chat photos: ${response.statusText}`);
  return response.json();
}

// ---------------------------------------------------------------------------
// Cost tracking API
// ---------------------------------------------------------------------------

export async function getCostSummary(): Promise<CostSummary> {
  const response = await fetch(`${API_BASE}/costs/summary`);
  if (!response.ok) throw new Error(`Failed to get cost summary: ${response.statusText}`);
  return response.json();
}

export async function getCostByChat(): Promise<ChatCost[]> {
  const response = await fetch(`${API_BASE}/costs/by-chat`);
  if (!response.ok) throw new Error(`Failed to get costs by chat: ${response.statusText}`);
  return response.json();
}

export async function getRecentCosts(n = 50): Promise<CostEntry[]> {
  const response = await fetch(`${API_BASE}/costs/recent?n=${n}`);
  if (!response.ok) throw new Error(`Failed to get recent costs: ${response.statusText}`);
  return response.json();
}

// ---------------------------------------------------------------------------
// VIP & history
// ---------------------------------------------------------------------------

export async function setVip(chatId: number, isVip: boolean): Promise<Chat> {
  const response = await fetch(`${API_BASE}/chats/${chatId}/vip`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_vip: isVip }),
  });
  if (!response.ok) throw new Error(`Failed to set VIP: ${response.statusText}`);
  return response.json();
}

export async function getChatHistory(chatId: number): Promise<ChatHistory> {
  const response = await fetch(`${API_BASE}/chats/${chatId}/history`);
  if (!response.ok) throw new Error(`Failed to get chat history: ${response.statusText}`);
  return response.json();
}

