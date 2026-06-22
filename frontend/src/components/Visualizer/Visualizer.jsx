import React from 'react';
import GridCanvas from './GridCanvas';
import LiveMetrics from './LiveMetrics';

/**
 * Visualizer
 * ----------
 * Parent component that owns the full visualisation panel.
 * Composes GridCanvas (the canvas renderer) and LiveMetrics (the stats bar).
 *
 * Props
 * -----
 *  result        {object|null}  OptimizationResult from the backend.
 *  config        {object|null}  The OptimizationConfig that was submitted, used
 *                               to pass sensingRadius / commRadius / area dims
 *                               to GridCanvas.
 */
export default function Visualizer({ result, config }) {
  const areaWidth = config?.area?.width ?? 100;
  const areaHeight = config?.area?.height ?? 100;
  const sensingRadius = config?.sensing_radius ?? 10;
  const commRadius = config?.comm_radius ?? 20;

  return (
    <div className="visualizer-container">
      {/* ─── Header ─────────────────────────────────────────────────── */}
      <div className="visualizer-header">
        <div>
          <h2 className="visualizer-title">Deployment Visualizer</h2>
          <p className="visualizer-subtitle">
            Coverage heatmap · Sensor nodes · Communication links
          </p>
        </div>
        {result && (
          <div className="vis-badge-group">
            {result.gpu_used && (
              <span className="vis-badge vis-badge--gpu">⚡ GPU</span>
            )}
            <span className="vis-badge vis-badge--complete">● Complete</span>
          </div>
        )}
      </div>

      {/* ─── Canvas ─────────────────────────────────────────────────── */}
      <GridCanvas
        result={result}
        areaWidth={areaWidth}
        areaHeight={areaHeight}
        sensingRadius={sensingRadius}
        commRadius={commRadius}
      />

      {/* ─── Metrics bar ────────────────────────────────────────────── */}
      <LiveMetrics result={result} />
    </div>
  );
}
