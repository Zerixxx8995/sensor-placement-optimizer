import React from 'react';

/**
 * LiveMetrics
 * -----------
 * Displays the four key outcome metrics from an optimization result in a
 * compact, styled row.  Designed to live just below the GridCanvas.
 *
 * Props
 * -----
 *  result   {object|null}  OptimizationResult.  If null, renders an empty state.
 */
export default function LiveMetrics({ result }) {
  if (!result) {
    return (
      <div className="live-metrics live-metrics--empty">
        <span>Run optimization to see live metrics.</span>
      </div>
    );
  }

  const metrics = [
    {
      id: 'coverage',
      label: 'Coverage',
      value: `${(result.coverage_ratio * 100).toFixed(1)}%`,
      sub: 'Target ≥ 91%',
      color: 'var(--color-success)',
      glow: 'var(--color-success-glow)',
      icon: '◉',
    },
    {
      id: 'connectivity',
      label: 'Connectivity',
      value: `${(result.connectivity_ratio * 100).toFixed(1)}%`,
      sub: 'Nodes connected',
      color: 'var(--color-info)',
      glow: 'rgba(14,165,233,0.2)',
      icon: '⬡',
    },
    {
      id: 'energy',
      label: 'Avg Energy',
      value: `${result.avg_energy.toFixed(3)} J`,
      sub: 'Per node remaining',
      color: 'var(--color-warning)',
      glow: 'rgba(251,191,36,0.2)',
      icon: '⚡',
    },
    {
      id: 'nodes',
      label: 'Sensors',
      value: result.best_positions?.length ?? 0,
      sub: `${result.iterations_run} iters · ${result.compute_time_seconds.toFixed(2)}s`,
      color: '#a78bfa',
      glow: 'rgba(167,139,250,0.2)',
      icon: '⬤',
    },
  ];

  return (
    <div className="live-metrics">
      {metrics.map((m) => (
        <div
          key={m.id}
          id={`metric-${m.id}`}
          className="live-metric-card"
          style={{ '--metric-color': m.color, '--metric-glow': m.glow }}
        >
          <span className="metric-icon">{m.icon}</span>
          <div className="metric-content">
            <span className="metric-label">{m.label}</span>
            <span className="metric-value" style={{ color: m.color }}>{m.value}</span>
            <span className="metric-sub">{m.sub}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
