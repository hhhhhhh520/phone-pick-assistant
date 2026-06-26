import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QuickReplyButtons } from '../components/QuickReplyButtons';

describe('QuickReplyButtons', () => {
  it('renders all options', () => {
    const options = ['1000-2000元', '2000-3000元', '3000-5000元'];
    render(<QuickReplyButtons options={options} onSelect={() => {}} />);

    options.forEach((option) => {
      expect(screen.getByText(option)).toBeInTheDocument();
    });
  });

  it('calls onSelect when button is clicked', () => {
    const options = ['选项A', '选项B'];
    const onSelect = vi.fn();
    render(<QuickReplyButtons options={options} onSelect={onSelect} />);

    fireEvent.click(screen.getByText('选项A'));
    expect(onSelect).toHaveBeenCalledWith('选项A');
  });

  it('does not render when options is empty', () => {
    const { container } = render(<QuickReplyButtons options={[]} onSelect={() => {}} />);
    expect(container.firstChild).toBeNull();
  });

  it('disables buttons when disabled prop is true', () => {
    const options = ['选项A'];
    const onSelect = vi.fn();
    render(<QuickReplyButtons options={options} onSelect={onSelect} disabled />);

    const button = screen.getByText('选项A');
    expect(button).toBeDisabled();

    fireEvent.click(button);
    expect(onSelect).not.toHaveBeenCalled();
  });
});
