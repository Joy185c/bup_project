import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Home, LayoutDashboard, Zap, List, LineChart, History, Activity, X, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';
import { checkHealth } from '../../services/api';

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Optimize Energy', href: '/optimize', icon: Zap },
  { name: 'Energy Plan', href: '/plan', icon: List },
  { name: 'Analytics', href: '/analytics', icon: LineChart },
  { name: 'Optimization History', href: '/history', icon: History },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  // Prevent scrolling when mobile sidebar is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const [healthStatus, setHealthStatus] = useState<'checking' | 'healthy' | 'error'>('checking');

  useEffect(() => {
    let mounted = true;
    
    const verifyHealth = async () => {
      const isHealthy = await checkHealth();
      if (mounted) {
        setHealthStatus(isHealthy ? 'healthy' : 'error');
      }
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 30000);
    
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const sidebarContent = (
    <div className="flex h-full w-64 flex-col border-r border-slate-200 bg-white/75 backdrop-blur-md">
      <div className="flex h-16 shrink-0 items-center justify-between px-6">
        <div className="flex items-center h-full py-2">
          <img src="/logo.png" alt="Nexus" className="h-full object-contain max-h-12" />
        </div>
        {onClose && (
          <button 
            onClick={onClose}
            className="lg:hidden rounded-md p-2 text-slate-500 hover:bg-slate-100"
          >
            <X className="h-6 w-6" />
          </button>
        )}
      </div>
      <div className="flex flex-1 flex-col overflow-y-auto px-4 py-4">
        <nav className="flex-1 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={() => {
                if (onClose) onClose();
              }}
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
          {healthStatus === 'checking' && (
            <>
              <Loader2 className="mr-2 h-5 w-5 text-slate-400 animate-spin" />
              Checking System...
            </>
          )}
          {healthStatus === 'healthy' && (
            <>
              <Activity className="mr-2 h-5 w-5 text-green-500" />
              System Healthy
            </>
          )}
          {healthStatus === 'error' && (
            <>
              <AlertCircle className="mr-2 h-5 w-5 text-red-500" />
              System Offline
            </>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-slate-900/80 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <div 
        className={cn(
          "fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-in-out lg:static lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {sidebarContent}
      </div>
    </>
  );
}
