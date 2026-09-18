import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, ArrowRight, ShieldCheck, Sparkles, Cpu, Layers } from 'lucide-react';
import { LandingHeader } from '../components/landing/LandingHeader';
import { HeroEnergyVisual } from '../components/landing/HeroEnergyVisual';
import { AIOperatorCard } from '../components/landing/AIOperatorCard';
import { HowItWorksSection } from '../components/landing/HowItWorksSection';
import { EnergySystemSection } from '../components/landing/EnergySystemSection';
import { CapabilityStrip } from '../components/landing/CapabilityStrip';
import { FinalCTASection } from '../components/landing/FinalCTASection';
import { TeamSection } from '../components/landing/TeamSection';
import { LandingFooter } from '../components/landing/LandingFooter';

export default function LandingPage() {
  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-green-100 selection:text-green-900">
      
      {/* Top Navigation */}
      <LandingHeader />

      {/* Main Landing Flow */}
      <main>
        
        {/* HERO SECTION */}
        <section className="relative pt-8 pb-16 sm:pt-14 sm:pb-24 lg:pt-20 overflow-hidden bg-gradient-to-b from-white via-white to-slate-50 border-b border-slate-200/80">
          
          {/* Subtle Accent Glow */}
          <div className="absolute top-0 right-1/4 -mt-24 h-96 w-96 rounded-full bg-green-50/70 blur-3xl pointer-events-none -z-10" />
          <div className="absolute top-1/2 left-0 -ml-24 h-72 w-72 rounded-full bg-emerald-50/60 blur-3xl pointer-events-none -z-10" />

          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
              
              {/* Hero Left Content */}
              <div className="lg:col-span-6 flex flex-col items-start text-left">
                
                {/* Microgrid badge */}
                <div className="inline-flex items-center gap-2 rounded-full bg-green-50 px-3 py-1.5 text-xs font-semibold text-green-800 border border-green-200/80 mb-6 shadow-2xs">
                  <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span>AI Energy Command Center • University Microgrids</span>
                </div>

                {/* Primary Headline */}
                <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl leading-[1.12]">
                  Optimize Campus Energy.{' '}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-700 via-green-600 to-emerald-700">
                    Intelligently.
                  </span>
                </h1>

                {/* Supporting Text */}
                <p className="mt-6 text-base sm:text-lg text-slate-600 leading-relaxed max-w-xl">
                  Turn operator instructions into safe, cost-efficient 24-hour energy schedules using AI, solar, battery, and grid optimization.
                </p>

                {/* Primary & Secondary CTAs */}
                <div className="mt-8 flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto">
                  <Link
                    to="/optimize"
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-green-700 px-7 py-3.5 text-base font-bold text-white shadow-md shadow-green-700/20 hover:bg-green-800 active:scale-[0.98] transition-all"
                  >
                    <Zap className="h-5 w-5 fill-current text-green-200" />
                    <span>⚡ Optimize Energy</span>
                  </Link>

                  <button
                    onClick={() => scrollToSection('how-it-works')}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-6 py-3.5 text-base font-semibold text-slate-700 border border-slate-300 hover:bg-slate-50 hover:text-slate-900 shadow-2xs transition-all cursor-pointer"
                  >
                    <span>How It Works</span>
                    <ArrowRight className="h-4 w-4 text-slate-400" />
                  </button>
                </div>

                {/* Trust & Architecture Pills */}
                <div className="mt-10 pt-6 border-t border-slate-100 flex flex-wrap items-center gap-4 text-xs font-medium text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="h-4 w-4 text-green-600" />
                    <span>13 Zero-Trust Guardrails</span>
                  </div>
                  <span className="text-slate-300">•</span>
                  <div className="flex items-center gap-1.5">
                    <Cpu className="h-4 w-4 text-green-600" />
                    <span>PuLP & CBC Solver</span>
                  </div>
                  <span className="text-slate-300">•</span>
                  <div className="flex items-center gap-1.5">
                    <Layers className="h-4 w-4 text-green-600" />
                    <span>24-Hour Plan Horizon</span>
                  </div>
                </div>

              </div>

              {/* Hero Right Visual: Energy System Simulation */}
              <div className="lg:col-span-6 w-full flex justify-center">
                <HeroEnergyVisual />
              </div>

            </div>
          </div>
        </section>

        {/* AI OPERATOR NOTE CARD DEMO SECTION */}
        <section className="py-14 sm:py-20 bg-slate-50">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mb-8">
              <span className="text-xs font-bold uppercase tracking-wider text-green-700 font-mono">
                Decoupled Intelligence in Action
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-1">
                How AI Converts Human Instructions into Mathematical Constraints
              </h2>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Campus operators speak naturally. The LLM translates text into typed directives, validated by zero-trust guardrails before solver execution.
              </p>
            </div>

            <AIOperatorCard />
          </div>
        </section>

        {/* HOW GRIDWISE WORKS (5-STEP PROCESS) */}
        <HowItWorksSection />

        {/* CAMPUS ENERGY ECOSYSTEM */}
        <EnergySystemSection />

        {/* CAPABILITY STRIP */}
        <CapabilityStrip />

        {/* FINAL CTA SECTION */}
        <FinalCTASection />

        {/* TEAM / DEVELOPERS SECTION */}
        <TeamSection />

      </main>

      {/* FOOTER */}
      <LandingFooter />

    </div>
  );
}
