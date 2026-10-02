import type { Message } from '../types';
import { PhoneCard } from './PhoneCard';
import { CompareTable } from './CompareTable';
import { QuickReplyButtons } from './QuickReplyButtons';

interface MessageItemProps {
  message: Message;
  onQuickReply?: (reply: string) => void;
  loading?: boolean;
}

export function MessageItem({ message, onQuickReply, loading }: MessageItemProps) {
  const isUser = message.role === 'user';
  const isCompare = message.isCompare ?? false;
  const isQuestion = message.isQuestion ?? false;
  const isPainPoint = message.painPointType !== undefined;

  // 追问消息使用特殊样式
  const getContainerClass = () => {
    if (isUser) {
      return 'bg-blue-500 text-white rounded-2xl rounded-br-md';
    }
    if (isQuestion) {
      // 痛点追问使用橙红色边框样式
      if (isPainPoint) {
        return 'bg-orange-50 text-gray-800 border-2 border-orange-300 rounded-2xl rounded-bl-md shadow-sm';
      }
      return 'bg-blue-50 text-gray-800 border border-blue-200 rounded-2xl rounded-bl-md';
    }
    return 'bg-white border border-gray-200 rounded-2xl rounded-bl-md';
  };

  // 痛点追问标题
  const getPainPointTitle = () => {
    if (!isPainPoint) return null;
    const typeNames: Record<string, string> = {
      // 旧语义键（历史 payload，保留兼容）
      battery: '续航问题',
      storage: '存储空间',
      camera: '影像表现',
      performance: '性能表现',
      screen: '屏幕体验',
      // 后端 question.py PAIN_POINT_TEMPLATES 全集 (ISSUE-049)
      budget_too_low_for_features: '预算不足',
      brand_budget_conflict: '品牌与预算',
      gaming_camera_budget_conflict: '游戏与拍照',
      battery_vs_gaming: '续航与游戏',
      high_demand_low_budget_general: '需求与预算',
      brand_not_match_features: '品牌与功能'
    };
    const severityColors: Record<string, string> = {
      // 后端实际枚举 question.py severity="high/medium/low" (ISSUE-049)
      high: 'text-red-600',
      medium: 'text-orange-600',
      low: 'text-orange-500',
      // 旧键保留
      mild: 'text-orange-500',
      moderate: 'text-orange-600',
      severe: 'text-red-600'
    };
    const severityLabels: Record<string, string> = {
      high: '重点关注',
      medium: '中度关注',
      low: '轻度关注',
      // 旧键保留
      mild: '轻度关注',
      moderate: '中度关注',
      severe: '重点关注'
    };
    // 未命中的新 code 兜底通用文案，避免内部 code 泄漏到用户可见标题 (ISSUE-049)
    const typeName = typeNames[message.painPointType!] || '偏好确认';
    const severityColor = severityColors[message.painPointSeverity!] || 'text-orange-500';
    const severityLabel = severityLabels[message.painPointSeverity!] || '';

    return (
      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-orange-200">
        <span className="text-lg">⚠️</span>
        <span className="font-medium text-orange-700">关于{typeName}的追问</span>
        {severityLabel && (
          <span className={`text-xs px-2 py-0.5 rounded-full bg-orange-100 ${severityColor}`}>
            {severityLabel}
          </span>
        )}
      </div>
    );
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${getContainerClass()} px-4 py-3`}>
        {getPainPointTitle()}
        {loading && !message.content && !isQuestion ? (
          <div className="flex gap-1 p-1" aria-label="正在生成回复">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{message.content}</p>
        )}

        {/* 系统提示（独立灰色条，不污染 content）(ISSUE-036/039) */}
        {message.notice && (
          <div className="mt-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
            ⚠️ {message.notice}
          </div>
        )}

        {/* 快捷回复按钮 */}
        {isQuestion && message.quickReplies && message.quickReplies.length > 0 && (
          <QuickReplyButtons
            options={message.quickReplies}
            onSelect={(reply) => onQuickReply?.(reply)}
            isPainPoint={isPainPoint}
          />
        )}

        {message.phones && message.phones.length > 0 && (
          isCompare ? (
            <CompareTable phones={message.phones} />
          ) : (
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {message.phones.map((phone) => (
                <PhoneCard key={phone.id} phone={phone} />
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
