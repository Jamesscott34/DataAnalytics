/**
 * Upload API calls.
 */

import { API_BASE_URL } from './client.js';
import { getAccessToken } from './tokenStorage.js';

/**
 * List recent uploads for the current user.
 *
 * @param {number} [limit]
 * @returns {Promise<Object>}
 */
export async function listUploads(limit = 20) {
  const headers = { Accept: 'application/json' };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const params = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/uploads?${params.toString()}`, {
    headers,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load uploads');
  }
  return response.json();
}

/**
 * Raised when an upload matches an existing file hash.
 */
export class DuplicateUploadError extends Error {
  /**
   * @param {string} message - API error message.
   * @param {Object} payload - Structured duplicate response body.
   */
  constructor(message, payload) {
    super(message);
    this.name = 'DuplicateUploadError';
    this.payload = payload;
  }
}

/**
 * Upload a CSV file to the backend.
 *
 * @param {File} file - CSV file selected by the user.
 * @param {{ clientSha256?: string, duplicateAction?: string }} [options]
 * @returns {Promise<Object>} Upload response metadata.
 */
export async function uploadCsv(file, options = {}) {
  const formData = new FormData();
  formData.append('file', file);
  if (options.clientSha256) {
    formData.append('client_sha256', options.clientSha256);
  }
  if (options.duplicateAction) {
    formData.append('duplicate_action', options.duplicateAction);
  }

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
    if (response.status === 409 && body.error === 'duplicate_upload') {
      throw new DuplicateUploadError(body.message ?? 'Duplicate file detected', body);
    }
    throw new Error(body.message ?? body.detail ?? 'Upload failed');
  }

  return response.json();
}

/**
 * Delete an uploaded CSV file by ID.
 *
 * @param {number} fileId - Uploaded file identifier.
 * @returns {Promise<Object>} Delete confirmation message.
 */
export async function deleteUpload(fileId) {
  const headers = { Accept: 'application/json' };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/uploads/${fileId}`, {
    method: 'DELETE',
    headers,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Delete failed');
  }

  return response.json();
}

/**
 * Fetch version history for an uploaded file.
 *
 * @param {number} fileId
 * @returns {Promise<Object>}
 */
export async function getFileVersions(fileId) {
  const headers = { Accept: 'application/json' };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/uploads/${fileId}/versions`, {
    headers,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to load versions');
  }
  return response.json();
}

/**
 * Compare two versions for the same uploaded file.
 *
 * @param {number} fileId
 * @param {number} versionA
 * @param {number} versionB
 * @returns {Promise<Object>}
 */
export async function compareFileVersions(fileId, versionA, versionB) {
  const headers = { Accept: 'application/json' };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const params = new URLSearchParams({
    version_a: String(versionA),
    version_b: String(versionB),
  });
  const response = await fetch(
    `${API_BASE_URL}/uploads/${fileId}/versions/compare?${params.toString()}`,
    { headers },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message ?? body.detail ?? 'Failed to compare versions');
  }
  return response.json();
}
