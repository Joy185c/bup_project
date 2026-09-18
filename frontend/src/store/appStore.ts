import { create } from 'zustand';
import type { OptimizeResponse, HistoryEntry, OptimizeRequest } from '../types/api.types';

interface AppState {
  lastResult: OptimizeResponse | null;
  lastRequest: OptimizeRequest | null;
  history: HistoryEntry[];
  setResult: (result: OptimizeResponse, request: OptimizeRequest) => void;
  clearResult: () => void;
}

// Simple in-memory + localStorage store
function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem('gridwise_history');
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveHistory(entries: HistoryEntry[]) {
  try {
    // Keep last 20
    localStorage.setItem('gridwise_history', JSON.stringify(entries.slice(0, 20)));
  } catch { /* ignore quota errors */ }
}

export const useAppStore = create<AppState>((set, get) => ({
  lastResult: null,
  lastRequest: null,
  history: loadHistory(),

  setResult: (result, request) => {
    const entry: HistoryEntry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      timestamp: new Date().toISOString(),
      scenario_id: result.scenario_id,
      operator_notes: request.operator_notes,
      result,
      request,
    };
    const newHistory = [entry, ...get().history].slice(0, 20);
    saveHistory(newHistory);
    set({ lastResult: result, lastRequest: request, history: newHistory });
  },

  clearResult: () => set({ lastResult: null, lastRequest: null }),
}));
