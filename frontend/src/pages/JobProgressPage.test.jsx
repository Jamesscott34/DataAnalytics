import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { JobProgressPage } from './JobProgressPage.jsx';
import * as jobsApi from '../api/jobs.js';

describe('JobProgressPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('queues a demo job and shows progress', async () => {
    const user = userEvent.setup();
    vi.spyOn(jobsApi, 'listJobs').mockResolvedValue({ items: [], total: 0 });
    vi.spyOn(jobsApi, 'createJob').mockResolvedValue({
      id: 'job-1',
      job_type: 'demo',
      status: 'queued',
      progress: 0,
    });
    vi.spyOn(jobsApi, 'getJob').mockResolvedValue({
      id: 'job-1',
      job_type: 'demo',
      status: 'complete',
      progress: 100,
      result: { message: 'Demo job complete' },
    });

    render(
      <MemoryRouter initialEntries={['/jobs']}>
        <Routes>
          <Route path="/jobs" element={<JobProgressPage />} />
          <Route path="/jobs/:jobId" element={<JobProgressPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /start demo job/i }));

    await waitFor(() => {
      expect(screen.getByLabelText('Job progress 100%')).toBeInTheDocument();
    });
    expect(screen.getByText('Status: complete')).toBeInTheDocument();
  });
});
