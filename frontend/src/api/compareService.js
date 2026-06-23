import { httpClient } from './httpClient';

export const compareService = {
  /**
   * Run a comparison run of all 4 strategies on the same configuration.
   *
   * @param {object} config - Validated OptimizationConfig
   * @returns {Promise<object>} Comparison results containing strategy metrics
   */
  runComparison: (config) => httpClient.post('/compare', config),
};
