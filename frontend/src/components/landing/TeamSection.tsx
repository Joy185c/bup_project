import React from 'react';
import { Users, Award, ShieldCheck } from 'lucide-react';
import { teamMembers } from '../../data/teamData';

export function TeamSection() {
  return (
    <section id="team" className="py-16 sm:py-24 bg-slate-50 border-t border-slate-200/80 scroll-mt-18">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-800 border border-green-200">
            <Users className="h-3.5 w-3.5 text-green-700" />
            Team CISNEXUS
          </span>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
            Meet the Team
          </h2>
          <p className="mt-4 text-base text-slate-600 leading-relaxed">
            Built by a team passionate about AI, optimization, and smarter campus energy.
          </p>
        </div>

        {/* 4-Card Responsive Grid: Desktop 4 in a row, Tablet 2x2, Mobile 1 col */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          {teamMembers.map((member, index) => (
            <div
              key={member.name}
              className="group relative flex flex-col justify-between rounded-2xl bg-white p-6 border border-slate-200/90 shadow-xs hover:shadow-xl hover:border-green-400 hover:-translate-y-1 transition-all duration-300"
            >
              <div>
                {/* Photo Container with subtle zoom effect */}
                <div className="relative mx-auto mb-5 h-44 w-44 sm:h-48 sm:w-48 overflow-hidden rounded-2xl bg-slate-100 border-2 border-slate-200/80 group-hover:border-green-600 shadow-sm transition-colors duration-300">
                  <img
                    src={member.image}
                    alt={`${member.name} - ${member.role}`}
                    loading="lazy"
                    className="h-full w-full object-cover object-top transition-transform duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/20 to-transparent pointer-events-none" />
                </div>

                {/* Member Info */}
                <div className="text-center">
                  <h3 className="text-lg font-bold text-slate-900 group-hover:text-green-800 transition-colors">
                    {member.name}
                  </h3>
                  
                  <p className="mt-1 text-xs font-semibold text-green-700 leading-snug">
                    {member.role}
                  </p>

                  <p className="mt-3 text-xs text-slate-600 leading-relaxed">
                    {member.description}
                  </p>
                </div>
              </div>

              {/* Focus Area Tag */}
              {member.focusArea && (
                <div className="mt-5 pt-3 border-t border-slate-100 text-center">
                  <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-medium text-slate-600 group-hover:bg-green-50 group-hover:text-green-800 transition-colors">
                    <Award className="h-3 w-3 text-green-600" />
                    <span>{member.focusArea}</span>
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Team Philosophy Note */}
        <div className="mt-12 text-center text-xs text-slate-500 max-w-xl mx-auto flex items-center justify-center gap-2">
          <ShieldCheck className="h-4 w-4 text-green-600 shrink-0" />
          <span>Developed with zero-trust safety principles for the BUP CSE FEST 2026 Hackathon Challenge.</span>
        </div>

      </div>
    </section>
  );
}
