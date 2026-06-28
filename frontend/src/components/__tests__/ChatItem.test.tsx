import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ChatItem } from '../ChatItem';
import { Chat } from '../../types';

describe('ChatItem', () => {
  const mockChat: Chat = {
    chat_id: 123,
    name: 'Juan',
    last_message_preview: 'Hola!',
    last_message_at: '2024-01-01T10:00:00',
    auto_enabled: false,
    conversation_status: 'active',
  };

  it('renders chat info correctly', () => {
    render(<ChatItem chat={mockChat} onToggle={() => {}} />);
    expect(screen.getByText('Juan')).toBeInTheDocument();
    expect(screen.getByText('Hola!')).toBeInTheDocument();
    expect(screen.getByText('Activa')).toBeInTheDocument();
  });

  it('shows closed badge when conversation is closed', () => {
    const closedChat = { ...mockChat, conversation_status: 'closed' as const };
    render(<ChatItem chat={closedChat} onToggle={() => {}} />);
    expect(screen.getByText('Cerrada')).toBeInTheDocument();
  });

  it('calls onToggle with correct params', () => {
    const mockToggle = vi.fn();
    render(<ChatItem chat={mockChat} onToggle={mockToggle} />);
    const toggle = screen.getByRole('checkbox');
    fireEvent.click(toggle);
    expect(mockToggle).toHaveBeenCalledWith(123, true);
  });

  it('renders first letter of name as avatar', () => {
    render(<ChatItem chat={mockChat} onToggle={() => {}} />);
    expect(screen.getByText('J')).toBeInTheDocument();
  });
});
