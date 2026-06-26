import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, beforeEach } from 'vitest';
import { ProtectedRoute } from './ProtectedRoute.jsx';
import { AuthProvider } from '../hooks/useAuth.jsx';
import { LoginPage } from '../pages/LoginPage.jsx';

describe('ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('redirects to login when no token is present', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <p>Secret dashboard</p>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    });
    expect(screen.queryByText('Secret dashboard')).not.toBeInTheDocument();
  });
});
