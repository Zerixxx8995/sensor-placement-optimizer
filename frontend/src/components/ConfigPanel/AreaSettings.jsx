import React from 'react';
import { useConfigStore } from '../../store/configStore';

export default function AreaSettings() {
  const { config, updateNestedField, updateField } = useConfigStore();

  const handleWidthChange = (e) => {
    const value = parseFloat(e.target.value) || 0;
    updateNestedField('area', 'width', value);
  };

  const handleHeightChange = (e) => {
    const value = parseFloat(e.target.value) || 0;
    updateNestedField('area', 'height', value);
  };

  const handleCellSizeChange = (e) => {
    const value = parseFloat(e.target.value) || 0;
    updateField('cell_size', value);
  };

  const cols = Math.floor(config.area.width / config.cell_size) || 0;
  const rows = Math.floor(config.area.height / config.cell_size) || 0;

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.1rem', fontWeight: 600, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        Area Dimensions
      </h3>
      
      <div className="form-group">
        <label className="form-label">Field Width (m)</label>
        <input
          type="number"
          min="1"
          max="10000"
          value={config.area.width}
          onChange={handleWidthChange}
          className="form-input"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Field Height (m)</label>
        <input
          type="number"
          min="1"
          max="10000"
          value={config.area.height}
          onChange={handleHeightChange}
          className="form-input"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Grid Resolution (m/cell)</label>
        <input
          type="number"
          min="0.1"
          max="100"
          step="0.5"
          value={config.cell_size}
          onChange={handleCellSizeChange}
          className="form-input"
        />
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Grid size: {cols} &times; {rows} cells
        </span>
      </div>
    </div>
  );
}
