import type { Phone } from '../types';

interface CompareTableProps {
  phones: Phone[];
}

export function CompareTable({ phones }: CompareTableProps) {
  if (phones.length < 2) {
    return null;
  }

  const [phone1, phone2] = phones;

  // 判断两个值是否不同
  const isDifferent = (a: number | string | undefined, b: number | string | undefined) => {
    if (a === undefined || b === undefined) return false;
    return a !== b;
  };

  // 格式化价格
  const formatPrice = (price: number) => `¥${price.toLocaleString()}`;

  const rows = [
    { label: '品牌', value1: phone1.brand, value2: phone2.brand },
    { label: '型号', value1: phone1.model, value2: phone2.model },
    { label: '价格', value1: formatPrice(phone1.price), value2: formatPrice(phone2.price), highlight: isDifferent(phone1.price, phone2.price) },
    { label: '处理器', value1: phone1.processor, value2: phone2.processor, highlight: isDifferent(phone1.processor, phone2.processor) },
    { label: '内存', value1: `${phone1.ram}GB`, value2: `${phone2.ram}GB`, highlight: isDifferent(phone1.ram, phone2.ram) },
    { label: '存储', value1: `${phone1.storage}GB`, value2: `${phone2.storage}GB`, highlight: isDifferent(phone1.storage, phone2.storage) },
    { label: '屏幕', value1: `${phone1.screen.size}" ${phone1.screen.refresh}Hz`, value2: `${phone2.screen.size}" ${phone2.screen.refresh}Hz` },
    { label: '电池', value1: `${phone1.battery}mAh`, value2: `${phone2.battery}mAh`, highlight: isDifferent(phone1.battery, phone2.battery) },
    { label: '主摄', value1: `${phone1.camera.main}MP`, value2: `${phone2.camera.main}MP`, highlight: isDifferent(phone1.camera.main, phone2.camera.main) },
    { label: '快充', value1: `${phone1.charging.wired}W`, value2: `${phone2.charging.wired}W`, highlight: isDifferent(phone1.charging.wired, phone2.charging.wired) },
    { label: '重量', value1: `${phone1.weight}g`, value2: `${phone2.weight}g`, highlight: isDifferent(phone1.weight, phone2.weight) },
  ];

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-50">
            <th className="border border-gray-200 px-3 py-2 text-left text-gray-600 w-24">参数</th>
            <th className="border border-gray-200 px-3 py-2 text-center text-gray-900 font-medium">
              {phone1.brand} {phone1.model}
            </th>
            <th className="border border-gray-200 px-3 py-2 text-center text-gray-900 font-medium">
              {phone2.brand} {phone2.model}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={row.label}
              className={row.highlight ? 'bg-yellow-50' : index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
            >
              <td className="border border-gray-200 px-3 py-2 text-gray-500">{row.label}</td>
              <td className={`border border-gray-200 px-3 py-2 text-center ${row.highlight ? 'font-medium text-gray-900' : 'text-gray-700'}`}>
                {row.value1 || '-'}
              </td>
              <td className={`border border-gray-200 px-3 py-2 text-center ${row.highlight ? 'font-medium text-gray-900' : 'text-gray-700'}`}>
                {row.value2 || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
