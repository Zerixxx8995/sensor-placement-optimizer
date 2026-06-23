import { describe, it, expect, vi, beforeEach } from 'vitest';
import { httpClient } from '../src/api/httpClient';
import { faultService } from '../src/api/faultService';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('faultService', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('should call the correct endpoint with the correct payload including seed', async () => {
    const mockResponse = {
      job_id: 'degraded-job-uuid',
      original_coverage_ratio: 0.85,
      degraded_coverage_ratio: 0.62,
      nodes_failed: 3,
      total_nodes: 10,
      dropout_percent: 30.0,
      coverage_map: [[0.5, 0.6]],
      connectivity_ratio: 0.75,
      failed_indices: [2, 5, 8],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockResponse,
    });

    const result = await faultService.submitFaultInject('job-123', 30.0, 42);

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, reqConfig] = mockFetch.mock.calls[0];
    
    expect(url).toBe('http://localhost:8000/api/v1/fault-inject');
    expect(reqConfig.method).toBe('POST');
    expect(reqConfig.body).toBe(JSON.stringify({
      job_id: 'job-123',
      dropout_percent: 30.0,
      seed: 42,
    }));
    expect(result).toEqual(mockResponse);
  });

  it('should handle optional seed parameter omitted', async () => {
    const mockResponse = { success: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockResponse,
    });

    await faultService.submitFaultInject('job-123', 25.0);

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [, reqConfig] = mockFetch.mock.calls[0];
    
    expect(reqConfig.body).toBe(JSON.stringify({
      job_id: 'job-123',
      dropout_percent: 25.0,
    }));
  });

  it('should ignore invalid seeds (non-numeric strings)', async () => {
    const mockResponse = { success: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockResponse,
    });

    await faultService.submitFaultInject('job-123', 25.0, 'abc');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [, reqConfig] = mockFetch.mock.calls[0];
    
    expect(reqConfig.body).toBe(JSON.stringify({
      job_id: 'job-123',
      dropout_percent: 25.0,
    }));
  });
});
