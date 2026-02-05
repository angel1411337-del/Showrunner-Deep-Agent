import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PlanningOutputs } from './PlanningOutputs';

describe('PlanningOutputs', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads and renders outline, reveals, and twists from API exports', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        text: async () => '# Outline\n\n- Beat: Jon returns to Winterfell',
      })
      .mockResolvedValueOnce({
        ok: true,
        text: async () =>
          'mystery,reveal,evidence\nWho sent the letter?,Littlefinger,book2:1',
      })
      .mockResolvedValueOnce({
        ok: true,
        text: async () => '# Twist Bank\n\n- Arya is carrying a false name ledger',
      });

    render(<PlanningOutputs />);

    expect(screen.getByText(/Loading planning outputs/i)).toBeInTheDocument();
    expect(await screen.findByText(/Beat: Jon returns to Winterfell/i)).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'Littlefinger' })).toBeInTheDocument();
    expect(screen.getByText(/Arya is carrying a false name ledger/i)).toBeInTheDocument();

    expect(fetch).toHaveBeenCalledTimes(3);
    expect(fetch).toHaveBeenNthCalledWith(1, 'http://localhost:8000/api/exports/outline');
    expect(fetch).toHaveBeenNthCalledWith(2, 'http://localhost:8000/api/exports/reveals');
    expect(fetch).toHaveBeenNthCalledWith(3, 'http://localhost:8000/api/exports/twists');
  });

  it('shows empty-state messages when exports are missing', async () => {
    fetch
      .mockResolvedValueOnce({ ok: true, text: async () => '' })
      .mockResolvedValueOnce({ ok: true, text: async () => '' })
      .mockResolvedValueOnce({ ok: true, text: async () => '' });

    render(<PlanningOutputs />);

    await waitFor(() => {
      expect(screen.getByText('No outline export found.')).toBeInTheDocument();
    });
    expect(screen.getByText('No reveal ledger export found.')).toBeInTheDocument();
    expect(screen.getByText('No twist bank export found.')).toBeInTheDocument();
  });
});
