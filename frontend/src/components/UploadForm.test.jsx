import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { UploadForm } from './UploadForm.jsx';
import * as uploadsApi from '../api/uploads.js';
import * as hashUtils from '../utils/hash.js';

function renderUploadForm() {
  return render(
    <MemoryRouter>
      <UploadForm />
    </MemoryRouter>,
  );
}

describe('UploadForm', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the upload form', () => {
    renderUploadForm();
    expect(screen.getByLabelText('CSV file')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Upload' })).toBeInTheDocument();
  });

  it('rejects non-csv files client-side', async () => {
    const user = userEvent.setup();
    renderUploadForm();

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
      scan_result: {
        status: 'safe',
        issues: [],
        risk_score: 0,
        recommended_action: 'File passed scanner checks and can be analysed.',
        scan_timestamp: '2026-06-26T17:00:00Z',
        file_hash: 'a'.repeat(64),
      },
    });

    renderUploadForm();
    const file = new File(['a,b\n1,2\n'], 'data.csv', { type: 'text/csv' });
    await user.upload(screen.getByLabelText('CSV file'), file);
    await user.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() => {
      expect(screen.getByText(/uploaded: data.csv/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/security scan: safe/i)).toBeInTheDocument();
  });

  it('requires hash confirmation for files over 50 MB', async () => {
    const user = userEvent.setup();
    vi.spyOn(hashUtils, 'sha256File').mockResolvedValue('b'.repeat(64));
    vi.spyOn(uploadsApi, 'uploadCsv').mockResolvedValue({
      file_id: 2,
      filename: 'large.csv',
      file_hash: 'b'.repeat(64),
      size_bytes: 60 * 1024 * 1024,
      row_count: 1,
      column_count: 2,
      is_duplicate: false,
      version_number: 1,
      client_hash_match: true,
      scan_result: {
        status: 'safe',
        issues: [],
        risk_score: 0,
        recommended_action: 'File passed scanner checks and can be analysed.',
        scan_timestamp: '2026-06-26T17:00:00Z',
        file_hash: 'b'.repeat(64),
      },
    });

    renderUploadForm();
    const file = new File(['a,b\n1,2\n'], 'large.csv', { type: 'text/csv' });
    Object.defineProperty(file, 'size', { value: 60 * 1024 * 1024 });

    await user.upload(screen.getByLabelText('CSV file'), file);
    expect(await screen.findByText('b'.repeat(64))).toBeInTheDocument();

    const uploadButton = screen.getByRole('button', { name: 'Upload' });
    expect(uploadButton).toBeDisabled();

    await user.click(screen.getByLabelText(/confirm this hash/i));
    await user.click(uploadButton);

    await waitFor(() => {
      expect(uploadsApi.uploadCsv).toHaveBeenCalledWith(file, {
        clientSha256: 'b'.repeat(64),
      });
    });
    expect(screen.getByText(/browser\/backend hash match: yes/i)).toBeInTheDocument();
  });

  it('shows duplicate resolution after a duplicate upload response', async () => {
    const user = userEvent.setup();
    vi.spyOn(uploadsApi, 'uploadCsv')
      .mockRejectedValueOnce(
        new uploadsApi.DuplicateUploadError('Duplicate file detected', {
          error: 'duplicate_upload',
          message: 'Duplicate file detected',
          file_hash: 'c'.repeat(64),
          existing_file: {
            id: 9,
            original_filename: 'existing.csv',
            file_hash: 'c'.repeat(64),
            size_bytes: 20,
            row_count: 3,
            column_count: 2,
            source: 'upload',
            created_at: '2026-06-26T17:00:00Z',
          },
          scan_result: {
            status: 'safe',
            issues: [],
            risk_score: 0,
            recommended_action: 'File passed scanner checks and can be analysed.',
            scan_timestamp: '2026-06-26T17:00:00Z',
            file_hash: 'c'.repeat(64),
          },
        }),
      )
      .mockResolvedValueOnce({
        file_id: 9,
        filename: 'existing.csv',
        file_hash: 'c'.repeat(64),
        size_bytes: 20,
        row_count: 3,
        column_count: 2,
        is_duplicate: true,
        version_number: 1,
        scan_result: {
          status: 'safe',
          issues: [],
          risk_score: 0,
          recommended_action: 'File passed scanner checks and can be analysed.',
          scan_timestamp: '2026-06-26T17:00:00Z',
          file_hash: 'c'.repeat(64),
        },
      });

    renderUploadForm();
    const file = new File(['a,b\n1,2\n'], 'dup.csv', { type: 'text/csv' });
    await user.upload(screen.getByLabelText('CSV file'), file);
    await user.click(screen.getByRole('button', { name: 'Upload' }));

    expect(await screen.findByText(/duplicate file detected/i)).toBeInTheDocument();
    expect(screen.getByText(/existing.csv/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Use existing file' }));

    await waitFor(() => {
      expect(uploadsApi.uploadCsv).toHaveBeenLastCalledWith(file, {
        duplicateAction: 'use_existing',
      });
    });
  });
});
