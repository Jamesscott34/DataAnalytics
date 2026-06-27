/**
 * EDA API calls.
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

/**
 * Run EDA on an uploaded file.
 *
 * @param {number} fileId
 * @param {{ forceRefresh?: boolean }} [options]
 */
export async function runEda(fileId, options = {}) {
  const response = await fetch(`${API_BASE_URL}/eda/${fileId}`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      force_refresh: options.forceRefresh ?? false,
      force_background: options.forceBackground ?? false,
    }),
  });
  const body = await response.json().catch(() => ({}));
  if (response.status === 202) {
    return body;
  }
  if (!response.ok) {
    throw new Error(body.message ?? body.detail ?? 'EDA analysis failed');
  }
  return body;
}

/**
 * Fetch cached EDA results.
 *
 * @param {number} fileId
 */
export async function getEda(fileId) {
  const response = await fetch(`${API_BASE_URL}/eda/${fileId}`, {
    headers: authHeaders(false),
  });
  if (response.status === 204) {
    return null;
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'EDA results not found');
  }
  return response.json();
}

/**
 * Fetch modelling suggestions from EDA.
 *
 * @param {number} fileId
 */
export async function getEdaSuggestions(fileId) {
  const response = await fetch(`${API_BASE_URL}/eda/${fileId}/suggestions`, {
    headers: authHeaders(false),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load EDA suggestions');
  }
  return response.json();
}
