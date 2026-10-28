import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { FlightBackground } from '../common/FlightBackground';

export const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col font-sans text-slate-100 relative selection:bg-sky-500/30">
      {/* Aviation Ambient Motion Background */}
      <FlightBackground variant="full" showRadar={true} />

      <Navbar />
      <div className="flex flex-1 overflow-hidden relative z-10">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-5 md:p-8 relative bg-[#FFFFFF]">
          <div className="max-w-7xl mx-auto animate-fade-in-up">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
