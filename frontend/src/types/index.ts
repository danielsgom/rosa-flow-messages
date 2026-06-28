export interface Chat {
  chat_id: number;
  name: string;
  last_message_preview: string;
  last_message_at: string;
  auto_enabled: boolean;
  conversation_status: 'active' | 'closed';
}
