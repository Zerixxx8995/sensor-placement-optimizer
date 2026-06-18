import React from 'react';

export default function Slider({ label, min, max, step = 1, value, onChange, showValue = true, unit = '', className = '', ...props }) {
  return (
    <div className={`slider-container ${className}`}>
      <div className="form-label">
        <span>{label}</span>
        {showValue && (
          <span className="value">
            {value}
            {unit}
          </span>
        )}
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={onChange}
        className="custom-slider"
        {...props}
      />
    </div>
  );
}
