export interface Chat {
  chat_id: number;
  name: string;
  full_name?: string;
  username?: string;
  last_message_preview: string;
  last_message_at: string;
  auto_enabled: boolean;
  conversation_status: 'active' | 'closed';
  is_vip: boolean;
  total_conversations: number;
  total_cost_usd: number;
  current_session_photos: string[];
}

export interface Photo {
  filename: string;
  size_bytes: number;
  enabled: boolean;
  url: string;
  caption?: string;
}

export interface ChatPhotos {
  chat_id: number;
  assigned_filenames: string[];
}

export interface ConversationHistory {
  id: number;
  started_at: string;
  ended_at: string | null;
  turn_count: number;
  max_turns: number | null;
  status: string;
  photos: string[];
  cost_usd: number;
}

export interface ChatHistory {
  chat_id: number;
  total_conversations: number;
  conversations: ConversationHistory[];
}

export interface CostSummary {
  total_calls: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
}

export interface ChatCost {
  chat_id: number;
  chat_name: string;
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
}

export interface CostEntry {
  chat_id: number;
  chat_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  timestamp: string;
}


export interface Photo {
  filename: string;
  size_bytes: number;
  enabled: boolean;
  url: string;
}

export interface ChatPhotos {
  chat_id: number;
  assigned_filenames: string[];
}

export interface CostSummary {
  total_calls: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
}

export interface ChatCost {
  chat_id: number;
  chat_name: string;
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
}

export interface CostEntry {
  chat_id: number;
  chat_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  timestamp: string;
}
