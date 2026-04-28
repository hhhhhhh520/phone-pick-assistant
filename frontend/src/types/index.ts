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
  pros: string[];
  cons: string[];
  suitable_for: string[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  phones?: Phone[];
  timestamp: Date;
}

export type IntentType = 'recommend' | 'compare' | 'filter';

export interface SearchHistoryItem {
  id: string;
  query: string;
  phones: Phone[];
  timestamp: number;
}
