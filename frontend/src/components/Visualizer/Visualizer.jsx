import React, { useState, useEffect, useCallback } from 'react';
import GridCanvas from './GridCanvas';
import LiveMetrics from './LiveMetrics';
import ParticleLayer from './ParticleLayer';
import ConvergenceChart from '../ConvergenceChart/ConvergenceChart';
import FaultInjector from '../FaultInjector/FaultInjector';
import { useSSEStream } from '../../hooks/useSSEStream';

/**
 * Visualizer
 * ----------
 * Parent component that owns the full visualisation panel.
 * Composes GridCanvas (the canvas renderer) and LiveMetrics (the stats bar).
 * Supports real-time visualization of running jobs using Server-Sent Events (SSE).
 *
 * Props
 * -----
 *  result        {object|null}  OptimizationResult from the backend (when complete).
 *  config        {object|null}  The OptimizationConfig that was submitted.
 *  jobId         {string|null}  UUID of the active job.
 *  status        {string|null}  Job execution status ('running', 'complete', etc.).
 */
export default function Visualizer({ result, config, jobId, status }) {
  const isRunning = status === 'running';

  const [liveHistory, setLiveHistory] = useState([]);
  const [faultResult, setFaultResult] = useState(null);

  // Clear live history and fault simulation results when jobId changes
  useEffect(() => {
    setLiveHistory([]);
    setFaultResult(null);
  }, [jobId]);

  const handleIteration = useCallback((data) => {
    setLiveHistory((prev) => {
      if (prev.some((item) => item.iteration === data.iteration)) {
        return prev;
      }
      return [...prev, { iteration: data.iteration, fitness: data.best_fitness }];
    });
  }, []);

  // Connect to SSE stream if the job is active
  const {
    particles,
    iteration,
    bestFitness,
    bestPositions,
  } = useSSEStream(isRunning ? jobId : null, {
    onIteration: handleIteration,
  });

  // Map fitness history: liveHistory if running, result.fitness_history if complete
  const chartData = isRunning
    ? liveHistory
    : (result?.fitness_history || []).map((val, idx) => ({
        iteration: idx,
        fitness: val,
      }));

  const areaWidth = config?.area?.width ?? 100;
  const areaHeight = config?.area?.height ?? 100;
  const sensingRadius = config?.sensing_radius ?? 10;
  const commRadius = config?.comm_radius ?? 20;

  // Render live positions when running, fallback to final result when complete
  const displayResult = isRunning
    ? { best_positions: bestPositions, coverage_map: null }
    : faultResult
      ? {
          ...result,
          coverage_map: faultResult.coverage_map,
          failed_indices: faultResult.failed_indices,
        }
      : result;

  return (
    <div className="visualizer-container">
      {/* ─── Header ─────────────────────────────────────────────────── */}
      <div className="visualizer-header">
        <div>
          <h2 className="visualizer-title">
            {isRunning ? 'Optimizing Deployments...' : 'Deployment Visualizer'}
          </h2>
          <p className="visualizer-subtitle">
            {isRunning
              ? 'Real-time swarm convergence · Candidate nodes · Live updates'
              : 'Coverage heatmap · Sensor nodes · Communication links'}
          </p>
        </div>
        {status === 'complete' && result && (
          <div className="vis-badge-group">
            {result.gpu_used && (
              <span className="vis-badge vis-badge--gpu">⚡ GPU</span>
            )}
            <span className="vis-badge vis-badge--complete">● Complete</span>
          </div>
        )}
        {isRunning && (
          <div className="vis-badge-group">
            <span
              className="vis-badge"
              style={{
                background: 'rgba(99, 102, 241, 0.15)',
                color: 'var(--color-primary)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                animation: 'pulse 1.5s infinite',
              }}
            >
              ● Optimizing
            </span>
            <style>{`
              @keyframes pulse {
                0%   { opacity: 0.6; }
                50%  { opacity: 1; }
                100% { opacity: 0.6; }
              }
            `}</style>
          </div>
        )}
      </div>

      {/* ─── Canvas Layer Stack ─────────────────────────────────────── */}
      <GridCanvas
        result={displayResult}
        areaWidth={areaWidth}
        areaHeight={areaHeight}
        sensingRadius={sensingRadius}
        commRadius={commRadius}
      >
        {isRunning && (
          <ParticleLayer
            particles={particles}
            areaWidth={areaWidth}
            areaHeight={areaHeight}
          />
        )}
      </GridCanvas>

      {/* ─── Metrics bar ────────────────────────────────────────────── */}
      <LiveMetrics
        result={result}
        status={status}
        liveIteration={iteration}
        liveFitness={bestFitness}
      />

      {/* ─── Convergence Chart ──────────────────────────────────────── */}
      <ConvergenceChart data={chartData} />

      {/* ─── Fault Injector Simulation ───────────────────────────────── */}
      {status === 'complete' && result && (
        <FaultInjector
          jobId={jobId}
          originalResult={result}
          onInject={setFaultResult}
          onReset={() => setFaultResult(null)}
        />
      )}
    </div>
  );
}
