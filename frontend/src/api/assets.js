/**
 * Temp assets API calls.
 */

import { API_BASE_URL } from './client.js';
import { DuplicateUploadError } from './uploads.js';
import { getAccessToken } from './tokenStorage.js';

/**
 * List CSV files available in temp_assets.
 *
 * @returns {Promise<{ files: Array<{ name: string, size_bytes: number, safe: boolean }> }>}
 */
export async function listAssets() {
  const headers = { Accept: 'application/json' };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/assets`, { headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load assets');
  }
  return response.json();
}

/**
 * Import a temp asset through the secure upload pipeline.
 *
 * @param {string} filename - Asset filename from temp_assets.
 * @param {{ duplicateAction?: string }} [options]
 * @returns {Promise<Object>} Upload response metadata.
 */
export async function selectAsset(filename, options = {}) {
  const headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/assets/select`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      filename,
      duplicate_action: options.duplicateAction ?? null,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (response.status === 409 && body.error === 'duplicate_upload') {
      throw new DuplicateUploadError(body.message ?? 'Duplicate file detected', body);
    }
    throw new Error(body.message ?? body.detail ?? 'Asset selection failed');
  }

  return response.json();
}
