import { describe, it, expect, vi, beforeEach } from 'vitest';
import { httpClient, ApiError } from '../src/api/httpClient';
import { optimizeService } from '../src/api/optimizeService';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('httpClient', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('should construct the correct URL and call fetch for GET requests', async () => {
    const mockData = { data: 'test' };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockData,
    });

    const result = await httpClient.get('/test-endpoint');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, config] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/test-endpoint');
    expect(config.method).toBe('GET');
    expect(config.headers['Content-Type']).toBe('application/json');
    expect(config.headers['X-Request-ID']).toBeDefined();
    expect(result).toEqual(mockData);
  });

  it('should serialize request body and send POST requests correctly', async () => {
    const payload = { key: 'value' };
    const mockResponse = { success: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockResponse,
    });

    const result = await httpClient.post('/test-endpoint', payload);

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, config] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/test-endpoint');
    expect(config.method).toBe('POST');
    expect(config.body).toBe(JSON.stringify(payload));
    expect(result).toEqual(mockResponse);
  });

  it('should throw ApiError with backend status code and details on error responses', async () => {
    const backendError = { error: 'Validation Error', detail: 'Invalid weights' };
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => backendError,
    });

    let thrownError;
    try {
      await httpClient.get('/error-endpoint');
    } catch (e) {
      thrownError = e;
    }

    expect(thrownError).toBeInstanceOf(ApiError);
    expect(thrownError.statusCode).toBe(422);
    expect(thrownError.message).toBe('Validation Error');
    expect(thrownError.detail).toBe('Invalid weights');
  });

  it('should support absolute URLs without prefixing base URL', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: () => null,
      },
    });

    await httpClient.get('https://example.com/api/v1/test');
    expect(mockFetch.mock.calls[0][0]).toBe('https://example.com/api/v1/test');
  });
});

describe('optimizeService', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('should submit optimization job config correctly', async () => {
    const config = {
      area: { width: 100, height: 100 },
      nodes: { count: 10, range: 15 },
    };
    const mockResponse = { job_id: 'job-123' };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockResponse,
    });

    const result = await optimizeService.submitOptimizationJob(config);

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, reqConfig] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/optimize');
    expect(reqConfig.method).toBe('POST');
    expect(reqConfig.body).toBe(JSON.stringify(config));
    expect(result).toEqual(mockResponse);
  });

  it('should fetch job status correctly', async () => {
    const mockResponse = { job_id: 'job-123', status: 'pending' };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockResponse,
    });

    const result = await optimizeService.getJobStatus('job-123');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const url = mockFetch.mock.calls[0][0];
    expect(url).toBe('http://localhost:8000/api/v1/optimize/job-123/status');
    expect(result).toEqual(mockResponse);
  });

  it('should fetch job result correctly', async () => {
    const mockResponse = { job_id: 'job-123', status: 'complete', fitness_history: [0.5, 0.4] };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: {
        get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null,
      },
      json: async () => mockResponse,
    });

    const result = await optimizeService.getJobResult('job-123');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const url = mockFetch.mock.calls[0][0];
    expect(url).toBe('http://localhost:8000/api/v1/optimize/job-123/result');
    expect(result).toEqual(mockResponse);
  });
});
