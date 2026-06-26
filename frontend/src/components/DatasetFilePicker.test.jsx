import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { DatasetFilePicker } from './DatasetFilePicker.jsx';
import * as uploadsApi from '../api/uploads.js';

describe('DatasetFilePicker', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('lists uploads and calls onSelect when a file is chosen', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    vi.spyOn(uploadsApi, 'listUploads').mockResolvedValue({
      items: [
        {
          id: 3,
          original_filename: 'sales.csv',
          row_count: 10,
          column_count: 4,
        },
      ],
    });

    render(
      <MemoryRouter>
        <DatasetFilePicker title="Choose dataset" onSelect={onSelect} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('sales.csv')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /sales.csv/i }));
    expect(onSelect).toHaveBeenCalledWith({
      file_id: 3,
      filename: 'sales.csv',
    });
  });
});
