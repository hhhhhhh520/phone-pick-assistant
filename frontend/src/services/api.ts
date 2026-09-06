const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8002';

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

  const requestBody = JSON.stringify({ message, session_id: sessionId });

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: requestBody,
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
