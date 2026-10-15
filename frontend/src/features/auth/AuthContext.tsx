import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../../types';
import { authApi } from '../../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: { email: string; password: string; full_name: string; role?: UserRole }) => Promise<void>;
  logout: () => void;
  loginAsDemo: (role: 'ADMIN' | 'SUPPORT_AGENT' | 'SUPPORT_ENGINEER' | 'PASSENGER' | 'REQUESTER') => Promise<void>;
  isAdmin: boolean;
  isSupport: boolean;
  isPassenger: boolean;
  isRequester: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('aero_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('aero_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        try {
          const freshUser = await authApi.getMe();
          setUser(freshUser);
          localStorage.setItem('aero_user', JSON.stringify(freshUser));
        } catch (err: any) {
          if (err.response?.status === 401) {
            logout();
          }
        }
      }
      setLoading(false);
    };
    verifyToken();
  }, [token]);

  const login = async (email: string, password: string) => {
    const data = await authApi.login({ email, password });
    localStorage.setItem('aero_token', data.access_token);
    localStorage.setItem('aero_user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  };

  const register = async (payload: { email: string; password: string; full_name: string; role?: UserRole }) => {
    const data = await authApi.register(payload);
    localStorage.setItem('aero_token', data.access_token);
    localStorage.setItem('aero_user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  };

  const logout = () => {
    authApi.logout();
    setToken(null);
    setUser(null);
  };

  const loginAsDemo = async (role: 'ADMIN' | 'SUPPORT_AGENT' | 'SUPPORT_ENGINEER' | 'PASSENGER' | 'REQUESTER') => {
    let email = 'admin@aeroassistant.com';
    let pass = 'AdminPass123!';
    if (role === 'SUPPORT_AGENT' || role === 'SUPPORT_ENGINEER') {
      email = 'engineer@aeroassistant.com';
      pass = 'EngineerPass123!';
    } else if (role === 'PASSENGER' || role === 'REQUESTER') {
      email = 'passenger@aeroassistant.com';
      pass = 'PassengerPass123!';
    }
    await login(email, pass);
  };

  const roleStr = user?.role ? String(user.role).trim().toUpperCase() : '';
  const isAdmin = roleStr === 'ADMIN';
  const isSupport = roleStr === 'ADMIN' || roleStr === 'SUPPORT_AGENT' || roleStr === 'SUPPORT_ENGINEER';
  const isPassenger = roleStr === 'PASSENGER' || roleStr === 'REQUESTER';
  const isRequester = isPassenger;


  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        loginAsDemo,
        isAdmin,
        isSupport,
        isPassenger,
        isRequester,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
