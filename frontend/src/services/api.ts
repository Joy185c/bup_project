import type { OptimizeRequest, OptimizeResponse } from '../types/api.types';

const BASE_URL = import.meta.env.PROD 
  ? (import.meta.env.VITE_API_BASE_URL ?? '') 
  : (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000');

export type ApiStatus = 'online' | 'offline' | 'checking';

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`, { signal: AbortSignal.timeout(4000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function optimizeEnergy(payload: OptimizeRequest): Promise<OptimizeResponse> {
  const res = await fetch(`${BASE_URL}/optimize-energy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(60000), // 60s — MILP + LLM can take a while
  });

  if (!res.ok) {
    let errMsg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      errMsg = body.message ?? body.error ?? errMsg;
    } catch { /* ignore */ }
    throw new Error(errMsg);
  }

  return res.json() as Promise<OptimizeResponse>;
}
