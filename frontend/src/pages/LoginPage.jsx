import { useNavigate } from 'react-router-dom';
import { LoginForm } from '../components/LoginForm.jsx';

/**
 * LoginPage
 *
 * Public login screen for existing users.
 */
export function LoginPage() {
  const navigate = useNavigate();

  return (
    <main className="auth-page">
      <header>
        <h1>Sign in</h1>
        <p>Access the analytics workspace</p>
      </header>
      <LoginForm onSuccess={() => navigate('/dashboard')} />
    </main>
  );
}
