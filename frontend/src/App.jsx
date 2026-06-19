import React from 'react';
import ConfigPanel from './components/ConfigPanel/ConfigPanel';
import StatusBadge from './components/shared/StatusBadge';
import ErrorBanner from './components/shared/ErrorBanner';
import { useOptimizationJob } from './hooks/useOptimizationJob';

export default function App() {
  const { jobId, status, result, error, isLoading, submitJob } = useOptimizationJob();

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
        <p className="app-subtitle">Multi-objective coverage & connectivity optimization using standard and chaos-based algorithms</p>
      </header>
      
      <main className="workspace-grid">
        <ConfigPanel
          onSubmit={submitJob}
          isLoading={isLoading}
          error={null}
        />
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {errorMsg && (
            <ErrorBanner
              message={errorMsg}
              detail={errorDetail}
            />
          )}

          {jobId ? (
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
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

              {(status === 'pending' || status === 'running') && (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px', gap: '1rem' }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    border: '3px solid rgba(99, 102, 241, 0.1)',
                    borderTop: '3px solid var(--color-primary)',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }} />
                  <style>{`
                    @keyframes spin {
                      0% { transform: rotate(0deg); }
                      100% { transform: rotate(360deg); }
                    }
                  `}</style>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                    Running optimization engine on backend...
                  </p>
                </div>
              )}

              {status === 'failed' && (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px', color: 'var(--text-muted)', gap: '0.5rem' }}>
                  <span style={{ fontSize: '3rem' }}>&times;</span>
                  <p>Optimization failed. Check error log above.</p>
                </div>
              )}

              {status === 'complete' && result && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                    <div className="glass-card" style={{ textAlign: 'center' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Coverage Ratio</span>
                      <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--color-success)', margin: '0.25rem 0' }}>
                        {(result.coverage_ratio * 100).toFixed(1)}%
                      </div>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Target: &ge; 91%</span>
                    </div>

                    <div className="glass-card" style={{ textAlign: 'center' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Connectivity Ratio</span>
                      <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--color-info)', margin: '0.25rem 0' }}>
                        {(result.connectivity_ratio * 100).toFixed(1)}%
                      </div>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Connected to Base Sink</span>
                    </div>

                    <div className="glass-card" style={{ textAlign: 'center' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Avg Node Energy</span>
                      <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--color-warning)', margin: '0.25rem 0' }}>
                        {result.avg_energy.toFixed(3)} J
                      </div>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Remaining Budget</span>
                    </div>
                  </div>

                  <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1rem', fontWeight: 600, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                      Solver Details
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.9rem' }}>
                      <div>Compute Time: <strong>{result.compute_time_seconds.toFixed(2)}s</strong></div>
                      <div>Iterations Run: <strong>{result.iterations_run}</strong></div>
                      <div>GPU Accelerated: <strong>{result.gpu_used ? 'Yes' : 'No'}</strong></div>
                      <div>Sensors Deployed: <strong>{result.best_positions?.length || 0}</strong></div>
                    </div>
                  </div>

                  <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '200px', borderStyle: 'dashed', borderColor: 'var(--border-color)' }}>
                    <h3 style={{ fontFamily: 'var(--font-title)', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Visualizer Canvas Placeholder</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', maxWidth: '350px' }}>
                      Result telemetry successfully fetched! Visual maps, sensor circles, and links will paint here in Step 10.
                    </p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '400px', gap: '1.5rem', textAlign: 'center' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(99, 102, 241, 0.1)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                fontSize: '2rem',
                color: 'var(--color-primary)'
              }}>
                &#x2699;
              </div>
              <div>
                <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  No Active Optimization
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '320px' }}>
                  Configure your network deployment parameters in the sidebar panel and click <strong>Run Optimization</strong> to launch a task.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
