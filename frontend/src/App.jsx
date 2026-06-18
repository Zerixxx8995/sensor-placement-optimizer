import React, { useState } from 'react';
import ConfigPanel from './components/ConfigPanel/ConfigPanel';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const handleSubmit = (config) => {
    console.log('Submitted Configuration:', config);
    setLoading(true);
    setSubmitError(null);
    setTimeout(() => {
      setLoading(false);
      alert('Job configuration validated successfully. (API call simulated in Step 8)');
    }, 1500);
  };

  return (
    <div className="app-container">
      <header>
        <h1 className="app-title">PSO Sensor Placement Optimizer</h1>
        <p className="app-subtitle">Multi-objective coverage & connectivity optimization using standard and chaos-based algorithms</p>
      </header>
      
      <main className="workspace-grid">
        <ConfigPanel
          onSubmit={handleSubmit}
          isLoading={loading}
          error={submitError}
        />
        
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '400px', borderStyle: 'dashed' }}>
          <h3 style={{ fontFamily: 'var(--font-title)', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Visualizer Viewport</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', maxWidth: '300px' }}>
            The live visualization canvas, metrics overlay, and convergence plots will be mounted here in Steps 10-12.
          </p>
        </div>
      </main>
    </div>
  );
}
