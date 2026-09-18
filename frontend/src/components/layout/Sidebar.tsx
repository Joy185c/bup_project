import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Zap, List, LineChart, History, Activity } from 'lucide-react';
import { cn } from '../../utils/cn';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Optimize Energy', href: '/optimize', icon: Zap },
  { name: 'Energy Plan', href: '/plan', icon: List },
  { name: 'Analytics', href: '/analytics', icon: LineChart },
  { name: 'Optimization History', href: '/history', icon: History },
];

export function Sidebar() {
  return (
    <div className="flex h-full w-64 flex-col border-r border-slate-200 bg-white">
      <div className="flex h-16 shrink-0 items-center px-6">
        <Zap className="h-8 w-8 text-green-700" />
        <span className="ml-3 text-xl font-bold tracking-tight text-slate-900">GridWise</span>
      </div>
      <div className="flex flex-1 flex-col overflow-y-auto px-4 py-4">
        <nav className="flex-1 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  isActive
                    ? 'bg-green-50 text-green-700'
                    : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900',
                  'group flex items-center rounded-md px-2 py-2 text-sm font-medium transition-colors'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon
                    className={cn(
                      isActive ? 'text-green-700' : 'text-slate-400 group-hover:text-slate-500',
                      'mr-3 h-5 w-5 flex-shrink-0 transition-colors'
                    )}
                    aria-hidden="true"
                  />
                  {item.name}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="shrink-0 border-t border-slate-200 p-4">
        <div className="flex items-center text-sm font-medium text-slate-700">
          <Activity className="mr-2 h-5 w-5 text-green-500" />
          System Healthy
        </div>
      </div>
    </div>
  );
}
