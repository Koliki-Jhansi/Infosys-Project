import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import {
  Home,
  PlusCircle,
  Inbox,
  Sparkles,
  GitBranch,
  BookOpen,
  BarChart3,
  Settings,
  ShieldCheck,
  Plane,
  ChevronLeft,
  ChevronRight,
  Radio,
  Clock,
  Layers,
  Shield
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { label: 'Home', to: '/home', icon: Home, badge: null },
    { label: 'New Ticket', to: '/tickets/new', icon: PlusCircle, badge: 'PNR' },
    { label: 'All Tickets', to: '/tickets', icon: Inbox, badge: null },
    { label: 'AI Solution', to: '/ai-solution', icon: Sparkles, badge: 'RAG' },
    { label: 'Multi-Agent Workflow', to: '/multi-agent-workflow', icon: GitBranch, badge: '5-Agent' },
    { label: 'Human Review Queue', to: '/reviews', icon: Shield, badge: 'Gate' },
    { label: 'Jira Cloud Sync', to: '/jira', icon: Layers, badge: 'REST' },
    { label: 'Knowledge Base', to: '/knowledge-base', icon: BookOpen, badge: null },
    { label: 'AI Analytics', to: '/analytics', icon: BarChart3, badge: 'Live' },
    { label: 'Settings', to: '/settings', icon: Settings, badge: null },
  ];

  return (
    <aside
      className={`bg-slate-950/80 backdrop-blur-xl border-r border-sky-500/15 flex flex-col justify-between p-3.5 flex-shrink-0 min-h-[calc(100vh-4rem)] transition-all duration-300 z-30 select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      <div className="space-y-5">
        {/* Section Heading & Collapse Toggle */}
        <div className="flex items-center justify-between px-2.5 pt-1">
          {!collapsed && (
            <p className="text-[10px] font-bold uppercase tracking-wider text-sky-400/80 font-['Outfit'] flex items-center gap-1.5">
              <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
              Flight Ops Menu
            </p>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors ml-auto"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-sky-600/25 via-blue-600/15 to-transparent text-white font-semibold border-l-2 border-sky-400 shadow-sm shadow-sky-500/10'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 hover:translate-x-0.5'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon
                    className={`w-4 h-4 flex-shrink-0 transition-transform duration-200 group-hover:scale-110 ${
                      isActive ? 'text-sky-400 drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]' : 'text-slate-400 group-hover:text-sky-300'
                    }`}
                  />
                  {!collapsed && (
                    <span className="truncate font-['Inter'] flex-1">{item.label}</span>
                  )}
                  {!collapsed && item.badge && (
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded-md font-mono font-semibold ${
                        isActive
                          ? 'bg-sky-500/25 text-sky-200 border border-sky-400/30'
                          : 'bg-slate-800 text-slate-400 border border-slate-700/60'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Airport Flight Support Guardrail Card */}
        {!collapsed && (
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-3.5 border border-sky-500/20 text-xs text-slate-300 space-y-2.5 shadow-md shadow-black/40 group hover:border-sky-500/35 transition-all">
            {/* Ambient accent light */}
            <div className="absolute -top-10 -right-10 w-24 h-24 bg-sky-500/10 rounded-full blur-xl pointer-events-none group-hover:bg-sky-500/20 transition-all" />

            <div className="flex items-center justify-between text-sky-400 font-semibold font-['Outfit']">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                <span>Passenger Safety SLA</span>
              </div>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed font-['Inter']">
              Confidence &lt; 70% or sensitive claims auto-route directly to human agents.
            </p>

            <div className="pt-2 flex items-center justify-between text-[11px] font-mono text-slate-400 border-t border-slate-800/80">
              <span className="text-slate-400">Confidence Gate:</span>
              <span className="text-emerald-400 font-bold font-mono tracking-tight bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                &ge; 70.0%
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Footer System Status */}
      <div className="pt-3 border-t border-sky-500/10 text-slate-400 text-xs flex items-center justify-between px-1">
        {!collapsed ? (
          <>
            <div className="flex items-center gap-2 text-slate-300 font-medium">
              <div className="w-5 h-5 rounded-lg bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
                <Plane className="w-3 h-3 -rotate-45" />
              </div>
              <span className="text-[11px] font-['Outfit'] font-semibold">ATC Dispatch</span>
            </div>
            <span className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              PORT 8081
            </span>
          </>
        ) : (
          <div className="mx-auto" title="Backend connected on port 8081">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 block animate-pulse" />
          </div>
        )}
      </div>
    </aside>
  );
};
