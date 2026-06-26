import { useState } from 'react';
import { useAuth } from './useAuth.jsx';

/**
 * useLogin
 *
 * Form state helper for login submission.
 *
 * @returns {{ submit: Function, loading: boolean, error: string|null }}
 */
export function useLogin() {
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { submit, loading, error };
}
