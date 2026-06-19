import { create } from 'zustand';

export const useJobStore = create((set) => ({
  jobId: null,
  status: null,
  result: null,
  error: null,
  isLoading: false,

  setJobId: (jobId) => set({ jobId }),
  setStatus: (status) => set({ status }),
  setResult: (result) => set({ result }),
  setError: (error) => set({ error }),
  setIsLoading: (isLoading) => set({ isLoading }),

  resetJob: () => set({
    jobId: null,
    status: null,
    result: null,
    error: null,
    isLoading: false,
  }),
}));
