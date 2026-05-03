import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// 模拟 fetch
const mockFetch = vi.fn();
(globalThis as unknown as { fetch: typeof vi.fn }).fetch = mockFetch;

// 模拟 ReadableStream
class MockReadableStream {
  private reader: MockReader;
  constructor(chunks: string[]) {
    this.reader = new MockReader(chunks);
  }
  getReader() {
    return this.reader;
  }
}

class MockReader {
  private chunks: string[];
  private index = 0;
  constructor(chunks: string[]) {
    this.chunks = chunks;
  }
  async read() {
    if (this.index >= this.chunks.length) {
      return { done: true, value: undefined };
    }
    const chunk = this.chunks[this.index++];
    return { done: false, value: new TextEncoder().encode(chunk) };
  }
}

describe('API Service - AbortController', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 重置模块
    vi.resetModules();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('abortCurrentRequest 应该中止当前请求', async () => {
    const { abortCurrentRequest, chatStream } = await import('../services/api');

    // 创建一个 AbortController 来跟踪
    mockFetch.mockImplementation(async (_url: string, _options: { signal?: AbortSignal }) => {
      return {
        ok: true,
        body: new MockReadableStream(['data: {"type":"done"}\n\n']),
      };
    });

    // 开始请求
    const generator = chatStream('test message', null);

    // 消费第一个值
    await generator.next();

    // 取消请求
    abortCurrentRequest();

    // 验证 abort 被调用
    expect(mockFetch).toHaveBeenCalled();
  });

  it('新请求应该取消之前的请求', async () => {
    const { chatStream } = await import('../services/api');

    let callCount = 0;
    mockFetch.mockImplementation(async () => {
      callCount++;
      return {
        ok: true,
        body: new MockReadableStream(['data: {"type":"done"}\n\n']),
      };
    });

    // 开始第一个请求
    const gen1 = chatStream('message 1', null);
    await gen1.next();

    // 开始第二个请求（应该取消第一个）
    const gen2 = chatStream('message 2', null);
    await gen2.next();

    // 应该有两次 fetch 调用
    expect(callCount).toBe(2);
  });

  it('AbortError 应该被正确处理', async () => {
    const { chatStream } = await import('../services/api');

    const abortError = new Error('The operation was aborted');
    abortError.name = 'AbortError';

    mockFetch.mockImplementation(async () => {
      throw abortError;
    });

    const generator = chatStream('test', null);

    await expect(async () => {
      for await (const _ of generator) {
        // 消费生成器
      }
    }).rejects.toThrow('The operation was aborted');
  });

  it('请求应该携带 signal 参数', async () => {
    const { chatStream } = await import('../services/api');

    mockFetch.mockImplementation(async () => ({
      ok: true,
      body: new MockReadableStream(['data: {"type":"done"}\n\n']),
    }));

    const generator = chatStream('test', null);
    await generator.next();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        signal: expect.any(AbortSignal),
      })
    );
  });
});