import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ComparisonTable from '../src/components/ComparisonTable/ComparisonTable';

describe('ComparisonTable Component Tests', () => {
  const mockResults = [
    {
      strategy: 'random',
      coverage_ratio: 0.725,
      connectivity_ratio: 0.821,
      avg_energy: 0.5432,
      compute_time_seconds: 0.005,
    },
    {
      strategy: 'grid',
      coverage_ratio: 0.812,
      connectivity_ratio: 0.950,
      avg_energy: 0.6210,
      compute_time_seconds: 0.012,
    },
    {
      strategy: 'pso',
      coverage_ratio: 0.914,
      connectivity_ratio: 0.982,
      avg_energy: 0.4501,
      compute_time_seconds: 1.250,
    },
    {
      strategy: 'pso_vdcoa',
      coverage_ratio: 0.942,
      connectivity_ratio: 0.995,
      avg_energy: 0.4610,
      compute_time_seconds: 1.543,
    },
  ];

  it('renders a table containing all 4 strategy rows', () => {
    render(<ComparisonTable results={mockResults} activeStrategy="pso" />);

    expect(screen.getByTestId('row-random')).toBeInTheDocument();
    expect(screen.getByTestId('row-grid')).toBeInTheDocument();
    expect(screen.getByTestId('row-pso')).toBeInTheDocument();
    expect(screen.getByTestId('row-pso_vdcoa')).toBeInTheDocument();

    expect(screen.getByText('Random Placement')).toBeInTheDocument();
    expect(screen.getByText('Grid Placement')).toBeInTheDocument();
    expect(screen.getByText('Standard PSO Swarm')).toBeInTheDocument();
    expect(screen.getByText('PSO-VDCOA Hybrid')).toBeInTheDocument();
  });

  it('highlights the active strategy row and shows the Active badge', () => {
    render(<ComparisonTable results={mockResults} activeStrategy="pso" />);

    const psoRow = screen.getByTestId('row-pso');
    expect(psoRow).toHaveClass('row-active');
    expect(psoRow.style.background).toContain('rgba(99, 102, 241, 0.08)');

    const randomRow = screen.getByTestId('row-random');
    expect(randomRow).not.toHaveClass('row-active');

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('formats metric values correctly (percentage, J, and s)', () => {
    render(<ComparisonTable results={mockResults} activeStrategy="pso" />);

    // Random row formats:
    // coverage_ratio: 0.725 -> 72.5%
    // connectivity_ratio: 0.821 -> 82.1%
    // avg_energy: 0.5432 -> 0.543 J
    // compute_time: 0.005 -> 0.005s
    expect(screen.getByText('72.5%')).toBeInTheDocument();
    expect(screen.getByText('82.1%')).toBeInTheDocument();
    expect(screen.getByText('0.543 J')).toBeInTheDocument();
    expect(screen.getByText('0.005s')).toBeInTheDocument();
  });

  it('applies styling to the best metrics dynamically', () => {
    render(<ComparisonTable results={mockResults} activeStrategy="pso" />);

    // Best coverage: pso_vdcoa (94.2%)
    // Best connectivity: pso_vdcoa (99.5%)
    // Best energy: grid (0.621 J, higher is better)
    // Best compute time: random (0.005s)

    const ccell = screen.getByText(/94.2%/);
    expect(ccell.style.color).toBe('var(--color-success)');
    expect(ccell.textContent).toContain('★');

    const ecell = screen.getByText(/0.621 J/);
    expect(ecell.style.color).toBe('var(--color-success)');
    expect(ecell.textContent).toContain('★');

    const tcell = screen.getByText(/0.005s/);
    expect(tcell.style.color).toBe('var(--color-success)');
    expect(tcell.textContent).toContain('★');
  });
});
