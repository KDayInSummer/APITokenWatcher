import { useRef, useState, useEffect } from 'react';
import { api } from '../api';
import { usePolling } from '../hooks/usePolling';
import UsageChart from './UsageChart';
import RecentRecords from './RecentRecords';
import type { TimeRange } from '../App';

interface Summary {
  today_tokens: number;
  today_completion_tokens: number;
  today_cost: number;
  today_calls: number;
  today_cache_hit_tokens: number;
  today_cache_miss_tokens: number;
  week_tokens: number;
  week_completion_tokens: number;
  week_cost: number;
  week_calls: number;
  week_cache_hit_tokens: number;
  week_cache_miss_tokens: number;
  month_tokens: number;
  month_completion_tokens: number;
  month_cost: number;
  month_calls: number;
  month_cache_hit_tokens: number;
  month_cache_miss_tokens: number;
  all_tokens: number;
  all_completion_tokens: number;
  all_cost: number;
  all_calls: number;
  all_cache_hit_tokens: number;
  all_cache_miss_tokens: number;
  remaining_balance: number;
  real_time_cost: number;
  currency: string;
}

const rangeLabels: Record<TimeRange, string> = {
  today: '今日',
  week: '本周',
  month: '本月',
  all: '累计',
};

type ChartMode = 'week' | 'month' | 'year';

function TooltipIcon({ text }: { text: string }) {
  return (
    <div className="relative group">
      <svg className="w-3 h-3 text-gray-500 cursor-help" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
      </svg>
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900 border border-gray-600 rounded text-[10px] text-gray-300 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
        {text}
      </div>
    </div>
  );
}

