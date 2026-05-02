import type { Phone } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// AbortController 用于取消请求
let currentController: AbortController | null = null;

export function abortCurrentRequest(): void {
  if (currentController) {
    currentController.abort();
    currentController = null;
  }
}

export async function* chatStream(
  message: string,
  sessionId?: string | null
): AsyncGenerator<{ type: string; data: unknown }> {
  // 取消之前的请求
  abortCurrentRequest();

  currentController = new AbortController();

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    cache: 'no-store',
    signal: currentController.signal,
  });

  if (!response.ok) {
    currentController = null;
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    currentController = null;
    throw new Error('No reader available');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            yield data;
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  } finally {
    currentController = null;
  }
}

export async function getPhones(params?: {
  brand?: string;
  min_price?: number;
  max_price?: number;
  limit?: number;
}): Promise<{ phones: Phone[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.brand) searchParams.set('brand', params.brand);
  if (params?.min_price) searchParams.set('min_price', String(params.min_price));
  if (params?.max_price) searchParams.set('max_price', String(params.max_price));
  if (params?.limit) searchParams.set('limit', String(params.limit));

  const response = await fetch(`${API_BASE}/api/phones?${searchParams}`);
  return response.json();
}

export async function getPhone(id: number): Promise<Phone> {
  const response = await fetch(`${API_BASE}/api/phones/${id}`);
  return response.json();
}
