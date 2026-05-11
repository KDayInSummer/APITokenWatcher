import { usePolling } from '../hooks/usePolling';
import { api } from '../api';

interface Alert {
  id: number;
  alert_type: string;
  message: string;
  triggered_at: string;
  acknowledged: boolean;
}

export default function AlertBanner() {
  const { data, error } = usePolling<Alert[]>(() => api.alerts.list(), 30000);

  const unack = (data || []).filter((a) => !a.acknowledged);

  const ack = async (id: number) => {
    await api.alerts.ack(id);
  };

  if (unack.length === 0) return null;

  return (
    <div className="space-y-1.5 mb-2">
      {unack.map((a) => (
        <div
          key={a.id}
          className="bg-amber-900/30 border border-amber-700/50 rounded-lg px-3 py-2 flex items-center justify-between"
        >
          <div className="text-xs text-amber-300">
            <span className="font-semibold">告警:</span> {a.message}
          </div>
          <button
            onClick={() => ack(a.id)}
            className="text-[11px] px-2.5 py-1 bg-amber-800/40 text-amber-300 rounded hover:bg-amber-700/40"
          >
            确认
          </button>
        </div>
      ))}
    </div>
  );
}