export default function Dashboard({ providerId, timeRange, onTimeRangeChange }: { providerId?: number; timeRange: TimeRange; onTimeRangeChange: (r: TimeRange) => void }) {
  const appStartTime = useRef(Date.now() / 1000);
  const [chartMode, setChartMode] = useState<ChartMode>('week');
  const now = new Date();
  const [chartYear, setChartYear] = useState(now.getFullYear());
  const [chartMonth, setChartMonth] = useState(now.getMonth() + 1);
  const [showMonthPicker, setShowMonthPicker] = useState(false);
  const [showYearPicker, setShowYearPicker] = useState(false);
  const monthPickerRef = useRef<HTMLDivElement>(null);
  const yearPickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (monthPickerRef.current && !monthPickerRef.current.contains(e.target as Node)) {
        setShowMonthPicker(false);
      }
      if (yearPickerRef.current && !yearPickerRef.current.contains(e.target as Node)) {
        setShowYearPicker(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const { data: summary } = usePolling<Summary>(
    () => api.usage.summary(providerId, appStartTime.current),
    10000,
    [providerId]
  );

  const trendLimit = chartMode === 'week' ? 7 : chartMode === 'month' ? 31 : 12;
  const { data: trend } = usePolling(
    () => api.usage.trend(providerId, chartMode, trendLimit, chartYear, chartMonth),
    30000,
    [providerId, chartMode, chartYear, chartMonth]
  );

  if (!summary) {
    return <div className="p-4 text-gray-400 text-sm">加载中...</div>;
  }

  const sym = summary.currency === 'CNY' ? '¥' : '$';
  const label = rangeLabels[timeRange];

  const cacheHit = summary[`${timeRange}_cache_hit_tokens` as keyof Summary] as number;
  const cacheMiss = summary[`${timeRange}_cache_miss_tokens` as keyof Summary] as number;
  const tokens = summary[`${timeRange}_tokens` as keyof Summary] as number;
  const completionTokens = summary[`${timeRange}_completion_tokens` as keyof Summary] as number;
  const cost = summary[`${timeRange}_cost` as keyof Summary] as number;
  const calls = summary[`${timeRange}_calls` as keyof Summary] as number;

  const hitRate = cacheHit + cacheMiss > 0
    ? (cacheHit / (cacheHit + cacheMiss) * 100).toFixed(1)
    : '-';

  const realTimeBalance = summary.remaining_balance - summary.real_time_cost;

  const trendTitle = chartMode === 'week'
    ? 'Token/费用 趋势 (近7天)'
    : chartMode === 'month'
    ? `Token/费用 趋势 (${chartYear}年${chartMonth}月)`
    : `Token/费用 趋势 (${chartYear}年)`;

  const currentYear = now.getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  return (
    <div className="space-y-3">
      {/* Point 4: 数据显示范围 - moved from header to above cards */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-400">数据显示范围</span>
        <select
          className="text-xs border border-gray-600 rounded px-2 py-1 bg-gray-700 text-gray-200"
          value={timeRange}
          onChange={(e) => onTimeRangeChange(e.target.value as TimeRange)}
        >
          <option value="today">今日</option>
          <option value="week">本周</option>
          <option value="month">本月</option>
          <option value="all">累计</option>
        </select>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 rounded-full bg-cyan-500" />
            <div className="text-xs text-gray-400">{label}输入缓存命中Token</div>
          </div>
          <div className="text-xl font-bold text-cyan-400">{cacheHit.toLocaleString()}</div>
          <div className="text-[10px] text-gray-500 mt-0.5">命中率 {hitRate}%</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 rounded-full bg-amber-500" />
            <div className="text-xs text-gray-400">{label}输入缓存未命中Token</div>
          </div>
          <div className="text-xl font-bold text-amber-400">{cacheMiss.toLocaleString()}</div>
          <div className="text-[10px] text-gray-500 mt-0.5">
            省 {sym}{(cacheMiss * 0.9 / 1_000_000).toFixed(4)}
            <span className="text-gray-600"> (按 0.9/百万差价计)</span>
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 rounded-full bg-teal-500" />
            <div className="text-xs text-gray-400">{label}输出Token</div>
          </div>
          <div className="text-xl font-bold text-teal-400">{completionTokens.toLocaleString()}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            <div className="text-xs text-gray-400">{label}消耗总Token</div>
          </div>
          <div className="text-xl font-bold text-blue-400">{tokens.toLocaleString()}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 rounded-full bg-indigo-500" />
            <div className="text-xs text-gray-400">{label}请求次数</div>
          </div>
          <div className="text-xl font-bold text-indigo-400">{calls.toLocaleString()}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <div className="text-xs text-gray-400">{label}消费金额</div>
          </div>
          <div className="text-xl font-bold text-emerald-400">{sym}{cost.toFixed(4)}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 rounded-full bg-pink-500" />
            <div className="text-xs text-gray-400">实时计算剩余金额</div>
            <TooltipIcon text="根据每次请求实时计算剩余金额" />
          </div>
          <div className="text-xl font-bold text-pink-400">{sym}{realTimeBalance.toFixed(2)}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 rounded-full bg-violet-500" />
            <div className="text-xs text-gray-400">剩余金额</div>
            <TooltipIcon text="每5分钟从平台 API 同步真实余额" />
          </div>
          <div className="text-xl font-bold text-violet-400">{sym}{summary.remaining_balance.toFixed(2)}</div>
        </div>
      </div>

      <RecentRecords providerId={providerId} currency={summary.currency} timeRange={timeRange} />

      {/* Point 5: 折线图 - title, then selector line, then charts */}
      <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
        <h3 className="text-xs font-semibold text-gray-100 mb-2">{trendTitle}</h3>
        {/* 折线图显示范围 selector - separate line, same style as 数据显示范围 */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-gray-400">折线图显示范围</span>
          <button
            onClick={() => setChartMode('week')}
            className={`px-2 py-0.5 text-[10px] rounded ${chartMode === 'week' ? 'bg-blue-600/30 text-blue-400' : 'text-gray-400 hover:bg-gray-700'}`}
          >
            周
          </button>
          <div className="relative" ref={monthPickerRef}>
            <button
              onClick={() => { setChartMode('month'); setShowMonthPicker(!showMonthPicker); setShowYearPicker(false); }}
              className={`px-2 py-0.5 text-[10px] rounded ${chartMode === 'month' ? 'bg-blue-600/30 text-blue-400' : 'text-gray-400 hover:bg-gray-700'}`}
            >
              月
            </button>
            {showMonthPicker && chartMode === 'month' && (
              <div className="absolute top-full left-0 mt-1 bg-gray-900 border border-gray-600 rounded p-2 z-50 shadow-lg">
                <div className="flex gap-1 mb-1">
                  <select
                    value={chartYear}
                    onChange={(e) => setChartYear(Number(e.target.value))}
                    className="text-[10px] bg-gray-700 border border-gray-600 rounded px-1 py-0.5 text-gray-200"
                  >
                    {years.map(y => <option key={y} value={y}>{y}年</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-4 gap-1">
                  {months.map(m => (
                    <button
                      key={m}
                      onClick={() => { setChartMonth(m); setShowMonthPicker(false); }}
                      className={`px-1.5 py-0.5 text-[10px] rounded ${chartMonth === m ? 'bg-blue-600/30 text-blue-400' : 'text-gray-400 hover:bg-gray-700'}`}
                    >
                      {m}月
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="relative" ref={yearPickerRef}>
            <button
              onClick={() => { setChartMode('year'); setShowYearPicker(!showYearPicker); setShowMonthPicker(false); }}
              className={`px-2 py-0.5 text-[10px] rounded ${chartMode === 'year' ? 'bg-blue-600/30 text-blue-400' : 'text-gray-400 hover:bg-gray-700'}`}
            >
              年
            </button>
            {showYearPicker && chartMode === 'year' && (
              <div className="absolute top-full left-0 mt-1 bg-gray-900 border border-gray-600 rounded p-2 z-50 shadow-lg min-w-[120px]">
                <div className="grid grid-cols-3 gap-1">
                  {years.map(y => (
                    <button
                      key={y}
                      onClick={() => { setChartYear(y); setShowYearPicker(false); }}
                      className={`px-2 py-0.5 text-[10px] rounded ${chartYear === y ? 'bg-blue-600/30 text-blue-400' : 'text-gray-400 hover:bg-gray-700'}`}
                    >
                      {y}年
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-2">
          <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
            <UsageChart data={trend || []} type="tokens" />
          </div>
          <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
            <UsageChart data={trend || []} type="cost" />
          </div>
        </div>
      </div>
    </div>
  );
}
