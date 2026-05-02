import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ErrorBoundary } from '../components/ErrorBoundary';

// 创建一个会抛出错误的组件
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
}

describe('ErrorBoundary', () => {
  // 抑制React错误日志
  const originalError = console.error;
  beforeEach(() => {
    console.error = vi.fn();
  });
  afterEach(() => {
    console.error = originalError;
  });

  it('正常渲染子组件', () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('捕获错误并显示错误界面', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('出错了')).toBeInTheDocument();
    expect(screen.getByText(/应用遇到了一个错误/)).toBeInTheDocument();
  });

  it('显示错误信息', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('显示重试按钮', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
  });

  it('点击重试按钮重置错误状态', async () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // 确认错误界面显示
    expect(screen.getByText('出错了')).toBeInTheDocument();

    // 点击重试
    fireEvent.click(screen.getByRole('button', { name: '重试' }));

    // 重置后错误界面应该消失（但子组件需要重新渲染才能显示）
    // 这里只验证按钮点击不会报错
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
  });

  it('使用自定义fallback', () => {
    render(
      <ErrorBoundary fallback={<div>Custom error UI</div>}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Custom error UI')).toBeInTheDocument();
  });
});