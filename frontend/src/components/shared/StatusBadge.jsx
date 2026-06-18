import React from 'react';

export default function StatusBadge({ status }) {
  const normalized = (status || 'pending').toLowerCase();
  return (
    <span className={`badge badge-${normalized}`}>
      {normalized}
    </span>
  );
}
