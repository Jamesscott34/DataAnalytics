import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { fetchCurrentUser, loginUser, logoutUser, registerUser } from '../api/auth.js';
import { getAccessToken } from '../api/tokenStorage.js';

/**
 * @typedef {import('../types/auth.js').User} User
 */

const AuthContext = createContext(null);

/**
 * AuthProvider
 *
 * Supplies authentication state and actions to the component tree.
 *
 * @param {Object} props
 * @param {import('react').ReactNode} props.children
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const profile = await fetchCurrentUser();
      setUser(profile);
    } catch (err) {
      setUser(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(
    async (email, password) => {
      setError(null);
      await loginUser({ email, password });
      await loadUser();
    },
    [loadUser],
  );

  const register = useCallback(
    async (email, password, fullName) => {
      setError(null);
      await registerUser({ email, password, full_name: fullName });
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      error,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      reload: loadUser,
    }),
    [user, loading, error, login, register, logout, loadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * useAuth
 *
 * Access authentication state and actions.
 *
 * @returns {{
 *   user: User|null,
 *   loading: boolean,
 *   error: string|null,
 *   isAuthenticated: boolean,
 *   login: (email: string, password: string) => Promise<void>,
 *   register: (email: string, password: string, fullName?: string) => Promise<void>,
 *   logout: () => Promise<void>,
 *   reload: () => Promise<void>,
 * }}
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
