// 影像评分接口
export interface CameraScoring {
  total: number;
  chip_score: number;
  hardware_score: number;
  algorithm_score: number;
  grade: string;
}

// Types for phone picker assistant
export interface Phone {
  id: number;
  brand: string;
  model: string;
  price: number;
  release_date?: string;
  screen: {
    size: number;
    type: string;
    refresh: number;
  };
  processor: string;
  ram: number;
  storage: number;
  camera: {
    main: number;
    ultra: number;
    telephoto: number;
    front: number;
    /** 以下影像字段后端可能返回，缺省为 undefined */
    sensorMain?: string;
    telephotoType?: string;
    hasOis?: boolean;
    imageBrand?: string;
    score?: number;
  };
  battery: number;
  charging: {
    wired: number;
    wireless: number;
  };
  weight: number;
  features: string[];
  url?: string;
  imageUrl?: string;
  pros: string[];
  cons: string[];
  suitable_for: string[];
  cameraScoring?: CameraScoring;  // 影像评分（可选）
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  phones?: Phone[];
  isCompare?: boolean;  // 是否为对比消息
  isQuestion?: boolean;  // 是否为追问消息
  quickReplies?: string[];  // 快捷回复选项
  missingFields?: string[];  // 缺失字段
  painPointType?: string;  // 痛点追问类型：后端 question.py PAIN_POINT_TEMPLATES 6 个 code（+旧语义键 battery 等），渲染映射见 MessageItem.tsx
  painPointSeverity?: string;  // 痛点严重程度：后端实际发 high/medium/low（旧键 mild/moderate/severe 保留兼容），渲染映射见 MessageItem.tsx
  notice?: string;  // 系统提示（如"未找到匹配机型"），独立灰色提示条，不写入会话历史 (ISSUE-036/039)
  timestamp: Date;
}

export type IntentType = 'recommend' | 'compare' | 'filter';

export interface SearchHistoryItem {
  id: string;
  query: string;
  phones: Phone[];
  timestamp: number;
}

// 追问响应
export interface QuestionResponse {
  question: string;
  quick_replies: string[];
  missing_fields: string[];
}
