import React from 'react';
import { useAuth } from '../../features/auth/AuthContext';
import { Plane, UserCircle, LogOut, Sparkles, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Navbar: React.FC = () => {
  const { user, logout, loginAsDemo, isAdmin, isSupport, isPassenger } = useAuth();

  return (
    <header className="h-16 bg-slate-950/80 backdrop-blur-xl border-b border-sky-500/15 text-white flex items-center justify-between px-6 sticky top-0 z-40 shadow-lg shadow-black/40">
      <Link to="/home" className="flex items-center gap-3.5 group">
        <div className="relative">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 via-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-sky-500/25 text-white font-bold transition-all duration-300 group-hover:scale-105 group-hover:shadow-sky-400/35">
            <Plane className="w-5 h-5 -rotate-45 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-slate-950 shadow-sm shadow-emerald-500/50" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-tight text-white font-['Outfit']">
              AeroAssist <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-cyan-300 to-blue-400 font-extrabold">AI</span>
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/25 flex items-center gap-1 shadow-sm">
              <Sparkles className="w-2.5 h-2.5 text-sky-400 animate-pulse" /> Ops Console
            </span>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:flex items-center gap-1.5 font-medium">
            <span>Enterprise Airline Dispatch</span>
            <span className="text-slate-600">•</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live v1.0
            </span>
          </p>
        </div>
      </Link>

      <div className="flex items-center gap-4">
        {/* Quick Demo Switcher */}
        <div className="hidden lg:flex items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-sky-500/20 text-xs text-slate-300 shadow-inner">
          <span className="px-2.5 text-slate-400 font-medium text-[11px] flex items-center gap-1">
            <Activity className="w-3 h-3 text-sky-400" /> Persona:
          </span>
          <button
            onClick={() => loginAsDemo('ADMIN')}
            className={`px-2.5 py-1 rounded-lg transition-all duration-200 text-xs ${
              isAdmin
                ? 'bg-gradient-to-r from-sky-600 to-blue-600 text-white font-semibold shadow-md shadow-sky-600/30'
                : 'hover:bg-slate-800 text-slate-300 hover:text-white'
            }`}
          >
            Admin
          </button>
          <button
            onClick={() => loginAsDemo('SUPPORT_AGENT')}
            className={`px-2.5 py-1 rounded-lg transition-all duration-200 text-xs ${
              !isAdmin && isSupport
                ? 'bg-gradient-to-r from-sky-600 to-blue-600 text-white font-semibold shadow-md shadow-sky-600/30'
                : 'hover:bg-slate-800 text-slate-300 hover:text-white'
            }`}
          >
            Support Agent
          </button>
          <button
            onClick={() => loginAsDemo('PASSENGER')}
            className={`px-2.5 py-1 rounded-lg transition-all duration-200 text-xs ${
              isPassenger
                ? 'bg-gradient-to-r from-sky-600 to-blue-600 text-white font-semibold shadow-md shadow-sky-600/30'
                : 'hover:bg-slate-800 text-slate-300 hover:text-white'
            }`}
          >
            Passenger
          </button>
        </div>

        {/* User Info & Logout */}
        {user && (
          <div className="flex items-center gap-3 border-l border-slate-800/80 pl-4">
            <div className="flex flex-col text-right">
              <span className="text-xs font-semibold text-slate-100 font-['Outfit'] tracking-wide">{user.full_name}</span>
              <span className="text-[10px] text-sky-400 font-mono font-medium tracking-tight">
                {isAdmin ? 'OPS ADMINISTRATOR' : isPassenger ? 'PASSENGER (PNR)' : 'SUPPORT AGENT'}
              </span>
            </div>

            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-sky-500/25 flex items-center justify-center text-sky-300 shadow-sm shadow-sky-950">
                <UserCircle className="w-5 h-5" />
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 rounded-xl transition-all duration-200 ml-1"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

