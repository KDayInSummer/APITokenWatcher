const BASE = '';

async function get(path: string) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function post(path: string, body?: object) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function put(path: string, body: object) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  providers: {
    list: () => get('/api/providers'),
    get: (id: number) => get(`/api/providers/${id}`),
    create: (data: any) => post('/api/providers', data),
    update: (id: number, data: any) => put(`/api/providers/${id}`, data),
    del: (id: number) => fetch(`${BASE}/api/providers/${id}`, { method: 'DELETE' }).then(r => r.json()),
    syncBalance: (id: number) => post(`/api/providers/${id}/sync-balance`),
  },
  usage: {
    summary: (providerId?: number) => get(`/api/usage/summary?${providerId ? `provider_id=${providerId}` : ''}`),
    trend: (providerId?: number, period = 'day', limit = 24) =>
      get(`/api/usage/trend?${providerId ? `provider_id=${providerId}&` : ''}period=${period}&limit=${limit}`),
    records: (providerId?: number, limit = 20, offset = 0) =>
      get(`/api/usage/records?${providerId ? `provider_id=${providerId}&` : ''}limit=${limit}&offset=${offset}`),
  },
  alerts: {
    list: () => get('/api/alerts'),
    ack: (id: number) => post(`/api/alerts/${id}/ack`),
    test: () => post('/api/alerts/test'),
  },
};
