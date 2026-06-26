/**
 * Authentication API calls.
 */

import { apiRequest } from './client.js';
import { clearTokens, getRefreshToken, setTokens } from './tokenStorage.js';

/**
 * Register a new user account.
 *
 * @param {{ email: string, password: string, full_name?: string }} payload
 * @returns {Promise<import('../types/auth.js').User>}
 */
export async function registerUser(payload) {
  return apiRequest('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

/**
 * Log in and store returned tokens.
 *
 * @param {{ email: string, password: string }} payload
 * @returns {Promise<import('../types/auth.js').TokenResponse>}
 */
export async function loginUser(payload) {
  const tokens = await apiRequest('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  setTokens(tokens);
  return tokens;
}

/**
 * Fetch the current authenticated user profile.
 *
 * @returns {Promise<import('../types/auth.js').User>}
 */
export async function fetchCurrentUser() {
  return apiRequest('/auth/me');
}

/**
 * Log out locally and revoke refresh token on the server when possible.
 *
 * @returns {Promise<void>}
 */
export async function logoutUser() {
  const refreshToken = getRefreshToken();
  try {
    await apiRequest('/auth/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } finally {
    clearTokens();
  }
}
