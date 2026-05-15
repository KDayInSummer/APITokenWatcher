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

async function del(path: string) {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  providers: {
    list: () => get('/api/providers'),
    get: (id: number) => get(`/api/providers/${id}`),
    create: (data: any) => post('/api/providers', data),
    update: (id: number, data: any) => put(`/api/providers/${id}`, data),
    del: (id: number) => del(`/api/providers/${id}`),
    syncBalance: (id: number) => post(`/api/providers/${id}/sync-balance`),
  },
  usage: {
    summary: (providerId?: number, startTime?: number) =>
      get(`/api/usage/summary?${providerId ? `provider_id=${providerId}&` : ''}${startTime ? `start_time=${startTime}` : ''}`),
    trend: (providerId?: number, period = 'day', limit = 24, year?: number, month?: number) =>
      get(`/api/usage/trend?${providerId ? `provider_id=${providerId}&` : ''}period=${period}&limit=${limit}${year ? `&year=${year}` : ''}${month ? `&month=${month}` : ''}`),
    records: (providerId?: number, limit = 10, offset = 0, range = 'all') =>
      get(`/api/usage/records?${providerId ? `provider_id=${providerId}&` : ''}limit=${limit}&offset=${offset}&range=${range}`),
  },
  alerts: {
    list: () => get('/api/alerts'),
    ack: (id: number) => post(`/api/alerts/${id}/ack`),
    test: () => post('/api/alerts/test'),
  },
  modelPricings: {
    list: (providerId: number) => get(`/api/providers/${providerId}/models`),
    create: (providerId: number, data: any) => post(`/api/providers/${providerId}/models`, data),
    update: (providerId: number, modelId: number, data: any) => put(`/api/providers/${providerId}/models/${modelId}`, data),
    del: (providerId: number, modelId: number) => del(`/api/providers/${providerId}/models/${modelId}`),
  },
};
