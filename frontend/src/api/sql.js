/**
 * SQL analysis API calls.
 */

import { API_BASE_URL } from './client.js';
import { getAccessToken } from './tokenStorage.js';

function authHeaders() {
  const headers = { Accept: 'application/json', 'Content-Type': 'application/json' };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Import CSV rows for SQL analysis.
 *
 * @param {number} fileId
 * @param {{ maxRows?: number }} [options]
 * @returns {Promise<Object>}
 */
export async function importSqlRows(fileId, options = {}) {
  const response = await fetch(`${API_BASE_URL}/sql/${fileId}/import`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      max_rows: options.maxRows ?? null,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'SQL import failed');
  }
  return response.json();
}

/**
 * Run a read-only SQL query.
 *
 * @param {number} fileId
 * @param {string} query
 * @returns {Promise<Object>}
 */
export async function runSqlQuery(fileId, query) {
  const response = await fetch(`${API_BASE_URL}/sql/${fileId}/query`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ query }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'SQL query failed');
  }
  return response.json();
}

/**
 * Fetch SQL presets for a file.
 *
 * @param {number} fileId
 * @returns {Promise<Object>}
 */
export async function getSqlPresets(fileId) {
  const response = await fetch(`${API_BASE_URL}/sql/${fileId}/presets`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load SQL presets');
  }
  return response.json();
}

/**
 * Run a built-in SQL preset.
 *
 * @param {number} fileId
 * @param {string} presetId
 * @returns {Promise<Object>}
 */
export async function runSqlPreset(fileId, presetId) {
  const response = await fetch(
    `${API_BASE_URL}/sql/${fileId}/presets/${presetId}/run`,
    {
      method: 'POST',
      headers: authHeaders(),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Preset query failed');
  }
  return response.json();
}
