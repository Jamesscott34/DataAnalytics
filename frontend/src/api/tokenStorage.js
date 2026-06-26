/**
 * Token storage keys in localStorage.
 */
const ACCESS_TOKEN_KEY = 'psal_access_token';
const REFRESH_TOKEN_KEY = 'psal_refresh_token';

/**
 * Read the stored access token.
 *
 * @returns {string|null}
 */
export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Persist access and refresh tokens from login or refresh.
 *
 * @param {import('../types/auth.js').TokenResponse} tokens
 */
export function setTokens(tokens) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

/**
 * Remove stored authentication tokens.
 */
export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Read the stored refresh token.
 *
 * @returns {string|null}
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}
