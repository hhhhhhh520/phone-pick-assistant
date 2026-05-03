import { useState } from 'react';
import type { Phone, CameraScoring } from '../types';

interface PhoneCardProps {
  phone: Phone;
  onClick?: () => void;
}

// API基础地址
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8002';

// 获取评分等级对应的颜色
function getGradeColor(grade: string): string {
  const gradeColors: Record<string, string> = {
    '顶级': 'text-amber-500',
    '旗舰': 'text-blue-500',
    '高端': 'text-green-500',
    '中端': 'text-orange-500',
    '基础': 'text-gray-500',
  };
  return gradeColors[grade] || 'text-gray-500';
}

// 获取评分对应的进度条颜色
function getScoreColor(score: number): string {
  if (score >= 85) return 'bg-amber-500';
  if (score >= 75) return 'bg-blue-500';
  if (score >= 60) return 'bg-green-500';
  if (score >= 40) return 'bg-orange-500';
  return 'bg-gray-500';
}

// 评分进度条组件
function ScoreBar({ label, score, maxScore = 100 }: { label: string; score: number; maxScore?: number }) {
  const percentage = Math.min((score / maxScore) * 100, 100);

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-gray-500 w-12 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${getScoreColor(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-gray-700 w-6 text-right">{score}</span>
    </div>
  );
}

// 影像评分卡片组件
function CameraScoringCard({ scoring }: { scoring: CameraScoring }) {
  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500">影像评分</span>
        <div className="flex items-center gap-1">
          <span className={`text-sm font-medium ${getGradeColor(scoring.grade)}`}>
            {scoring.grade}
          </span>
          <span className="text-lg font-bold text-gray-800">{scoring.total}</span>
        </div>
      </div>
      <div className="space-y-1.5">
        <ScoreBar label="芯片" score={scoring.chip_score} />
        <ScoreBar label="硬件" score={scoring.hardware_score} />
        <ScoreBar label="算法" score={scoring.algorithm_score} />
      </div>
    </div>
  );
}

// 默认手机图标SVG
function DefaultPhoneIcon() {
  return (
    <svg
      className="w-16 h-16 text-gray-300"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <rect x="5" y="2" width="14" height="20" rx="2" ry="2" strokeWidth="1.5" />
      <line x1="9" y1="18" x2="15" y2="18" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function PhoneCard({ phone, onClick }: PhoneCardProps) {
  const [imageError, setImageError] = useState(false);

  // 处理图片URL：本地路径需要拼接API地址，外部URL直接使用
  const getFullImageUrl = (url: string | undefined): string | null => {
    if (!url) return null;
    // 外部URL（如三星官方图片）直接使用
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    // 本地路径拼接API地址
    return `${API_BASE}${url}`;
  };

  const fullImageUrl = getFullImageUrl(phone.imageUrl);
  const showDefaultIcon = !fullImageUrl || imageError;

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      {/* 手机图片 */}
      <div className="mb-3 flex justify-center items-center h-24">
        {showDefaultIcon ? (
          <DefaultPhoneIcon />
        ) : (
          <img
            src={fullImageUrl!}
            alt={`${phone.brand} ${phone.model}`}
            className="w-24 h-24 object-contain"
            onError={() => setImageError(true)}
          />
        )}
      </div>

      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="text-sm text-gray-500">{phone.brand}</span>
          <h3 className="font-medium text-gray-900">{phone.model}</h3>
        </div>
        <span className="text-lg font-semibold text-blue-600">¥{phone.price}</span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
        <div>
          <span className="text-gray-400">处理器:</span> {phone.processor}
        </div>
        <div>
          <span className="text-gray-400">内存:</span> {phone.ram}GB
        </div>
        <div>
          <span className="text-gray-400">存储:</span> {phone.storage}GB
        </div>
        <div>
          <span className="text-gray-400">电池:</span> {phone.battery}mAh
        </div>
      </div>

      {phone.features.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {phone.features.slice(0, 3).map((feature, i) => (
            <span
              key={i}
              className="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded"
            >
              {feature}
            </span>
          ))}
        </div>
      )}

      {/* 影像评分 */}
      {phone.cameraScoring && (
        <CameraScoringCard scoring={phone.cameraScoring} />
      )}
    </div>
  );
}
