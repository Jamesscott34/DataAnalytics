import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchCurrentUser, loginUser, logoutUser, registerUser } from '../api/auth.js';
import { getAccessToken } from '../api/tokenStorage.js';
import { AuthContext } from './authContext.js';

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

  const loadUser = useCallback(async (options = {}) => {
    const { silent = false } = options;
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    if (!silent) {
      setLoading(true);
    }
    setError(null);
    try {
      const profile = await fetchCurrentUser();
      setUser(profile);
    } catch (err) {
      setUser(null);
      if (getAccessToken()) {
        setError(err.message);
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(async (email, password) => {
    setError(null);
    const response = await loginUser({ email, password });
    setUser(response.user);
    setLoading(false);
  }, []);

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
