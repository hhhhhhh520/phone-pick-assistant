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
  painPointType?: string;  // 痛点追问类型 (battery, storage, camera, performance, screen)
  painPointSeverity?: string;  // 痛点严重程度 (mild, moderate, severe)
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
