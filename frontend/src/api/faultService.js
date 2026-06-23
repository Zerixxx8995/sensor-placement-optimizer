import { httpClient } from './httpClient';

export const faultService = {
  /**
   * Submit a fault injection request to simulate random node dropouts.
   *
   * @param {string} jobId - UUID of a completed optimization job
   * @param {number|string} dropoutPercent - Percentage of nodes to fail (0, 100]
   * @param {number|string} [seed] - Optional seed for RNG
   * @returns {Promise<object>} Response containing degraded coverage map and metrics
   */
  submitFaultInject: (jobId, dropoutPercent, seed) => {
    const payload = {
      job_id: jobId,
      dropout_percent: parseFloat(dropoutPercent),
    };

    if (seed !== undefined && seed !== null && seed !== '') {
      const parsedSeed = parseInt(seed, 10);
      if (!isNaN(parsedSeed)) {
        payload.seed = parsedSeed;
      }
    }

    return httpClient.post('/fault-inject', payload);
  },
};
