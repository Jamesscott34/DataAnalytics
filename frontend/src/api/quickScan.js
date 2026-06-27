/**
 * Quick scan API calls.
 */

import { API_BASE_URL } from './client.js';
import { getAccessToken } from './tokenStorage.js';

function authHeaders(json = true) {
  const headers = { Accept: 'application/json' };
  if (json) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function runQuickScan(fileId) {
  const response = await fetch(`${API_BASE_URL}/files/${fileId}/quick-scan`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Quick scan failed');
  }
  return response.json();
}

export async function getLatestQuickScan(fileId) {
  const response = await fetch(`${API_BASE_URL}/files/${fileId}/quick-scan`, {
    headers: authHeaders(false),
  });
  if (response.status === 204) {
    return null;
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Quick scan report not found');
  }
  return response.json();
}
