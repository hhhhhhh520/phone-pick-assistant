import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { InputBar } from '../components/InputBar';

describe('InputBar', () => {
  // 渲染输入框和发送按钮
  it('renders input field and send button', () => {
    render(<InputBar onSend={() => {}} />);

    expect(screen.getByPlaceholderText('输入你的问题...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '发送' })).toBeInTheDocument();
  });

  // 输入文本后发送按钮可点击
  it('enables send button when text is entered', () => {
    render(<InputBar onSend={() => {}} />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    const sendButton = screen.getByRole('button', { name: '发送' });

    expect(sendButton).toBeDisabled();

    fireEvent.change(input, { target: { value: '推荐一款手机' } });
    expect(sendButton).not.toBeDisabled();
  });

  // 提交后清空输入
  it('clears input after submission', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '推荐一款手机' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    expect(onSend).toHaveBeenCalledWith('推荐一款手机');
    expect(input).toHaveValue('');
  });

  // 空输入不提交
  it('does not submit empty input', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} />);

    const sendButton = screen.getByRole('button', { name: '发送' });
    fireEvent.click(sendButton);

    expect(onSend).not.toHaveBeenCalled();
  });

  // 纯空格输入不提交
  it('does not submit whitespace-only input', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    expect(onSend).not.toHaveBeenCalled();
  });

  // 提交时去除首尾空格
  it('trims whitespace from input before sending', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '  推荐手机  ' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    expect(onSend).toHaveBeenCalledWith('推荐手机');
  });

  // 表单提交（Enter键）
  it('submits on form submit event', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '测试' } });
    fireEvent.submit(input.closest('form')!);

    expect(onSend).toHaveBeenCalledWith('测试');
  });

  // disabled 状态下显示取消按钮
  it('shows cancel button when disabled and onCancel provided', () => {
    render(<InputBar onSend={() => {}} onCancel={() => {}} disabled />);

    expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '发送' })).not.toBeInTheDocument();
  });

  // disabled 状态下输入框被禁用
  it('disables input when disabled prop is true', () => {
    render(<InputBar onSend={() => {}} onCancel={() => {}} disabled />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    expect(input).toBeDisabled();
  });

  // 点击取消按钮触发 onCancel
  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn();
    render(<InputBar onSend={() => {}} onCancel={onCancel} disabled />);

    fireEvent.click(screen.getByRole('button', { name: '取消' }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  // 未提供 onCancel 时不显示取消按钮（即使 disabled）
  it('does not show cancel button when onCancel is not provided', () => {
    render(<InputBar onSend={() => {}} disabled />);

    expect(screen.queryByRole('button', { name: '取消' })).not.toBeInTheDocument();
    // 应该显示发送按钮（虽然 disabled）
    expect(screen.getByRole('button', { name: '发送' })).toBeInTheDocument();
  });

  // disabled 状态下没有 onCancel 时仍显示发送按钮
  it('shows send button (not cancel) when disabled without onCancel', () => {
    render(<InputBar onSend={() => {}} disabled />);

    const sendButton = screen.getByRole('button', { name: '发送' });
    expect(sendButton).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '取消' })).not.toBeInTheDocument();
  });

  // 多次提交
  it('handles multiple submissions', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入你的问题...');

    fireEvent.change(input, { target: { value: '第一次' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    fireEvent.change(input, { target: { value: '第二次' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    expect(onSend).toHaveBeenCalledTimes(2);
    expect(onSend).toHaveBeenNthCalledWith(1, '第一次');
    expect(onSend).toHaveBeenNthCalledWith(2, '第二次');
    expect(input).toHaveValue('');
  });
});
