import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ConvergenceChart from '../src/components/ConvergenceChart/ConvergenceChart';

// Mock Recharts to extract props passed to LineChart during testing
vi.mock('recharts', () => {
  return {
    ResponsiveContainer: ({ children }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
    LineChart: ({ data, children }) => (
      <div data-testid="line-chart" data-chart-data={JSON.stringify(data)}>
        {children}
      </div>
    ),
    Line: () => <div data-testid="line" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: () => <div data-testid="y-axis" />,
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    Tooltip: () => <div data-testid="tooltip" />,
  };
});

describe('ConvergenceChart Component', () => {
  it('renders an empty state when no data is provided', () => {
    render(<ConvergenceChart data={[]} />);
    expect(
      screen.getByText(/No convergence data available yet/i)
    ).toBeDefined();
  });

  it('passes the correct data shape to Recharts LineChart', () => {
    const testData = [
      { iteration: 0, fitness: 0.85 },
      { iteration: 1, fitness: 0.82 },
      { iteration: 2, fitness: 0.79 },
    ];

    render(<ConvergenceChart data={testData} />);
    const chart = screen.getByTestId('line-chart');
    const passedData = JSON.parse(chart.getAttribute('data-chart-data'));

    expect(passedData).toEqual(testData);
    expect(passedData).toHaveLength(3);
    expect(passedData[0]).toHaveProperty('iteration');
    expect(passedData[0]).toHaveProperty('fitness');
    expect(passedData[0].iteration).toBe(0);
    expect(passedData[0].fitness).toBe(0.85);
  });
});
