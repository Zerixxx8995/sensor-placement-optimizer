import { describe, it, expect } from 'vitest';
import { valueToViridis, valueToViridisRGB } from '../src/utils/colormap';

describe('colormap utility tests', () => {
  it('should map 0 to dark purple (#440154)', () => {
    expect(valueToViridis(0)).toBe('#440154');
    expect(valueToViridisRGB(0)).toEqual([68, 1, 84]);
  });

  it('should clamp out-of-bounds input values', () => {
    // Underflow (< 0)
    expect(valueToViridis(-0.5)).toBe('#440154');
    expect(valueToViridisRGB(-100)).toEqual([68, 1, 84]);

    // Overflow (> 1)
    const maxRGB = valueToViridisRGB(1);
    expect(valueToViridisRGB(1.5)).toEqual(maxRGB);
    expect(valueToViridis(2.0)).toBe(valueToViridis(1));
  });

  it('should return valid hex colors for intermediate values', () => {
    const hexPattern = /^#[0-9a-f]{6}$/i;
    
    expect(valueToViridis(0.25)).toMatch(hexPattern);
    expect(valueToViridis(0.5)).toMatch(hexPattern);
    expect(valueToViridis(0.75)).toMatch(hexPattern);
  });

  it('should return valid RGB arrays for intermediate values', () => {
    const rgb = valueToViridisRGB(0.5);
    expect(Array.isArray(rgb)).toBe(true);
    expect(rgb).toHaveLength(3);
    rgb.forEach(channel => {
      expect(typeof channel).toBe('number');
      expect(channel).toBeGreaterThanOrEqual(0);
      expect(channel).toBeLessThanOrEqual(255);
    });
  });
});
