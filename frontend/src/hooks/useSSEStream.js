import { useEffect, useState, useRef } from 'react';

const BASE_URL = import.meta.env?.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * useSSEStream
 * ------------
 * A custom React hook that establishes a Server-Sent Events (SSE) connection
 * to stream optimization progress updates (iterations, particles, best positions).
 *
 * @param {string|null} jobId - The UUID of the active optimization job.
 * @param {object} options - Optional event callbacks.
 * @param {function} options.onIteration - Callback invoked on each iteration update.
 * @param {function} options.onComplete - Callback invoked when job completes successfully.
 * @param {function} options.onFailed - Callback invoked when job fails.
 */
export function useSSEStream(jobId, options = {}) {
  const { onIteration, onComplete, onFailed } = options;
  const [particles, setParticles] = useState([]);
  const [iteration, setIteration] = useState(0);
  const [bestFitness, setBestFitness] = useState(null);
  const [bestPositions, setBestPositions] = useState([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);

  const eventSourceRef = useRef(null);

  useEffect(() => {
    // If no jobId is active, reset state and return
    if (!jobId) {
      setParticles([]);
      setIteration(0);
      setBestFitness(null);
      setBestPositions([]);
      setConnected(false);
      setError(null);
      return;
    }

    setConnected(true);
    setError(null);

    // Resolve URL (handle absolute or relative BASE_URL)
    const baseUrlResolved = BASE_URL.startsWith('http')
      ? BASE_URL
      : `${window.location.origin}${BASE_URL}`;

    const url = `${baseUrlResolved}/optimize/${jobId}/stream`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'connected') {
          setConnected(true);
        } else if (data.event === 'iteration') {
          setIteration(data.iteration);
          setBestFitness(data.best_fitness);
          setBestPositions(data.best_positions);
          setParticles(data.particles);
          if (onIteration) onIteration(data);
        } else if (data.event === 'complete') {
          setConnected(false);
          es.close();
          if (onComplete) onComplete(data.result);
        } else if (data.event === 'failed') {
          setConnected(false);
          setError(data.error);
          es.close();
          if (onFailed) onFailed(data.error);
        }
      } catch (err) {
        console.error('Error parsing SSE event data:', err);
      }
    };

    es.onerror = (err) => {
      // EventSource raises generic errors without details when closed by client/server
      console.error('EventSource connection error:', err);
      setError('Connection interrupted or closed.');
      setConnected(false);
      es.close();
      if (onFailed) onFailed('EventSource connection error');
    };

    return () => {
      if (es) {
        es.close();
      }
    };
  }, [jobId, onIteration, onComplete, onFailed]);

  return {
    particles,
    iteration,
    bestFitness,
    bestPositions,
    connected,
    error,
  };
}
