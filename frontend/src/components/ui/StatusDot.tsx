import React from 'react';
import { cn } from '../../utils/cn';

interface StatusDotProps {
  status: 'online' | 'offline' | 'checking';
  className?: string;
}

export function StatusDot({ status, className }: StatusDotProps) {
  const colors = {
    online: 'bg-green-500',
    offline: 'bg-red-500',
    checking: 'bg-amber-500 animate-pulse',
  };

  return (
    <span className={cn('relative flex h-3 w-3', className)}>
      {status === 'online' && (
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
      )}
      <span className={cn('relative inline-flex rounded-full h-3 w-3', colors[status])}></span>
    </span>
  );
}
