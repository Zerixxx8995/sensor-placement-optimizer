import React, { useState } from 'react';
import DropoutSlider from './DropoutSlider';
import DegradedView from './DegradedView';
import Button from '../shared/Button';
import { faultService } from '../../api/faultService';

export default function FaultInjector({ jobId, originalResult, onInject, onReset }) {
  const [dropoutPercent, setDropoutPercent] = useState(30);
  const [seed, setSeed] = useState('');
  const [faultResult, setFaultResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInject = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await faultService.submitFaultInject(jobId, dropoutPercent, seed);
      setFaultResult(res);
      if (onInject) {
        onInject(res);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Fault injection failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFaultResult(null);
    setDropoutPercent(30);
    setSeed('');
    setError(null);
    if (onReset) {
      onReset();
    }
  };

  return (
    <div className="fault-injector-panel glass-card">
      <div className="fault-injector-header">
        <h2 className="fault-injector-title" style={{ fontFamily: 'var(--font-title)', fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
          Simulate Node Failures
        </h2>
        <p className="fault-injector-subtitle" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Randomly disable sensor nodes to test network resilience and coverage degradation.
        </p>
      </div>

      <div className="fault-injector-controls">
        <DropoutSlider
          value={dropoutPercent}
          onChange={(e) => setDropoutPercent(Number(e.target.value))}
          disabled={isLoading}
        />

        <div className="form-group" style={{ marginTop: '1rem' }}>
          <label className="form-label" htmlFor="fault-seed-input">
            <span>RNG Seed (optional)</span>
          </label>
          <input
            id="fault-seed-input"
            type="number"
            className="form-input"
            placeholder="e.g. 42 for reproducible results"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="error-text" style={{ color: 'var(--color-danger)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
            Error: {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.25rem' }}>
          <Button
            variant="primary"
            onClick={handleInject}
            disabled={isLoading}
            style={{ flex: 1 }}
          >
            {isLoading ? 'Simulating...' : 'Inject Faults'}
          </Button>

          {faultResult && (
            <Button
              variant="secondary"
              onClick={handleReset}
              disabled={isLoading}
            >
              Clear Simulation
            </Button>
          )}
        </div>
      </div>

      {faultResult && (
        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
          <DegradedView faultResult={faultResult} originalResult={originalResult} />
        </div>
      )}
    </div>
  );
}
