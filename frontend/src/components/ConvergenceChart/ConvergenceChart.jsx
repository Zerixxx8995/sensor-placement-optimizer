import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

/**
 * ConvergenceChart
 * ----------------
 * Renders the fitness convergence curve of the active optimization run.
 * Accepts a pre-formatted array of { iteration: number, fitness: number } objects.
 *
 * Props
 * -----
 *  data  {Array}  Array of { iteration, fitness } data points.
 */
export default function ConvergenceChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="convergence-chart-empty">
        <span>No convergence data available yet. Waiting for run to start…</span>
      </div>
    );
  }

  // Bounding calculations for Y axis to keep values readable and tight
  const fitnesses = data.map((d) => d.fitness);
  const minFit = Math.min(...fitnesses);
  const maxFit = Math.max(...fitnesses);
  const padding = (maxFit - minFit) * 0.1 || 0.02;
  const yDomain = [
    Math.max(0, minFit - padding),
    Math.min(1.0, maxFit + padding),
  ];

  return (
    <div className="convergence-chart-card glass-card">
      <div style={{ marginBottom: '1rem' }}>
        <h3 className="chart-title">Fitness Convergence</h3>
        <p className="chart-subtitle">
          Objective function minimization progress over iterations
        </p>
      </div>

      <div style={{ width: '100%', height: 200, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 5, right: 5, left: -25, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255, 255, 255, 0.04)"
              vertical={false}
            />
            <XAxis
              dataKey="iteration"
              stroke="var(--text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              dy={10}
            />
            <YAxis
              stroke="var(--text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              domain={yDomain}
              tickFormatter={(val) => val.toFixed(3)}
              dx={-5}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div className="chart-tooltip">
                      <p className="tooltip-iter">Iteration {item.iteration}</p>
                      <p className="tooltip-fit">
                        Fitness:{' '}
                        <span className="value">{item.fitness.toFixed(5)}</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="monotone"
              dataKey="fitness"
              stroke="var(--color-primary)"
              strokeWidth={2}
              dot={false}
              activeDot={{
                r: 4,
                stroke: 'var(--color-primary)',
                strokeWidth: 2,
                fill: 'var(--text-primary)',
              }}
              isAnimationActive={false} // Disable active transition animations on updates for rendering performance
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
