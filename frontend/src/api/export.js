/**
 * Export API calls.
 */

import { API_BASE_URL, apiRequest } from './client.js';
import { getAccessToken } from './tokenStorage.js';

function authHeaders(extra = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...extra,
  };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Save a quick-scan report as Markdown in scan_results/.
 *
 * @param {string} reportId
 * @returns {Promise<{ saved: object, download_filename: string }>}
 */
export async function saveMarkdownReport(reportId) {
  return apiRequest('/export/markdown', {
    method: 'POST',
    headers: authHeaders({ Accept: 'application/json' }),
    body: JSON.stringify({ report_id: reportId }),
  });
}

/**
 * Save a quick-scan report as PDF in scan_results/.
 *
 * @param {string} reportId
 * @returns {Promise<{ saved: object, download_filename: string }>}
 */
export async function savePdfReport(reportId) {
  return apiRequest('/export/pdf', {
    method: 'POST',
    headers: authHeaders({ Accept: 'application/json' }),
    body: JSON.stringify({ report_id: reportId }),
  });
}

/**
 * List saved scan result files.
 *
 * @returns {Promise<{ items: object[], total: number }>}
 */
export function listScanResults() {
  return apiRequest('/export/scan-results');
}

/**
 * Build an authenticated URL for viewing a saved scan result.
 *
 * @param {string} filename
 * @returns {string}
 */
export function getScanResultViewPath(filename) {
  return `/scan-results/view/${encodeURIComponent(filename)}`;
}

/**
 * Fetch a saved scan result for inline viewing.
 *
 * @param {string} filename
 * @returns {Promise<{ contentType: string, blob: Blob, text?: string }>}
 */
export async function fetchScanResult(filename) {
  const response = await fetch(
    `${API_BASE_URL}/export/scan-results/${encodeURIComponent(filename)}`,
    {
      headers: authHeaders({ Accept: '*/*' }),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load scan result');
  }
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('text/markdown') || filename.toLowerCase().endsWith('.md')) {
    const text = await response.text();
    return { contentType, blob: new Blob([text], { type: contentType }), text };
  }
  const blob = await response.blob();
  return { contentType, blob };
}
