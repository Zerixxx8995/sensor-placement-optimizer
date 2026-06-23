import React from 'react';
import Slider from '../shared/Slider';

export default function DropoutSlider({ value, onChange, disabled }) {
  return (
    <Slider
      label="Node Dropout Rate"
      min={1}
      max={100}
      step={1}
      value={value}
      onChange={onChange}
      disabled={disabled}
      unit="%"
      className="dropout-slider"
      id="dropout-slider-input"
    />
  );
}
