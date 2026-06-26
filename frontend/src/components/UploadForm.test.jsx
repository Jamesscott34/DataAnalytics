import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { UploadForm } from './UploadForm.jsx';
import * as uploadsApi from '../api/uploads.js';

describe('UploadForm', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the upload form', () => {
    render(<UploadForm />);
    expect(screen.getByLabelText('CSV file')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Upload' })).toBeInTheDocument();
  });

  it('rejects non-csv files client-side', async () => {
    const user = userEvent.setup();
    render(<UploadForm />);

    const file = new File(['hello'], 'notes.txt', { type: 'text/csv' });
    await user.upload(screen.getByLabelText('CSV file'), file);
    await user.click(screen.getByRole('button', { name: 'Upload' }));

    expect(screen.getByRole('alert')).toHaveTextContent(/only .csv/i);
  });

  it('displays upload metadata after successful CSV upload', async () => {
    const user = userEvent.setup();
    vi.spyOn(uploadsApi, 'uploadCsv').mockResolvedValue({
      file_id: 1,
      filename: 'data.csv',
      file_hash: 'a'.repeat(64),
      size_bytes: 18,
      row_count: 2,
      column_count: 2,
      is_duplicate: false,
      version_number: 1,
    });

    render(<UploadForm />);
    const file = new File(['a,b\n1,2\n'], 'data.csv', { type: 'text/csv' });
    await user.upload(screen.getByLabelText('CSV file'), file);
    await user.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() => {
      expect(screen.getByText(/uploaded: data.csv/i)).toBeInTheDocument();
    });
  });
});
