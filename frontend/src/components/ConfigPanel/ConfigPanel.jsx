import React from 'react';
import { useConfigStore } from '../../store/configStore';
import AreaSettings from './AreaSettings';
import NodeSettings from './NodeSettings';
import WeightSliders from './WeightSliders';
import GridPainter from './GridPainter';
import StrategySelector from './StrategySelector';
import Button from '../shared/Button';

export default function ConfigPanel({ onSubmit, isLoading = false, error = null }) {
  const { config, resetConfig } = useConfigStore();

  const handleReset = () => {
    if (window.confirm('Reset all parameters to default?')) {
      resetConfig();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSubmit) {
      onSubmit(config);
    }
  };

  // Live client-side validations to show on the form
  const validations = [];
  if (config.sensing_radius >= config.comm_radius) {
    validations.push('Sensing radius must be strictly less than comm radius.');
  }
  const weightSum = config.weights.w1 + config.weights.w2 + config.weights.w3;
  if (Math.abs(weightSum - 1.0) > 1e-6) {
    validations.push(`Objective weights must sum to exactly 1.0 (currently ${weightSum.toFixed(3)}).`);
  }

  const isFormValid = validations.length === 0;

  return (
    <form onSubmit={handleSubmit} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
        <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.4rem', fontWeight: 600 }}>
          Configuration Panel
        </h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          Configure deploy space & optimization constraints
        </p>
      </div>

      <AreaSettings />
      <NodeSettings />
      <WeightSliders />
      <GridPainter />
      <StrategySelector />

      {validations.length > 0 && (
        <div style={{
          padding: '0.75rem 1rem',
          background: 'rgba(244, 63, 94, 0.08)',
          border: '1px solid rgba(244, 63, 94, 0.25)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.85rem',
          color: 'var(--color-danger)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem'
        }}>
          {validations.map((v, idx) => (
            <div key={idx}>&bull; {v}</div>
          ))}
        </div>
      )}

      {error && (
        <div style={{
          padding: '0.75rem 1rem',
          background: 'rgba(244, 63, 94, 0.08)',
          border: '1px solid rgba(244, 63, 94, 0.25)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.85rem',
          color: 'var(--color-danger)'
        }}>
          {typeof error === 'object' ? error.message || 'Error submitting job' : error}
        </div>
      )}

      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
        <Button
          type="button"
          onClick={handleReset}
          variant="secondary"
          style={{ flex: 1 }}
          disabled={isLoading}
        >
          Reset Defaults
        </Button>
        <Button
          type="submit"
          variant="primary"
          style={{ flex: 1 }}
          disabled={isLoading || !isFormValid}
        >
          {isLoading ? 'Running...' : 'Run Optimization'}
        </Button>
      </div>
    </form>
  );
}
