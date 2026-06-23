import { describe, it, expect, vi, beforeEach } from 'vitest';
import { httpClient } from '../src/api/httpClient';
import { compareService } from '../src/api/compareService';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('compareService', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('should call the correct endpoint with the correct payload', async () => {
    const config = {
      area: { width: 100, height: 100 },
      num_nodes: 20,
      sensing_radius: 10,
      comm_radius: 20,
      weights: { w1: 0.5, w2: 0.25, w3: 0.25 },
    };

    const mockResponse = {
      job_id: 'compare-job-123',
      status: 'complete',
      results: [
        {
          strategy: 'random',
          coverage_ratio: 0.5,
          connectivity_ratio: 0.6,
          avg_energy: 0.9,
          compute_time_seconds: 0.1,
        },
      ],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockResponse,
    });

    const result = await compareService.runComparison(config);

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, reqConfig] = mockFetch.mock.calls[0];

    expect(url).toBe('http://localhost:8000/api/v1/compare');
    expect(reqConfig.method).toBe('POST');
    expect(reqConfig.body).toBe(JSON.stringify(config));
    expect(result).toEqual(mockResponse);
  });
});
