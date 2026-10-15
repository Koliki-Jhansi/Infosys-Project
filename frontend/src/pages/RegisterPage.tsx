import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import { Plane, Lock, Mail, User as UserIcon, ArrowRight, AlertCircle, Shield, Eye, EyeOff, Sparkles } from 'lucide-react';
import { UserRole } from '../types';
import { getApiErrorMessage } from '../services/api';
import { FlightBackground } from '../components/common/FlightBackground';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<UserRole>('REQUESTER');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    setError('');
    setLoading(true);
    try {
      await register({ email: email.trim(), password, full_name: fullName.trim(), role });
      navigate('/home');
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Registration failed. Please check your information and try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden selection:bg-sky-500/30">
      {/* Moving Aviation Background */}
      <FlightBackground variant="full" showRadar={true} />

      <div className="max-w-md w-full aviation-glass-card rounded-2xl p-8 shadow-2xl relative z-10 animate-fade-in-up border border-sky-500/20">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-600 via-blue-600 to-cyan-500 shadow-xl shadow-sky-500/30 text-white mb-4 animate-flight-float">
            <Plane className="w-7 h-7 -rotate-45" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-['Outfit']">
            Create Account
          </h1>
          <p className="text-xs text-slate-400 mt-1.5 font-['Inter']">
            Join AeroAssist AI Airline Operations & Passenger Platform
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5 animate-scale-in">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 font-['Outfit']">
              Full Name
            </label>
            <div className="relative">
              <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Smith"
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-500/20 transition-all duration-200"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 font-['Outfit']">
              Work / Passenger Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jane@aeroassistant.com"
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-500/20 transition-all duration-200"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 font-['Outfit']">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-11 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-500/20 transition-all duration-200"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-200 transition-colors"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 font-['Outfit']">
              Account Role
            </label>
            <div className="relative">
              <Shield className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5 pointer-events-none" />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-500/20 transition-all duration-200 appearance-none cursor-pointer"
              >
                <option value="REQUESTER">Passenger / Ticket Requester</option>
                <option value="PASSENGER">Frequent Flyer / Passenger</option>
                <option value="SUPPORT_AGENT">Airline Support Agent (Tier 1)</option>
                <option value="SUPPORT_ENGINEER">Support Systems Engineer (Tier 2)</option>
                <option value="ADMIN">Airline Operations Admin</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-gradient-to-r from-sky-600 via-blue-600 to-sky-500 hover:from-sky-500 hover:to-blue-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-sky-600/30 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 mt-6 btn-aviation"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Creating Account...</span>
              </>
            ) : (
              <>
                <span>Complete Registration</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-xs text-slate-400 mt-6 font-['Inter']">
          Already registered?{' '}
          <Link to="/login" className="text-sky-400 hover:text-sky-300 font-semibold hover:underline">
            Sign In here
          </Link>
          {' · '}
          <Link to="/welcome" className="text-slate-400 hover:text-slate-200 hover:underline">
            Back to Welcome
          </Link>
        </p>
      </div>
    </div>
  );
};
