import { api } from '../api';
import { usePolling } from '../hooks/usePolling';

interface Record {
  id: number;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  timestamp: string;
  currency?: string;
}

function toChinaTime(utcStr: string): string {
  const d = new Date(utcStr);
  // 手动加8小时转为中国时间
  d.setHours(d.getHours() + 8);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  const s = String(d.getSeconds()).padStart(2, '0');
  return `${y}/${m}/${day} ${h}:${min}:${s}`;
}

export default function RecentRecords({ providerId, currency = 'CNY' }: { providerId?: number; currency?: string }) {
  const { data } = usePolling<{ total: number; records: Record[] }>(
    () => api.usage.records(providerId, 10, 0),
    10000,
    [providerId]
  );

  const records = data?.records || [];
  const sym = currency === 'CNY' ? '¥' : '$';

  return (
    <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
      <h3 className="text-xs font-semibold mb-2 text-gray-100">最近用量记录</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-left text-gray-400 border-b border-gray-700">
              <th className="pb-1.5 font-medium">时间</th>
              <th className="pb-1.5 font-medium">模型</th>
              <th className="pb-1.5 font-medium text-right">输入</th>
              <th className="pb-1.5 font-medium text-right">输出</th>
              <th className="pb-1.5 font-medium text-right">总量</th>
              <th className="pb-1.5 font-medium text-right">费用</th>
            </tr>
          </thead>
          <tbody>
            {records.length === 0 && (
              <tr>
                <td colSpan={6} className="py-6 text-center text-gray-500">暂无记录</td>
              </tr>
            )}
            {records.map((r) => (
              <tr key={r.id} className="border-b border-gray-700/50 last:border-0">
                <td className="py-2 text-gray-400">{toChinaTime(r.timestamp)}</td>
                <td className="py-2 font-medium text-gray-200">{r.model}</td>
                <td className="py-2 text-right text-gray-400">{r.prompt_tokens.toLocaleString()}</td>
                <td className="py-2 text-right text-gray-400">{r.completion_tokens.toLocaleString()}</td>
                <td className="py-2 text-right font-medium text-gray-200">{r.total_tokens.toLocaleString()}</td>
                <td className="py-2 text-right text-emerald-400 font-medium">{sym}{r.cost_usd.toFixed(6)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
