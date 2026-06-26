/**
 * Upload API calls.
 */

import { API_BASE_URL } from './client.js';
import { getAccessToken } from './tokenStorage.js';

/**
 * Upload a CSV file to the backend.
 *
 * @param {File} file - CSV file selected by the user.
 * @returns {Promise<Object>} Upload response metadata.
 */
export async function uploadCsv(file) {
  const formData = new FormData();
  formData.append('file', file);

  const headers = { Accept: 'application/json' };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/uploads`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Upload failed');
  }

  return response.json();
}
