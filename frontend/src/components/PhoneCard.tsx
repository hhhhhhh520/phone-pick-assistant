import { Phone } from '../types';

interface PhoneCardProps {
  phone: Phone;
  onClick?: () => void;
}

export function PhoneCard({ phone, onClick }: PhoneCardProps) {
  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
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
    </div>
  );
}
