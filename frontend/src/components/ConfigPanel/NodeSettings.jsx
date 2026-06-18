import React from 'react';
import { useConfigStore } from '../../store/configStore';

export default function NodeSettings() {
  const { config, updateField } = useConfigStore();

  const handleInputChange = (field, isFloat = false) => (e) => {
    let value = e.target.value === '' ? null : (isFloat ? parseFloat(e.target.value) : parseInt(e.target.value, 10));
    if (value !== null && isNaN(value)) value = 0;
    updateField(field, value);
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.1rem', fontWeight: 600, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        Node Configuration
      </h3>

      <div className="form-group">
        <label className="form-label">Node Count</label>
        <input
          type="number"
          min="1"
          max="10000"
          value={config.num_nodes ?? ''}
          onChange={handleInputChange('num_nodes')}
          className="form-input"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Sensing Radius Rs (m)</label>
        <input
          type="number"
          min="0.1"
          max="5000"
          step="0.5"
          value={config.sensing_radius ?? ''}
          onChange={handleInputChange('sensing_radius', true)}
          className="form-input"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Comm Radius Rc (m)</label>
        <input
          type="number"
          min="0.1"
          max="10000"
          step="0.5"
          value={config.comm_radius ?? ''}
          onChange={handleInputChange('comm_radius', true)}
          className="form-input"
        />
        {config.sensing_radius >= config.comm_radius && (
          <span style={{ fontSize: '0.75rem', color: 'var(--color-danger)' }}>
            Warning: Rs must be less than Rc
          </span>
        )}
      </div>

      <div className="form-group">
        <label className="form-label">Initial Energy (J)</label>
        <input
          type="number"
          min="0.01"
          max="1000"
          step="0.1"
          value={config.initial_energy ?? ''}
          onChange={handleInputChange('initial_energy', true)}
          className="form-input"
        />
      </div>

      <div className="form-group">
        <label className="form-label">RNG Seed</label>
        <input
          type="number"
          min="0"
          value={config.seed ?? ''}
          onChange={handleInputChange('seed')}
          placeholder="None (random)"
          className="form-input"
        />
      </div>
    </div>
  );
}
