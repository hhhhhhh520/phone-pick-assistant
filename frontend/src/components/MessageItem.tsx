import type { Message } from '../types';
import { PhoneCard } from './PhoneCard';
import { CompareTable } from './CompareTable';

interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const isCompare = message.isCompare ?? false;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] ${
          isUser
            ? 'bg-blue-500 text-white rounded-2xl rounded-br-md'
            : 'bg-white border border-gray-200 rounded-2xl rounded-bl-md'
        } px-4 py-3`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

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
