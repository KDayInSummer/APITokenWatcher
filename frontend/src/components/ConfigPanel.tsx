import { useEffect, useState } from 'react';
import { api } from '../api';

interface Provider {
  id?: number;
  name: string;
  api_key: string;
  base_url: string;
  balance_currency: string;
  alert_threshold_cost: number;
  alert_threshold_balance: number;
  is_enabled: boolean;
  pricing_cache_hit_input: number;
  pricing_cache_miss_input: number;
  pricing_output: number;
}

export default function ConfigPanel({ onChange }: { onChange?: () => void }) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [editing, setEditing] = useState<Provider | null>(null);
  const [syncing, setSyncing] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const list = await api.providers.list();
    setProviders(list);
  };

  useEffect(() => {
    load();
  }, []);

  const [saveError, setSaveError] = useState<string | null>(null);

  const save = async () => {
    if (!editing) return;
    setSaving(true);
    setSaveError(null);
    const payload = { ...editing };
    delete (payload as any).created_at;
    delete (payload as any).updated_at;
    try {
      if (editing.id) {
        await api.providers.update(editing.id, payload);
      } else {
        await api.providers.create(payload);
      }
      setEditing(null);
      await load();
      onChange?.();
    } catch (e: any) {
      const msg = e?.message || '保存失败，请检查网络或稍后重试';
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: number) => {
    if (!confirm('确定删除此平台配置？')) return;
    await api.providers.del(id);
    await load();
    onChange?.();
  };

  const syncBalance = async (id: number) => {
    setSyncing(id);
    try {
      await api.providers.syncBalance(id);
      await load();
      onChange?.();
    } catch (e) {
      alert('余额同步失败，请检查 API Key 是否正确');
    }
    setSyncing(null);
  };

  const startEdit = (p?: Provider) => {
    setEditing(
      p || {
        name: 'deepseek',
        api_key: '',
        base_url: 'https://api.deepseek.com',
        balance_currency: 'CNY',
        alert_threshold_cost: 0,
        alert_threshold_balance: 0,
        is_enabled: true,
        pricing_cache_hit_input: 0.02,
        pricing_cache_miss_input: 1.0,
        pricing_output: 2.0,
      }
    );
  };

  const sym = (c: string) => c === 'CNY' ? '¥' : '$';

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold text-gray-100">平台配置</h2>
        <button
          onClick={() => startEdit()}
          className="px-3 py-1 bg-blue-600 text-white rounded text-[10px] hover:bg-blue-500"
        >
          + 新增平台
        </button>
      </div>

      {providers.map((p) => (
        <div key={p.id} className="bg-gray-800 rounded-lg p-2 border border-gray-700 flex justify-between items-center">
          <div>
            <div className="font-medium text-gray-100 text-xs">{p.name}</div>
            <div className="text-[10px] text-gray-500">
              定价: 缓存命中 {p.pricing_cache_hit_input} | 未命中 {p.pricing_cache_miss_input} | 输出 {p.pricing_output}
            </div>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => syncBalance(p.id!)}
              disabled={syncing === p.id}
              className="px-2 py-0.5 text-[10px] border border-emerald-700 text-emerald-400 rounded hover:bg-emerald-900/30 disabled:opacity-50"
            >
              {syncing === p.id ? '...' : '同步'}
            </button>
            <button onClick={() => startEdit(p)} className="px-2 py-0.5 text-[10px] border border-gray-600 text-gray-300 rounded hover:bg-gray-700">编辑</button>
            <button onClick={() => remove(p.id!)} className="px-2 py-0.5 text-[10px] border border-red-800 text-red-400 rounded hover:bg-red-900/30">删除</button>
          </div>
        </div>
      ))}

      {editing && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg shadow-lg w-full max-w-lg p-4 space-y-3 border border-gray-700 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xs font-semibold text-gray-100">{editing.id ? '编辑平台' : '新增平台'}</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] text-gray-400 mb-0.5">名称</label>
                <input
                  className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                  value={editing.name}
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[10px] text-gray-400 mb-0.5">API Key</label>
                <input
                  className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                  value={editing.api_key}
                  onChange={(e) => setEditing({ ...editing, api_key: e.target.value })}
                />
              </div>
              <div className="col-span-2">
                <label className="block text-[10px] text-gray-400 mb-0.5">Base URL</label>
                <input
                  className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                  value={editing.base_url}
                  onChange={(e) => setEditing({ ...editing, base_url: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[10px] text-gray-400 mb-0.5">币种</label>
                <select
                  className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                  value={editing.balance_currency}
                  onChange={(e) => setEditing({ ...editing, balance_currency: e.target.value })}
                >
                  <option value="CNY">CNY</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] text-gray-400 mb-0.5">费用阈值</label>
                <input
                  type="number"
                  step="0.01"
                  className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                  value={editing.alert_threshold_cost}
                  onChange={(e) => setEditing({ ...editing, alert_threshold_cost: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="block text-[10px] text-gray-400 mb-0.5">余额阈值</label>
                <input
                  type="number"
                  step="0.01"
                  className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                  value={editing.alert_threshold_balance}
                  onChange={(e) => setEditing({ ...editing, alert_threshold_balance: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            {/* 模型定价配置 */}
            <div className="pt-2 border-t border-gray-700">
              <div className="text-[10px] text-gray-400 mb-2">模型定价（每百万 token，单位：{editing.balance_currency}）</div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-[10px] text-gray-400 mb-0.5">输入（缓存命中）</label>
                  <input
                    type="number"
                    step="0.001"
                    className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                    value={editing.pricing_cache_hit_input}
                    onChange={(e) => setEditing({ ...editing, pricing_cache_hit_input: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-400 mb-0.5">输入（缓存未命中）</label>
                  <input
                    type="number"
                    step="0.01"
                    className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                    value={editing.pricing_cache_miss_input}
                    onChange={(e) => setEditing({ ...editing, pricing_cache_miss_input: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-gray-400 mb-0.5">输出</label>
                  <input
                    type="number"
                    step="0.01"
                    className="w-full border border-gray-600 rounded px-2 py-1 text-xs bg-gray-700 text-gray-200 focus:outline-none focus:border-blue-500"
                    value={editing.pricing_output}
                    onChange={(e) => setEditing({ ...editing, pricing_output: parseFloat(e.target.value) || 0 })}
                  />
                </div>
              </div>
            </div>

            {saveError && (
              <div className="text-[10px] text-red-400 bg-red-900/20 border border-red-800 rounded px-2 py-1">
                {saveError}
              </div>
            )}
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => { setEditing(null); setSaveError(null); }} className="px-3 py-1 text-[10px] border border-gray-600 text-gray-300 rounded hover:bg-gray-700">取消</button>
              <button onClick={save} disabled={saving} className="px-3 py-1 text-[10px] bg-blue-600 text-white rounded hover:bg-blue-500 disabled:opacity-50">
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
