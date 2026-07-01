export interface Chat {
  chat_id: number;
  name: string;                 // display name (first_name)
  full_name?: string;           // first_name + last_name
  username?: string;            // @username without @
  last_message_preview: string;
  last_message_at: string;
  auto_enabled: boolean;
  conversation_status: 'active' | 'closed';
}

export interface Photo {
  filename: string;
  size_bytes: number;
  enabled: boolean;
  url: string;
}
