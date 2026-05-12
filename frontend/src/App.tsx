import { useEffect, useState } from 'react';
import { api } from './api';
import Dashboard from './components/Dashboard';
import ConfigPanel from './components/ConfigPanel';
import AlertBanner from './components/AlertBanner';

interface Provider {
  id: number;
  name: string;
}

type Tab = 'dashboard' | 'config';
export type TimeRange = 'today' | 'week' | 'month' | 'all';

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<number | undefined>(undefined);
  const [timeRange, setTimeRange] = useState<TimeRange>('today');

  const loadProviders = async () => {
    const list = await api.providers.list();
    setProviders(list);
    if (list.length > 0 && selectedProvider === undefined) {
      setSelectedProvider(list[0].id);
    }
  };

  useEffect(() => {
    loadProviders();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-xs">
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-3 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-500 rounded flex items-center justify-center text-white font-bold text-[10px]">
              AT
            </div>
            <h1 className="text-sm font-bold text-gray-100">APITokenWatcher</h1>
          </div>
          <div className="flex items-center gap-3">
            {providers.length > 0 && (
              <select
                className="text-xs border border-gray-600 rounded px-2 py-1 bg-gray-700 text-gray-200"
                value={selectedProvider || ''}
                onChange={(e) => setSelectedProvider(e.target.value ? parseInt(e.target.value) : undefined)}
              >
                <option value="">全部平台</option>
                {providers.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            )}
            <nav className="flex gap-1">
              <button
                onClick={() => setTab('dashboard')}
                className={`px-3 py-1 text-xs rounded ${tab === 'dashboard' ? 'bg-blue-600/20 text-blue-400 font-medium' : 'text-gray-400 hover:bg-gray-700'}`}
              >
                仪表盘
              </button>
              <button
                onClick={() => setTab('config')}
                className={`px-3 py-1 text-xs rounded ${tab === 'config' ? 'bg-blue-600/20 text-blue-400 font-medium' : 'text-gray-400 hover:bg-gray-700'}`}
              >
                配置
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-3 py-3">
        {tab === 'dashboard' && (
          <>
            <AlertBanner />
            <Dashboard providerId={selectedProvider} timeRange={timeRange} onTimeRangeChange={setTimeRange} />
          </>
        )}
        {tab === 'config' && (
          <ConfigPanel onChange={loadProviders} />
        )}
      </main>
    </div>
  );
}
