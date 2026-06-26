interface QuickReplyButtonsProps {
  options: string[];
  onSelect: (option: string) => void;
  disabled?: boolean;
  isPainPoint?: boolean;  // 是否为痛点追问
}

/**
 * 快捷回复按钮组件
 * 用于追问消息中展示可选的快捷回复选项
 * 痛点追问使用警告图标和橙色/红色边框样式
 */
export function QuickReplyButtons({ options, onSelect, disabled = false, isPainPoint = false }: QuickReplyButtonsProps) {
  if (options.length === 0) {
    return null;
  }

  // 痛点追问样式：警告图标 + 橙色边框
  const buttonClass = isPainPoint
    ? `${disabled
        ? 'bg-orange-50 text-orange-300 border-orange-200 cursor-not-allowed'
        : 'bg-orange-50 text-orange-700 border-orange-300 hover:bg-orange-100 hover:border-orange-400 active:bg-orange-200'
      }`
    : `${disabled
        ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
        : 'bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100 hover:border-blue-300 active:bg-blue-200'
      }`;

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {options.map((option, index) => (
        <button
          key={index}
          onClick={() => onSelect(option)}
          disabled={disabled}
          className={`px-3 py-1.5 text-sm rounded-full border transition-all duration-200 flex items-center gap-1.5 ${buttonClass}`}
        >
          {isPainPoint && <span className="text-base">⚠️</span>}
          {option}
        </button>
      ))}
    </div>
  );
}
