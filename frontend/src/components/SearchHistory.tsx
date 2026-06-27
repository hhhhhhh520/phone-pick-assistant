import type { SearchHistoryItem } from '../types';

interface SearchHistoryProps {
  history: SearchHistoryItem[];
  onSelect: (item: SearchHistoryItem) => void;
  onClear: () => void;
}

export function SearchHistory({ history, onSelect, onClear }: SearchHistoryProps) {
  if (history.length === 0) {
    return null;
  }

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return `${days}天前`;
  };

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-2" aria-label="搜索历史">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">搜索历史</span>
        <button
          onClick={onClear}
          aria-label="清空搜索历史"
          className="text-xs text-gray-400 hover:text-gray-600"
        >
          清空
        </button>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1" role="list">
        {history.slice(0, 10).map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(item)}
            aria-label={`${item.query} - ${formatTime(item.timestamp)}`}
            className="flex-shrink-0 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-700 transition-colors"
          >
            <span className="truncate max-w-[120px] inline-block">{item.query}</span>
            <span className="text-gray-400 text-xs ml-1">
              {formatTime(item.timestamp)}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
