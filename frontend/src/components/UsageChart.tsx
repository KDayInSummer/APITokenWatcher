import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface DataPoint {
  time: string;
  tokens: number;
  cost: number;
}

export default function UsageChart({ data, type }: { data: DataPoint[]; type: 'tokens' | 'cost' }) {
  const color = type === 'tokens' ? '#60a5fa' : '#34d399';
  const key = type === 'tokens' ? 'tokens' : 'cost';

  return (
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id={`grad-${type}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#9ca3af' }} axisLine={{ stroke: '#4b5563' }} tickLine={{ stroke: '#4b5563' }} />
        <YAxis tick={{ fontSize: 9, fill: '#9ca3af' }} axisLine={{ stroke: '#4b5563' }} tickLine={{ stroke: '#4b5563' }} width={35} />
        <Tooltip
          contentStyle={{ borderRadius: 6, border: '1px solid #374151', backgroundColor: '#1f2937', color: '#e5e7eb', boxShadow: '0 4px 12px rgba(0,0,0,0.4)', fontSize: 11 }}
        />
        <Area
          type="monotone"
          dataKey={key}
          stroke={color}
          fillOpacity={1}
          fill={`url(#grad-${type})`}
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
