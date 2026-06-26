/**
 * HTTP client for the backend API.
 *
 * All fetch calls must go through this module — not directly from components.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

/**
 * Parse a standard API error body.
 *
 * @param {Response} response - Fetch response object.
 * @returns {Promise<Error>} Error with message from API.
 */
async function parseApiError(response) {
  let message = response.statusText;
  try {
    const body = await response.json();
    message = body.message ?? body.detail ?? message;
  } catch {
    // Non-JSON error bodies fall back to status text.
  }
  return new Error(message);
}

/**
 * Perform an authenticated JSON request against the API.
 *
 * @param {string} path - Path relative to API base (e.g. `/health`).
 * @param {RequestInit} [options] - Fetch options.
 * @returns {Promise<unknown>} Parsed JSON response.
 */
export async function apiRequest(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const headers = {
    Accept: 'application/json',
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    throw await parseApiError(response);
  }

  return response.json();
}

export { API_BASE_URL };
