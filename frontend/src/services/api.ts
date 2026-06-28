import { Chat } from '../types';

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
