import React from 'react';
import { User, ChevronDown, Menu } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { NotificationBell } from './NotificationBell';

interface TopHeaderProps {
  onMenuClick?: () => void;
}

export function TopHeader({ onMenuClick }: TopHeaderProps) {
  const lastResult = useAppStore((state) => state.lastResult);

  return (
    <header className="relative z-30 flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white/85 backdrop-blur-md px-4 sm:px-6 lg:px-8">
      <div className="flex flex-1 items-center">
        {onMenuClick && (
          <button 
            onClick={onMenuClick}
            className="mr-4 rounded-md p-2 text-slate-500 hover:bg-slate-100 lg:hidden focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
        )}
        <h1 className="text-lg font-semibold text-slate-900 truncate">
          Campus Energy Control
        </h1>
        {lastResult && (
          <div className="ml-4 hidden sm:flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            Scenario: <span className="ml-1 text-slate-900 font-semibold truncate max-w-[150px]">{lastResult.scenario_id}</span>
          </div>
        )}
      </div>
      <div className="flex items-center space-x-2 sm:space-x-4 ml-4">
        <NotificationBell />
      </div>
    </header>
  );
}
