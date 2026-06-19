import { useEffect, useRef, useCallback } from 'react';
import { useJobStore } from '../store/jobStore';
import { optimizeService } from '../api/optimizeService';

export function useOptimizationJob() {
  const {
    jobId,
    status,
    result,
    error,
    isLoading,
    setJobId,
    setStatus,
    setResult,
    setError,
    setIsLoading,
    resetJob,
  } = useJobStore();

  const pollIntervalRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  const fetchResult = useCallback(async (id) => {
    try {
      const res = await optimizeService.getJobResult(id);
      setResult(res);
    } catch (err) {
      setError(err);
    }
  }, [setResult, setError]);

  const startPolling = useCallback((id) => {
    stopPolling();

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await optimizeService.getJobStatus(id);
        const newStatus = res.status;
        setStatus(newStatus);

        if (newStatus === 'complete') {
          stopPolling();
          await fetchResult(id);
        } else if (newStatus === 'failed') {
          stopPolling();
          await fetchResult(id);
        }
      } catch (err) {
        stopPolling();
        setError(err);
      }
    }, 1000);
  }, [setStatus, setError, stopPolling, fetchResult]);

  const submitJob = useCallback(async (config) => {
    resetJob();
    setIsLoading(true);

    try {
      const res = await optimizeService.submitOptimizationJob(config);
      setJobId(res.job_id);
      setStatus(res.status || 'pending');
      setIsLoading(false);
      startPolling(res.job_id);
    } catch (err) {
      setIsLoading(false);
      setError(err);
    }
  }, [resetJob, setIsLoading, setJobId, setStatus, startPolling, setError]);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    jobId,
    status,
    result,
    error,
    isLoading,
    submitJob,
    resetJob,
  };
}
