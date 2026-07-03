import React, { useEffect, useState } from 'react';
import { CostSummary, ChatCost, CostEntry } from '../types';
import { getCostSummary, getCostByChat, getRecentCosts } from '../services/api';

interface Props {
  onClose: () => void;
}

type Tab = 'summary' | 'by-chat' | 'history';

function formatUsd(value: number): string {
  if (value < 0.001) return `$${(value * 1000).toFixed(4)}m`;
  return `$${value.toFixed(4)}`;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function timeLabel(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString('es-ES', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}

export const CostModal: React.FC<Props> = ({ onClose }) => {
  const [tab, setTab] = useState<Tab>('summary');
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [byChat, setByChat] = useState<ChatCost[]>([]);
  const [recent, setRecent] = useState<CostEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([getCostSummary(), getCostByChat(), getRecentCosts(100)])
      .then(([s, c, r]) => {
        setSummary(s);
        setByChat(c);
        setRecent(r);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 flex-shrink-0">
          <h2 className="text-base font-semibold text-gray-900">Control de gasto</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-100 flex-shrink-0">
          {(['summary', 'by-chat', 'history'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
                tab === t
                  ? 'text-rosa-600 border-b-2 border-rosa-500'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t === 'summary' ? 'Resumen' : t === 'by-chat' ? 'Por chat' : 'Historial'}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 px-5 py-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rosa-500" />
            </div>
          ) : tab === 'summary' && summary ? (
            <SummaryTab summary={summary} />
          ) : tab === 'by-chat' ? (
            <ByChatTab items={byChat} />
          ) : (
            <HistoryTab entries={recent} />
          )}
        </div>
      </div>
    </div>
  );
};

const SummaryTab: React.FC<{ summary: CostSummary }> = ({ summary }) => (
  <div className="space-y-4">
    {/* Big total */}
    <div className="bg-gradient-to-br from-rosa-50 to-pink-50 rounded-xl p-5 text-center">
      <p className="text-xs text-gray-500 mb-1">Gasto total</p>
      <p className="text-4xl font-bold text-rosa-600">{formatUsd(summary.total_cost_usd)}</p>
    </div>

    {/* Stats grid */}
    <div className="grid grid-cols-3 gap-3">
      <StatCard label="Llamadas" value={String(summary.total_calls)} />
      <StatCard label="Tokens entrada" value={formatTokens(summary.total_prompt_tokens)} />
      <StatCard label="Tokens salida" value={formatTokens(summary.total_completion_tokens)} />
    </div>

    <div className="bg-gray-50 rounded-xl p-4 text-xs text-gray-500 space-y-1">
      <p>Modelo: <span className="font-medium text-gray-700">deepseek/deepseek-chat</span></p>
      <p>Precio entrada: <span className="font-medium text-gray-700">$0.27 / 1M tokens</span></p>
      <p>Precio salida: <span className="font-medium text-gray-700">$1.10 / 1M tokens</span></p>
      <p>Total tokens: <span className="font-medium text-gray-700">{formatTokens(summary.total_tokens)}</span></p>
    </div>
  </div>
);

const StatCard: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="bg-gray-50 rounded-xl p-3 text-center">
    <p className="text-lg font-semibold text-gray-800">{value}</p>
    <p className="text-[10px] text-gray-500 mt-0.5">{label}</p>
  </div>
);

const ByChatTab: React.FC<{ items: ChatCost[] }> = ({ items }) => (
  items.length === 0 ? (
    <p className="text-sm text-gray-400 text-center py-8">Sin datos todavía</p>
  ) : (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.chat_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-800 truncate">{item.chat_name}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {item.calls} llamadas · {formatTokens(item.total_tokens)} tokens
            </p>
          </div>
          <span className="ml-3 text-sm font-semibold text-rosa-600 flex-shrink-0">
            {formatUsd(item.cost_usd)}
          </span>
        </div>
      ))}
    </div>
  )
);

const HistoryTab: React.FC<{ entries: CostEntry[] }> = ({ entries }) => (
  entries.length === 0 ? (
    <p className="text-sm text-gray-400 text-center py-8">Sin historial todavía</p>
  ) : (
    <div className="space-y-1.5">
      {entries.map((entry, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-gray-700 truncate">{entry.chat_name}</p>
            <p className="text-[10px] text-gray-400 mt-0.5">
              {timeLabel(entry.timestamp)} · in:{entry.prompt_tokens} out:{entry.completion_tokens}
            </p>
          </div>
          <span className="ml-2 text-xs font-semibold text-gray-600 flex-shrink-0">
            {formatUsd(entry.cost_usd)}
          </span>
        </div>
      ))}
    </div>
  )
);
