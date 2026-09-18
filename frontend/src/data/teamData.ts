export interface TeamMember {
  name: string;
  role: string;
  image: string;
  description: string;
  focusArea?: string;
}

export const teamMembers: TeamMember[] = [
  {
    name: "Fayek Ahanaf",
    role: "Lead AI Engineer & System Architect",
    image: "/team/fayek-ahanaf.jpg",
    description: "Architected the zero-trust guardrails pipeline, strict prompt schema, and end-to-end FastAPI microgrid orchestration.",
    focusArea: "LLM Guardrails & API Architecture"
  },
  {
    name: "Joy Kumar Yuv",
    role: "Full Stack Engineer & Optimization Specialist",
    image: "/team/joy-sarker.jpg",
    description: "Engineered the Mixed-Integer Linear Programming (MILP) formulation with PuLP & CBC and full-stack system deployment.",
    focusArea: "MILP Solvers & Backend Systems"
  },
  {
    name: "Nafisa Tabassum",
    role: "Data Scientist & ML Research",
    image: "/team/nafisa-tabassum.png",
    description: "Spearheaded campus electricity load profiling, solar generation modeling, and statistical validation metrics.",
    focusArea: "Energy Modeling & Validation"
  },
  {
    name: "Atul Paul",
    role: "Frontend Developer & UI/UX Designer",
    image: "/team/atul-paul.png",
    description: "Designed and built the responsive command center dashboard, glassmorphic UI components, and real-time telemetry charts.",
    focusArea: "UI/UX & Interactive Telemetry"
  }
];
