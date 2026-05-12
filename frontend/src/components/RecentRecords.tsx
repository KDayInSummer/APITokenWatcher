import { useState, useEffect } from 'react';
import { api } from '../api';
import { usePolling } from '../hooks/usePolling';
import type { TimeRange } from '../App';

interface Record {
  id: number;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  timestamp: string;
}

function toChinaTime(utcStr: string): string {
  const d = new Date(utcStr);
  d.setHours(d.getHours() + 8);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  const s = String(d.getSeconds()).padStart(2, '0');
  return `${y}/${m}/${day} ${h}:${min}:${s}`;
}

export default function RecentRecords({ providerId, currency = 'CNY', timeRange }: { providerId?: number; currency?: string; timeRange: TimeRange }) {
  const [page, setPage] = useState(0);
  const limit = 10;

  useEffect(() => {
    setPage(0);
  }, [timeRange, providerId]);

  const { data } = usePolling<{ total: number; records: Record[] }>(
    () => api.usage.records(providerId, limit, page * limit, timeRange),
    10000,
    [providerId, timeRange, page]
  );

  const records = data?.records || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / limit);
  const sym = currency === 'CNY' ? '¥' : '$';

  return (
    <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-gray-100">最近用量记录</h3>
      </div>
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
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-700">
          <span className="text-[10px] text-gray-500">共 {total} 条</span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-2 py-0.5 text-[10px] border border-gray-600 text-gray-300 rounded hover:bg-gray-700 disabled:opacity-40"
            >
              上一页
            </button>
            <span className="px-2 py-0.5 text-[10px] text-gray-400">{page + 1}/{totalPages}</span>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="px-2 py-0.5 text-[10px] border border-gray-600 text-gray-300 rounded hover:bg-gray-700 disabled:opacity-40"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
