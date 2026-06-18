import React, { useState, useRef } from 'react';
import { useConfigStore } from '../../store/configStore';
import Button from '../shared/Button';

export default function GridPainter() {
  const { config, paintedCells, toggleCell, clearGrid } = useConfigStore();
  const { area, cell_size } = config;
  const [paintMode, setPaintMode] = useState('restricted'); // 'restricted', 'non_critical', 'clear'
  const isMouseDown = useRef(false);

  const cols = Math.floor(area.width / cell_size) || 0;
  const rows = Math.floor(area.height / cell_size) || 0;
  const totalCells = cols * rows;

  const handleCellInteraction = (col, row) => {
    if (paintMode === 'clear') {
      const cellKey = `${col},${row}`;
      if (paintedCells[cellKey]) {
        toggleCell(col, row, paintedCells[cellKey]);
      }
    } else {
      toggleCell(col, row, paintMode);
    }
  };

  const handleMouseDown = (col, row) => {
    isMouseDown.current = true;
    handleCellInteraction(col, row);
  };

  const handleMouseEnter = (col, row) => {
    if (isMouseDown.current) {
      handleCellInteraction(col, row);
    }
  };

  const handleMouseUp = () => {
    isMouseDown.current = false;
  };

  React.useEffect(() => {
    const handleGlobalMouseUp = () => {
      isMouseDown.current = false;
    };
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, []);

  const maxCellsToRender = 1600; // max grid 40x40 for fluidity
  const isGridTooLarge = totalCells > maxCellsToRender;

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', userSelect: 'none' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.1rem', fontWeight: 600 }}>
          Grid Painter
        </h3>
        <Button variant="secondary" onClick={clearGrid} style={{ padding: '2px 8px', fontSize: '0.75rem' }}>
          Clear All
        </Button>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => setPaintMode('restricted')}
          style={{
            flex: 1,
            padding: '6px 12px',
            fontSize: '0.8rem',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            cursor: 'pointer',
            background: paintMode === 'restricted' ? 'var(--color-danger)' : 'rgba(244, 63, 94, 0.15)',
            color: '#fff',
            fontWeight: 600,
            transition: 'all var(--transition-fast)'
          }}
        >
          Restricted Area (RA)
        </button>
        <button
          type="button"
          onClick={() => setPaintMode('non_critical')}
          style={{
            flex: 1,
            padding: '6px 12px',
            fontSize: '0.8rem',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            cursor: 'pointer',
            background: paintMode === 'non_critical' ? 'var(--color-info)' : 'rgba(14, 165, 233, 0.15)',
            color: '#fff',
            fontWeight: 600,
            transition: 'all var(--transition-fast)'
          }}
        >
          Non-Critical (NCA)
        </button>
        <button
          type="button"
          onClick={() => setPaintMode('clear')}
          style={{
            flex: 1,
            padding: '6px 12px',
            fontSize: '0.8rem',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            cursor: 'pointer',
            background: paintMode === 'clear' ? 'var(--text-muted)' : 'rgba(100, 116, 139, 0.15)',
            color: '#fff',
            fontWeight: 600,
            transition: 'all var(--transition-fast)'
          }}
        >
          Eraser
        </button>
      </div>

      {isGridTooLarge ? (
        <div style={{
          padding: '1rem',
          background: 'rgba(251, 191, 36, 0.08)',
          border: '1px solid rgba(251, 191, 36, 0.2)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.85rem',
          textAlign: 'center',
          color: 'var(--color-warning)'
        }}>
          Grid size ({cols} &times; {rows} = {totalCells} cells) is too large to paint interactively.
          Please increase the Grid Resolution (e.g. 5.0m) to enable painting.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'center' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${cols}, 1fr)`,
              gap: '2px',
              width: '100%',
              maxWidth: '320px',
              aspectRatio: `${cols} / ${rows}`,
              background: 'rgba(0,0,0,0.4)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              padding: '4px',
              cursor: 'crosshair'
            }}
          >
            {Array.from({ length: rows }).map((_, r) => {
              const rowIdx = rows - 1 - r;
              return Array.from({ length: cols }).map((__, colIdx) => {
                const key = `${colIdx},${rowIdx}`;
                const cellType = paintedCells[key];

                let bg = 'rgba(255,255,255,0.02)';
                if (cellType === 'restricted') {
                  bg = 'var(--color-danger)';
                } else if (cellType === 'non_critical') {
                  bg = 'var(--color-info)';
                }

                return (
                  <div
                    key={key}
                    data-testid={`cell-${colIdx}-${rowIdx}`}
                    onMouseDown={() => handleMouseDown(colIdx, rowIdx)}
                    onMouseEnter={() => handleMouseEnter(colIdx, rowIdx)}
                    style={{
                      background: bg,
                      borderRadius: '1px',
                      transition: 'background-color 0.1s ease',
                      border: '0.5px solid rgba(255,255,255,0.02)',
                    }}
                  />
                );
              });
            })}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Drag mouse over cells to paint zones.
          </span>
        </div>
      )}
    </div>
  );
}
