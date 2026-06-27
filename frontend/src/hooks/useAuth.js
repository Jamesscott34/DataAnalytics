import { useContext } from 'react';
import { AuthContext } from '../context/authContext.js';

/**
 * useAuth
 *
 * Access authentication state and actions.
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
