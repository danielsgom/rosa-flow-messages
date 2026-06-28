import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ChatList } from '../ChatList';
import { Chat } from '../../types';

describe('ChatList', () => {
  const mockChats: Chat[] = [
    {
      chat_id: 1,
      name: 'Ana',
      last_message_preview: 'Hola!',
      last_message_at: '2024-01-01T10:00:00',
      auto_enabled: true,
      conversation_status: 'active',
    },
    {
      chat_id: 2,
      name: 'Luis',
      last_message_preview: 'Adios',
      last_message_at: '2024-01-01T09:00:00',
      auto_enabled: false,
      conversation_status: 'closed',
    },
  ];

  it('renders loading state', () => {
    render(<ChatList chats={[]} onToggle={() => {}} loading={true} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    render(<ChatList chats={[]} onToggle={() => {}} loading={false} />);
    expect(screen.getByText('No hay conversaciones aún')).toBeInTheDocument();
  });

  it('renders list of chats', () => {
    render(<ChatList chats={mockChats} onToggle={() => {}} loading={false} />);
    expect(screen.getByText('Ana')).toBeInTheDocument();
    expect(screen.getByText('Luis')).toBeInTheDocument();
    expect(screen.getByText('Activa')).toBeInTheDocument();
    expect(screen.getByText('Cerrada')).toBeInTheDocument();
  });
});
