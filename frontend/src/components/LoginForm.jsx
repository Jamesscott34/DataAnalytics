import { useState } from 'react';
import { useLogin } from '../hooks/useLogin.js';

/**
 * LoginForm
 *
 * Email/password form that authenticates against the backend API.
 *
 * @param {Object} props
 * @param {() => void} [props.onSuccess] - Called after a successful login.
 */
export function LoginForm({ onSuccess }) {
  const { submit, loading, error } = useLogin();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await submit(email, password);
      onSuccess?.();
    } catch {
      // Error state handled in useLogin.
    }
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Sign in form" noValidate>
      <label htmlFor="login-email">Email</label>
      <input
        id="login-email"
        type="email"
        autoComplete="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        aria-label="Email address"
      />

      <label htmlFor="login-password">Password</label>
      <input
        id="login-password"
        type="password"
        autoComplete="current-password"
        required
        minLength={8}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        aria-label="Password"
      />

      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}

      <button type="submit" disabled={loading} aria-busy={loading}>
        {loading ? 'Signing in…' : 'Sign in'}
      </button>
    </form>
  );
}
