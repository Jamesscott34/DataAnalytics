/**
 * Authentication-related type definitions.
 *
 * @typedef {'admin' | 'analyst' | 'viewer'} UserRole
 */

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} email
 * @property {string|null} full_name
 * @property {UserRole} role
 * @property {boolean} is_active
 */

/**
 * @typedef {Object} TokenResponse
 * @property {string} access_token
 * @property {string} refresh_token
 * @property {string} token_type
 * @property {number} expires_in
 */

/**
 * @typedef {TokenResponse & { user: User }} LoginResponse
 */

export {};
