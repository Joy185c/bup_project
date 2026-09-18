import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopHeader } from './TopHeader';

export function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen font-sans text-slate-900 overflow-hidden relative bg-slate-100">
      {/* Subtle Premium Watermark Background */}
      <div 
        className="absolute inset-0 z-0 pointer-events-none opacity-[0.12] mix-blend-multiply"
        style={{
          backgroundImage: "url('/bg-watermark.png')",
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
      />
      
      {/* Sidebar */}
      <div className="relative z-20 h-full">
        <Sidebar isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />
      </div>

      <div className="flex flex-1 flex-col overflow-hidden w-full relative z-10">
        <TopHeader onMenuClick={() => setIsMobileMenuOpen(true)} />
        <main className="flex-1 overflow-y-auto bg-slate-50/85 backdrop-blur-sm p-4 sm:p-6 lg:p-8 w-full">
          <div className="mx-auto max-w-7xl flex flex-col min-h-full">
            <div className="flex-1 pb-8">
              <Outlet />
            </div>
            <footer className="pt-8 pb-2 border-t border-slate-200/60 text-center mt-auto">
              <p className="text-xs text-slate-400">
                Developed by <span className="font-semibold text-slate-500 tracking-wider">CISNEXUS</span>
              </p>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}
