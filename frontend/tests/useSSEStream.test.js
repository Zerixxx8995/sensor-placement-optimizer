import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSSEStream } from '../src/hooks/useSSEStream';

// Mock EventSource class
class MockEventSource {
  static instances = [];

  constructor(url) {
    this.url = url;
    this.close = vi.fn();
    this.onmessage = null;
    this.onerror = null;
    MockEventSource.instances.push(this);
  }

  emitMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  emitError(err) {
    if (this.onerror) {
      this.onerror(err);
    }
  }
}

describe('useSSEStream hook tests', () => {
  beforeEach(() => {
    MockEventSource.instances = [];
    global.EventSource = MockEventSource;
  });

  afterEach(() => {
    delete global.EventSource;
  });

  it('should initialize with default states and not open EventSource if jobId is falsy', () => {
    const { result } = renderHook(() => useSSEStream(null));

    expect(result.current.particles).toEqual([]);
    expect(result.current.iteration).toBe(0);
    expect(result.current.bestFitness).toBeNull();
    expect(result.current.bestPositions).toEqual([]);
    expect(result.current.connected).toBe(false);
    expect(result.current.error).toBeNull();

    expect(MockEventSource.instances).toHaveLength(0);
  });

  it('should establish EventSource connection when jobId is provided', () => {
    const jobId = 'test-job-uuid';
    const { result } = renderHook(() => useSSEStream(jobId));

    expect(result.current.connected).toBe(true);
    expect(MockEventSource.instances).toHaveLength(1);
    expect(MockEventSource.instances[0].url).toContain(`/optimize/${jobId}/stream`);
  });

  it('should handle connected event', () => {
    const jobId = 'test-job-uuid';
    const { result } = renderHook(() => useSSEStream(jobId));

    const instance = MockEventSource.instances[0];
    
    act(() => {
      instance.emitMessage({ event: 'connected' });
    });

    expect(result.current.connected).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should handle iteration events and trigger onIteration callback', () => {
    const jobId = 'test-job-uuid';
    const onIterationMock = vi.fn();
    const { result } = renderHook(() => useSSEStream(jobId, { onIteration: onIterationMock }));

    const instance = MockEventSource.instances[0];

    const iterationData = {
      event: 'iteration',
      iteration: 5,
      best_fitness: 0.85,
      best_positions: [{ x: 10, y: 20 }],
      particles: [[{ x: 11, y: 19 }]]
    };

    act(() => {
      instance.emitMessage(iterationData);
    });

    expect(result.current.iteration).toBe(5);
    expect(result.current.bestFitness).toBe(0.85);
    expect(result.current.bestPositions).toEqual([{ x: 10, y: 20 }]);
    expect(result.current.particles).toEqual([[{ x: 11, y: 19 }]]);
    expect(onIterationMock).toHaveBeenCalledWith(iterationData);
  });

  it('should handle complete event, close connection, and trigger onComplete callback', () => {
    const jobId = 'test-job-uuid';
    const onCompleteMock = vi.fn();
    const { result } = renderHook(() => useSSEStream(jobId, { onComplete: onCompleteMock }));

    const instance = MockEventSource.instances[0];

    const completeData = {
      event: 'complete',
      result: { finalFitness: 0.95 }
    };

    act(() => {
      instance.emitMessage(completeData);
    });

    expect(result.current.connected).toBe(false);
    expect(instance.close).toHaveBeenCalledTimes(1);
    expect(onCompleteMock).toHaveBeenCalledWith(completeData.result);
  });

  it('should handle failed event, close connection, set error, and trigger onFailed callback', () => {
    const jobId = 'test-job-uuid';
    const onFailedMock = vi.fn();
    const { result } = renderHook(() => useSSEStream(jobId, { onFailed: onFailedMock }));

    const instance = MockEventSource.instances[0];

    const failedData = {
      event: 'failed',
      error: 'Optimization converged prematurely or crashed'
    };

    act(() => {
      instance.emitMessage(failedData);
    });

    expect(result.current.connected).toBe(false);
    expect(result.current.error).toBe(failedData.error);
    expect(instance.close).toHaveBeenCalledTimes(1);
    expect(onFailedMock).toHaveBeenCalledWith(failedData.error);
  });

  it('should handle connection errors, set connection status and error, and call onFailed', () => {
    const jobId = 'test-job-uuid';
    const onFailedMock = vi.fn();
    const { result } = renderHook(() => useSSEStream(jobId, { onFailed: onFailedMock }));

    const instance = MockEventSource.instances[0];

    act(() => {
      instance.emitError(new Error('Network error'));
    });

    expect(result.current.connected).toBe(false);
    expect(result.current.error).toBe('Connection interrupted or closed.');
    expect(instance.close).toHaveBeenCalledTimes(1);
    expect(onFailedMock).toHaveBeenCalledWith('EventSource connection error');
  });

  it('should close the event source connection on unmount', () => {
    const jobId = 'test-job-uuid';
    const { unmount } = renderHook(() => useSSEStream(jobId));

    const instance = MockEventSource.instances[0];
    expect(instance.close).not.toHaveBeenCalled();

    unmount();

    expect(instance.close).toHaveBeenCalledTimes(1);
  });
});
