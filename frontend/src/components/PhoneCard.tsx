import { useState } from 'react';
import type { Phone, CameraScoring } from '../types';
import { formatStorage } from '../utils/format';

interface PhoneCardProps {
  phone: Phone;
}

// API基础地址
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8002';

/**
 * 把数据库里的 `image_url` 转成浏览器可用的完整地址。
 *
 * 数据库里混着两种本地路径写法：`images\x.jpg`（Windows 反斜杠，132 条 / 38%）
 * 与 `/images/x.jpg`。反斜杠必须归一化——`encodeURI` 不会把 `\` 变成 `/`，
 * 而是编成 `%5C`，于是拼出 `http://localhost:8002images%5C...`：主机名被吃成
 * `localhost:8002images`，浏览器直接拒绝解析、**连请求都不发**，静默换成默认图标（ISSUE-046）。
 *
 * 导出供单测；组件内调用走默认基址。
 */
export function getFullImageUrl(
  url: string | undefined,
  apiBase: string = API_BASE
): string | null {
  if (!url) return null;
  // 外部URL（如中关村在线图床）直接使用，不重复编码
  if (url.startsWith('http://') || url.startsWith('https://')) return url;

  // 1) 反斜杠统一成正斜杠
  // 2) 路径以 / 开头、基址去掉尾斜杠 → 二者之间恰好一个斜杠
  const path = url.replace(/\\/g, '/');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const base = apiBase.replace(/\/+$/, '');

  // 文件名含 + (如 12GB+256GB) 需编码为 %2B，否则浏览器当作空格 → 404
  // 已含 % 视为已编码，跳过避免双重编码
  const encoded = normalizedPath.includes('%')
    ? normalizedPath
    : encodeURI(normalizedPath).replace(/\+/g, '%2B');

  return `${base}${encoded}`;
}

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

export function PhoneCard({ phone }: PhoneCardProps) {
  const [imageError, setImageError] = useState(false);

  const fullImageUrl = getFullImageUrl(phone.imageUrl);
  const showDefaultIcon = !fullImageUrl || imageError;

  // 型号去重：model 字段常含品牌前缀（如"小米15 Pro"），避免与 brand 行重复显示 (ISSUE-038)
  // null guard：brand/model 可能为空字符串或 undefined
  const displayModel = phone.model
    ? (phone.brand && phone.model.startsWith(phone.brand) ? phone.model.slice(phone.brand.length).trim() || phone.model : phone.model)
    : '-';

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4"
      aria-label={`${phone.brand} ${phone.model} - ${phone.price}元`}
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
            loading="lazy"
            decoding="async"
            onError={() => setImageError(true)}
          />
        )}
      </div>

      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="text-sm text-gray-500">{phone.brand}</span>
          <h3 className="font-medium text-gray-900">{displayModel}</h3>
        </div>
        <span className="text-lg font-semibold text-blue-600">¥{phone.price}</span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
        <div>
          <span className="text-gray-400">处理器:</span> {phone.processor || '-'}
        </div>
        <div>
          <span className="text-gray-400">内存:</span> {phone.ram ? `${phone.ram}GB` : '-'}
        </div>
        <div>
          <span className="text-gray-400">存储:</span> {formatStorage(phone.storage)}
        </div>
        <div>
          <span className="text-gray-400">电池:</span> {phone.battery ? `${phone.battery}mAh` : '-'}
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
