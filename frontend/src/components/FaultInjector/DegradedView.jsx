import React from 'react';

export default function DegradedView({ faultResult, originalResult }) {
  if (!faultResult) return null;

  const originalCov = (faultResult.original_coverage_ratio * 100).toFixed(1);
  const degradedCov = (faultResult.degraded_coverage_ratio * 100).toFixed(1);
  
  // Use originalResult connectivity ratio if available, otherwise faultResult original
  const origConnRatio = originalResult?.connectivity_ratio ?? 0;
  const originalConn = (origConnRatio * 100).toFixed(1);
  const degradedConn = (faultResult.connectivity_ratio * 100).toFixed(1);

  const covDiff = (faultResult.degraded_coverage_ratio - faultResult.original_coverage_ratio) * 100;
  const connDiff = (faultResult.connectivity_ratio - origConnRatio) * 100;

  return (
    <div className="degraded-view-container">
      <h3 className="degraded-title">Simulation Results</h3>
      
      <div className="degraded-metrics-grid">
        {/* Coverage Metric */}
        <div className="degraded-metric-card">
          <span className="metric-label">Area Coverage</span>
          <div className="metric-comparison">
            <span className="metric-val original">{originalCov}%</span>
            <span className="metric-arrow">→</span>
            <span className={`metric-val degraded ${covDiff < 0 ? 'text-danger' : 'text-success'}`}>{degradedCov}%</span>
          </div>
          <span className={`metric-diff ${covDiff < 0 ? 'text-danger' : 'text-success'}`}>
            {covDiff >= 0 ? '+' : ''}{covDiff.toFixed(1)}%
          </span>
        </div>

        {/* Connectivity Metric */}
        <div className="degraded-metric-card">
          <span className="metric-label">Network Connectivity</span>
          <div className="metric-comparison">
            <span className="metric-val original">{originalConn}%</span>
            <span className="metric-arrow">→</span>
            <span className={`metric-val degraded ${connDiff < 0 ? 'text-danger' : 'text-success'}`}>{degradedConn}%</span>
          </div>
          <span className={`metric-diff ${connDiff < 0 ? 'text-danger' : 'text-success'}`}>
            {connDiff >= 0 ? '+' : ''}{connDiff.toFixed(1)}%
          </span>
        </div>

        {/* Node Failures Metric */}
        <div className="degraded-metric-card">
          <span className="metric-label">Disabled Sensors</span>
          <div className="metric-value-large text-danger">
            {faultResult.nodes_failed} <span className="metric-slash">/</span> {faultResult.total_nodes}
          </div>
          <span className="metric-meta-text">
            ({faultResult.dropout_percent}% rate)
          </span>
        </div>
      </div>
    </div>
  );
}
