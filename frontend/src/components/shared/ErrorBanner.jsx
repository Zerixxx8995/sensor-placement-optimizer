import React from 'react';

export default function ErrorBanner({ message, detail, onClose }) {
  if (!message) return null;

  return (
    <div style={{
      background: 'rgba(244, 63, 94, 0.15)',
      border: '1px solid rgba(244, 63, 94, 0.35)',
      borderRadius: 'var(--radius-md)',
      padding: '1rem',
      color: 'var(--text-primary)',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.5rem',
      position: 'relative',
      marginBottom: '1rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong style={{ color: 'var(--color-danger)' }}>Error</strong>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: '1.25rem',
              lineHeight: 1,
            }}
          >
            &times;
          </button>
        )}
      </div>
      <div>{message}</div>
      {detail && (
        <div style={{
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
          background: 'rgba(0, 0, 0, 0.25)',
          padding: '0.5rem',
          borderRadius: 'var(--radius-sm)',
          marginTop: '0.25rem',
          fontFamily: 'monospace',
          whiteSpace: 'pre-wrap',
        }}>
          {typeof detail === 'object' ? JSON.stringify(detail, null, 2) : detail}
        </div>
      )}
    </div>
  );
}
