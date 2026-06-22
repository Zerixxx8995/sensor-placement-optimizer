import React, { useState } from 'react';
import ConfigPanel from './components/ConfigPanel/ConfigPanel';
import StatusBadge from './components/shared/StatusBadge';
import ErrorBanner from './components/shared/ErrorBanner';
import Visualizer from './components/Visualizer/Visualizer';
import { useOptimizationJob } from './hooks/useOptimizationJob';

export default function App() {
  const { jobId, status, result, error, isLoading, submitJob } = useOptimizationJob();

  // Keep a copy of the last submitted config so GridCanvas knows the area
  // dimensions and radii it needs for correct coordinate mapping.
  const [lastConfig, setLastConfig] = useState(null);

  const handleSubmit = (config) => {
    setLastConfig(config);
    submitJob(config);
  };

  let errorMsg = null;
  let errorDetail = null;
  if (error) {
    errorMsg = error.message || 'Optimization job failed';
    errorDetail = error.detail || null;
  }

  return (
    <div className="app-container">
      <header>
        <h1 className="app-title">PSO Sensor Placement Optimizer</h1>
        <p className="app-subtitle">
          Multi-objective coverage &amp; connectivity optimization using standard and chaos-based algorithms
        </p>
      </header>

      <main className="workspace-grid">
        {/* ── Left panel: configuration ─────────────────────────────── */}
        <ConfigPanel
          onSubmit={handleSubmit}
          isLoading={isLoading}
          error={null}
        />

        {/* ── Right panel: status + visualizer ─────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {errorMsg && (
            <ErrorBanner message={errorMsg} detail={errorDetail} />
          )}

          {jobId ? (
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* ── Job header ── */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid var(--border-color)',
                paddingBottom: '0.75rem',
              }}>
                <div>
                  <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.4rem', fontWeight: 600 }}>
                    Optimization Status
                  </h2>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                    Job ID: {jobId}
                  </span>
                </div>
                <StatusBadge status={status} />
              </div>

              {/* ── Spinner while pending ── */}
              {status === 'pending' && (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: '300px',
                  gap: '1rem',
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    border: '3px solid rgba(99, 102, 241, 0.1)',
                    borderTop: '3px solid var(--color-primary)',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                  }} />
                  <style>{`
                    @keyframes spin {
                      0%   { transform: rotate(0deg); }
                      100% { transform: rotate(360deg); }
                    }
                  `}</style>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                    Initializing optimization engine on backend…
                  </p>
                </div>
              )}

              {/* ── Failed state ── */}
              {status === 'failed' && (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: '300px',
                  color: 'var(--text-muted)',
                  gap: '0.5rem',
                }}>
                  <span style={{ fontSize: '3rem' }}>&times;</span>
                  <p>Optimization failed. Check error log above.</p>
                </div>
              )}

              {/* ── Success or Running: Visualizer ── */}
              {(status === 'running' || status === 'complete') && (
                <Visualizer
                  result={result}
                  config={lastConfig}
                  jobId={jobId}
                  status={status}
                />
              )}
            </div>
          ) : (
            /* ── Empty state ── */
            <div className="glass-panel" style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: '400px',
              gap: '1.5rem',
              textAlign: 'center',
            }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(99, 102, 241, 0.1)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                fontSize: '2rem',
                color: 'var(--color-primary)',
              }}>
                &#x2699;
              </div>
              <div>
                <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  No Active Optimization
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '320px' }}>
                  Configure your network deployment parameters in the sidebar panel and click{' '}
                  <strong>Run Optimization</strong> to launch a task.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
