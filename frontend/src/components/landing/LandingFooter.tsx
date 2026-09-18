import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, ShieldCheck } from 'lucide-react';

export function LandingFooter() {
  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <footer className="bg-white border-t border-slate-200 py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          
          {/* Brand & Wordmark */}
          <div className="flex flex-col items-center md:items-start text-center md:text-left">
            <div className="flex items-center gap-2.5">
              <img src="/logo.png" alt="GridWise Logo" className="h-7 w-7 object-contain" />
              <span className="text-lg font-bold text-slate-900 tracking-tight">GridWise</span>
            </div>
            <p className="mt-2 text-xs text-slate-500 max-w-xs leading-relaxed">
              AI-powered campus energy optimization and deterministic microgrid dispatch engine.
            </p>
            <p className="mt-1 text-[11px] font-medium text-green-700">
              Team CISNEXUS • BUP CSE FEST 2026
            </p>
          </div>

          {/* Quick Navigation Links */}
          <div className="flex flex-wrap justify-center gap-6 text-xs font-medium text-slate-600">
            <Link to="/dashboard" className="hover:text-green-700 transition-colors">
              Dashboard
            </Link>
            <Link to="/optimize" className="hover:text-green-700 transition-colors">
              Optimize Energy
            </Link>
            <button onClick={() => scrollToSection('how-it-works')} className="hover:text-green-700 transition-colors cursor-pointer">
              How It Works
            </button>
            <button onClick={() => scrollToSection('energy-system')} className="hover:text-green-700 transition-colors cursor-pointer">
              Energy System
            </button>
            <button onClick={() => scrollToSection('capabilities')} className="hover:text-green-700 transition-colors cursor-pointer">
              Capabilities
            </button>
            <button onClick={() => scrollToSection('team')} className="hover:text-green-700 transition-colors cursor-pointer">
              Team
            </button>
          </div>

          {/* GitHub Project Link & Status */}
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/Joy185c/bup_project"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            >
              <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>GitHub Repository</span>
            </a>
          </div>

        </div>

        {/* Bottom copyright line */}
        <div className="mt-8 pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-400 gap-2">
          <span>&copy; {new Date().getFullYear()} GridWise • All rights reserved.</span>
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-green-600" />
            Deterministic Mixed-Integer Linear Programming Engine
          </span>
        </div>
      </div>
    </footer>
  );
}
