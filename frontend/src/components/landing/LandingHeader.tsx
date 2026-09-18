import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Zap, Menu, X, ArrowRight, Activity } from 'lucide-react';
import { checkHealth } from '../../services/api';

export function LandingHeader() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const location = useLocation();

  useEffect(() => {
    let mounted = true;
    checkHealth().then((healthy) => {
      if (mounted) setIsHealthy(healthy);
    });
    return () => {
      mounted = false;
    };
  }, []);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobileMenuOpen]);

  const scrollToSection = (id: string) => {
    setIsMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/90 backdrop-blur-md transition-all">
      <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        
        {/* Brand / Logo */}
        <Link to="/" className="flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-green-600 rounded-lg p-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-50 border border-green-200 shadow-xs group-hover:border-green-300 transition-colors">
            <img src="/logo.png" alt="GridWise Logo" className="h-7 w-7 object-contain" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-slate-900">GridWise</span>
              <span className="hidden sm:inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800 border border-green-200">
                AI Microgrid
              </span>
            </div>
            <p className="text-[11px] font-medium text-slate-500 tracking-wide hidden sm:block">Campus Energy Optimization</p>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1 lg:gap-2">
          <Link
            to="/dashboard"
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-colors"
          >
            Dashboard
          </Link>
          <Link
            to="/optimize"
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-colors"
          >
            Optimize
          </Link>
          <button
            onClick={() => scrollToSection('how-it-works')}
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-colors cursor-pointer"
          >
            How It Works
          </button>
          <button
            onClick={() => scrollToSection('energy-system')}
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-colors cursor-pointer"
          >
            Energy System
          </button>
          <button
            onClick={() => scrollToSection('capabilities')}
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-colors cursor-pointer"
          >
            Capabilities
          </button>
          <button
            onClick={() => scrollToSection('team')}
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-colors cursor-pointer"
          >
            Team
          </button>
        </nav>

        {/* Right CTA Area */}
        <div className="hidden sm:flex items-center gap-3">
          {/* Health indicator badge */}
          <div className="hidden lg:flex items-center gap-1.5 rounded-full bg-slate-100/80 px-2.5 py-1 text-xs font-medium text-slate-600 border border-slate-200">
            <span
              className={`h-2 w-2 rounded-full ${
                isHealthy === null
                  ? 'bg-amber-400 animate-pulse'
                  : isHealthy
                  ? 'bg-green-500 animate-pulse'
                  : 'bg-red-500'
              }`}
            />
            <span>{isHealthy === null ? 'Engine Connecting' : isHealthy ? 'Solver Ready' : 'Offline'}</span>
          </div>

          <Link
            to="/optimize"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-green-700 px-4 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-green-800 focus:outline-none focus:ring-2 focus:ring-green-600 focus:ring-offset-2 transition-all active:scale-[0.98]"
          >
            <Zap className="h-4 w-4 fill-current text-green-200" />
            <span>Launch Optimizer</span>
          </Link>
        </div>

        {/* Mobile Hamburger Button */}
        <div className="flex sm:hidden items-center gap-2">
          <Link
            to="/optimize"
            className="inline-flex items-center justify-center rounded-lg bg-green-700 px-3 py-1.5 text-xs font-semibold text-white shadow-xs"
          >
            <Zap className="h-3.5 w-3.5 mr-1" />
            Launch
          </Link>
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(true)}
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-green-600"
            aria-label="Open navigation menu"
          >
            <Menu className="h-6 w-6" />
          </button>
        </div>

      </div>

      {/* Mobile Drawer Backdrop & Menu */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex justify-end">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setIsMobileMenuOpen(false)}
          />

          {/* Drawer Content */}
          <div className="relative z-10 w-full max-w-xs bg-white h-full shadow-2xl flex flex-col p-6 border-l border-slate-200 animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-5 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <img src="/logo.png" alt="GridWise Logo" className="h-8 w-8 object-contain" />
                <span className="font-bold text-slate-900 text-lg">GridWise</span>
              </div>
              <button
                type="button"
                onClick={() => setIsMobileMenuOpen(false)}
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-green-600"
                aria-label="Close navigation menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex flex-col gap-1.5 py-6 flex-1 overflow-y-auto">
              <Link
                to="/dashboard"
                onClick={() => setIsMobileMenuOpen(false)}
                className="flex items-center justify-between rounded-lg px-3 py-2.5 text-base font-medium text-slate-700 hover:bg-green-50 hover:text-green-800"
              >
                <span>Dashboard</span>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </Link>
              <Link
                to="/optimize"
                onClick={() => setIsMobileMenuOpen(false)}
                className="flex items-center justify-between rounded-lg px-3 py-2.5 text-base font-medium text-slate-700 hover:bg-green-50 hover:text-green-800"
              >
                <span>Optimize Energy</span>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </Link>
              <button
                onClick={() => scrollToSection('how-it-works')}
                className="flex items-center justify-between text-left rounded-lg px-3 py-2.5 text-base font-medium text-slate-700 hover:bg-green-50 hover:text-green-800 cursor-pointer"
              >
                <span>How It Works</span>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </button>
              <button
                onClick={() => scrollToSection('energy-system')}
                className="flex items-center justify-between text-left rounded-lg px-3 py-2.5 text-base font-medium text-slate-700 hover:bg-green-50 hover:text-green-800 cursor-pointer"
              >
                <span>Energy System</span>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </button>
              <button
                onClick={() => scrollToSection('capabilities')}
                className="flex items-center justify-between text-left rounded-lg px-3 py-2.5 text-base font-medium text-slate-700 hover:bg-green-50 hover:text-green-800 cursor-pointer"
              >
                <span>Capabilities</span>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </button>
              <button
                onClick={() => scrollToSection('team')}
                className="flex items-center justify-between text-left rounded-lg px-3 py-2.5 text-base font-medium text-slate-700 hover:bg-green-50 hover:text-green-800 cursor-pointer"
              >
                <span>Meet the Team</span>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </button>
            </div>

            <div className="pt-4 border-t border-slate-100 flex flex-col gap-3">
              <Link
                to="/optimize"
                onClick={() => setIsMobileMenuOpen(false)}
                className="flex items-center justify-center gap-2 rounded-xl bg-green-700 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-green-800"
              >
                <Zap className="h-4 w-4 fill-current text-green-200" />
                <span>Launch Optimizer</span>
              </Link>
              <p className="text-center text-xs text-slate-400">Team CISNEXUS • BUP CSE FEST 2026</p>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
