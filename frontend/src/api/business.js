import { API_BASE_URL } from './client.js';
import { getAccessToken } from './tokenStorage.js';

function authHeaders() {
  const headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function analyzeBusiness(fileId, payload) {
  const response = await fetch(`${API_BASE_URL}/business/${fileId}/analyze`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      date_column: payload.dateColumn || null,
      revenue_column: payload.revenueColumn || null,
      cost_column: payload.costColumn || null,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Business analytics failed');
  }
  return response.json();
}
