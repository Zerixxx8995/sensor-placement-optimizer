import { httpClient } from './httpClient';

export const optimizeService = {
  submitOptimizationJob: (config) => httpClient.post('/optimize', config),
  getJobStatus: (jobId) => httpClient.get(`/optimize/${jobId}/status`),
  getJobResult: (jobId) => httpClient.get(`/optimize/${jobId}/result`),
};
