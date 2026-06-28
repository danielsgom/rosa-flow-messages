import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { HomePage } from '../HomePage';

vi.mock('../../hooks/useChats', () => ({
  useChats: () => ({
    chats: [],
    loading: false,
    error: null,
    toggleAuto: () => {},
    refresh: () => {},
  }),
}));

describe('HomePage', () => {
  it('renders title and subtitle', () => {
    render(<HomePage />);
    expect(screen.getByText('Rosa Flow')).toBeInTheDocument();
    expect(screen.getByText('Gestiona tus conversaciones de Telegram con IA')).toBeInTheDocument();
  });

  it('renders stats cards', () => {
    render(<HomePage />);
    expect(screen.getByText('Chats')).toBeInTheDocument();
    expect(screen.getByText('Auto activo')).toBeInTheDocument();
    expect(screen.getByText('Activas')).toBeInTheDocument();
  });
});
