import { api } from '../api';
import { usePolling } from '../hooks/usePolling';
import UsageChart from './UsageChart';
import RecentRecords from './RecentRecords';

interface Summary {
  today_tokens: number;
  today_cost: number;
  week_cost: number;
  month_cost: number;
  total_cost: number;
  today_calls: number;
  remaining_balance: number;
  currency: string;
}

export default function Dashboard({ providerId }: { providerId?: number }) {
  const { data: summary } = usePolling<Summary>(() => api.usage.summary(providerId), 10000, [providerId]);
  const { data: trend } = usePolling(() => api.usage.trend(providerId, 'day', 7), 30000, [providerId]);

  if (!summary) {
    return <div className="p-4 text-gray-400 text-sm">加载中...</div>;
  }

  const sym = summary.currency === 'CNY' ? '¥' : '$';
  const cards = [
    { label: '今日Token', value: summary.today_tokens.toLocaleString(), color: 'bg-blue-500' },
    { label: '今日费用', value: `${sym}${summary.today_cost.toFixed(4)}`, color: 'bg-emerald-500' },
    { label: '本月费用', value: `${sym}${summary.month_cost.toFixed(4)}`, color: 'bg-orange-500' },
    { label: '今日调用', value: summary.today_calls.toLocaleString(), color: 'bg-indigo-500' },
    { label: '累计费用', value: `${sym}${summary.total_cost.toFixed(4)}`, color: 'bg-rose-500' },
    { label: '剩余额度', value: `${sym}${summary.remaining_balance.toFixed(2)}`, color: 'bg-cyan-500' },
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-2">
        {cards.map((c) => (
          <div key={c.label} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
            <div className="flex items-center gap-1.5 mb-1">
              <div className={`w-2 h-2 rounded-full ${c.color}`} />
              <div className="text-xs text-gray-400">{c.label}</div>
            </div>
            <div className="text-xl font-bold text-gray-100">{c.value}</div>
          </div>
        ))}
      </div>

      <RecentRecords providerId={providerId} currency={summary.currency} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <h3 className="text-xs font-semibold mb-2 text-gray-100">Token 趋势 (近7天)</h3>
          <UsageChart data={trend || []} type="tokens" />
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <h3 className="text-xs font-semibold mb-2 text-gray-100">费用趋势 (近7天)</h3>
          <UsageChart data={trend || []} type="cost" />
        </div>
      </div>
    </div>
  );
}
