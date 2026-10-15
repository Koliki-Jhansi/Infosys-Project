import React from 'react';

interface FlightBackgroundProps {
  variant?: 'minimal' | 'full' | 'hero';
  showRadar?: boolean;
}

export const FlightBackground: React.FC<FlightBackgroundProps> = ({
  variant = 'full',
  showRadar = true
}) => {
  return (
    <div
      className="fixed inset-0 pointer-events-none overflow-hidden z-0 select-none"
      aria-hidden="true"
    >
      {/* Dynamic Ambient Gradient Meshes */}
      <div className="absolute top-[-10%] left-[15%] w-[600px] h-[600px] bg-sky-600/10 rounded-full blur-[120px] animate-pulse-glow" />
      <div className="absolute bottom-[-10%] right-[10%] w-[550px] h-[550px] bg-blue-700/10 rounded-full blur-[140px] animate-flight-drift" />
      <div className="absolute top-[40%] right-[30%] w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-[100px]" />

      {/* Subtle Aviation Flight Grid */}
      <div className="absolute inset-0 bg-flight-grid opacity-60" />

      {/* Decorative Radar Sweep Element (Air Operations Theme) */}
      {showRadar && (
        <div className="absolute top-12 right-12 w-64 h-64 opacity-20 hidden lg:block">
          {/* Radar Circles */}
          <div className="absolute inset-0 rounded-full border border-sky-400/30" />
          <div className="absolute inset-8 rounded-full border border-sky-400/25" />
          <div className="absolute inset-16 rounded-full border border-sky-400/20" />
          <div className="absolute inset-24 rounded-full border border-sky-400/15" />
          {/* Crosshairs */}
          <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-sky-400/20" />
          <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-sky-400/20" />
          {/* Sweeping Needle */}
          <div className="absolute inset-0 animate-radar-sweep origin-center">
            <div className="w-1/2 h-1/2 origin-bottom-right bg-gradient-to-br from-cyan-400/30 to-transparent" />
          </div>
          {/* Blip */}
          <div className="absolute top-[28%] left-[65%] w-1.5 h-1.5 rounded-full bg-cyan-400 animate-radar-ping shadow-sm shadow-cyan-300" />
        </div>
      )}

      {/* Ambient Flight Trajectory SVG */}
      {variant !== 'minimal' && (
        <svg
          className="absolute inset-0 w-full h-full opacity-15"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M -100,200 Q 350,120 700,320 T 1500,220 T 2200,400"
            fill="none"
            stroke="url(#flightGrad)"
            strokeWidth="1.5"
            strokeDasharray="6 8"
            className="[animation:flight-dash_25s_linear_infinite]"
          />
          <path
            d="M -50,600 Q 400,750 900,500 T 1800,680"
            fill="none"
            stroke="url(#flightGrad2)"
            strokeWidth="1.2"
            strokeDasharray="4 6"
            className="[animation:flight-dash_35s_linear_infinite]"
          />
          <defs>
            <linearGradient id="flightGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0284c7" stopOpacity="0" />
              <stop offset="40%" stopColor="#38bdf8" stopOpacity="0.8" />
              <stop offset="80%" stopColor="#22d3ee" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#0284c7" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="flightGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0" />
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      )}
    </div>
  );
};
