import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserProfile, UserRole } from '../types';
import { INITIAL_USER, ADMIN_USER, GUEST_USER } from '../data/mockData';
import { api } from '../services/api';

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole | null;
  token: string | null;
  isAuthenticated: boolean;
  loginCitizen: (mobile: string, otp: string) => Promise<{ success: boolean; error?: string }>;
  loginAdmin: (idOrEmail: string, password: string) => Promise<{ success: boolean; error?: string }>;
  loginGuest: () => Promise<void>;
  logout: () => void;
  updateUserProfile: (updates: Partial<UserProfile>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'jansamadhan_jwt';
const USER_KEY = 'jansamadhan_user';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    const savedUser = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch (e) {
        return null;
      }
    }
    return null;
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY) || null;
  });

  const role = user ? user.role : null;
  const isAuthenticated = !!token && !!user;

  // Sync with backend /auth/me on mount
  useEffect(() => {
    if (token) {
      api.getMe()
        .then(u => {
          setUser(u);
          if (u.role === 'guest') {
            sessionStorage.setItem(USER_KEY, JSON.stringify(u));
          } else {
            localStorage.setItem(USER_KEY, JSON.stringify(u));
          }
        })
        .catch(() => {
          // If offline or 401, handle appropriately
        });
    }
  }, [token]);

  const saveSession = (newUser: UserProfile, jwtToken: string) => {
    // Clear any previous user's data before saving new session
    localStorage.removeItem('jansamadhan_complaints');
    localStorage.removeItem('jansamadhan_notifications');
    sessionStorage.removeItem('jansamadhan_complaints');
    sessionStorage.removeItem('jansamadhan_notifications');

    setUser(newUser);
    setToken(jwtToken);
    if (newUser.role === 'guest') {
      sessionStorage.setItem(USER_KEY, JSON.stringify(newUser));
      sessionStorage.setItem(TOKEN_KEY, jwtToken);
    } else {
      localStorage.setItem(USER_KEY, JSON.stringify(newUser));
      localStorage.setItem(TOKEN_KEY, jwtToken);
    }
  };

  const loginCitizen = async (mobile: string, otp: string): Promise<{ success: boolean; error?: string }> => {
    // Clear state before login
    setUser(null);
    setToken(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('jansamadhan_complaints');
    localStorage.removeItem('jansamadhan_notifications');
    sessionStorage.clear();

    try {
      const res = await api.verifyOtp(mobile, otp);
      saveSession(res.user, res.access_token);
      return { success: true };
    } catch (e: any) {
      // Fallback to local verification if backend unreachable
      const cleanMobile = mobile.replace(/\D/g, '');
      if (!/^[6-9]\d{9}$/.test(cleanMobile)) {
        return { success: false, error: 'Mobile number must be 10 digits starting with 6-9.' };
      }
      if (otp !== '123456') {
        return { success: false, error: 'Invalid OTP. For demonstration, use mock code 123456.' };
      }
      const isRani = cleanMobile === '9876543210';
      const citizenUser: UserProfile = isRani
        ? { ...INITIAL_USER, phone: cleanMobile }
        : {
            id: `usr_${cleanMobile}`,
            name: '',
            phone: cleanMobile,
            role: 'citizen',
            district: '',
            state: 'Odisha',
            language: 'en',
          };
      saveSession(citizenUser, `mock_jwt_citizen_${cleanMobile}`);
      return { success: true };
    }
  };

  const loginAdmin = async (idOrEmail: string, password: string): Promise<{ success: boolean; error?: string }> => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('jansamadhan_complaints');
    localStorage.removeItem('jansamadhan_notifications');
    sessionStorage.clear();

    try {
      const res = await api.adminLogin(idOrEmail, password);
      saveSession(res.user, res.access_token);
      return { success: true };
    } catch (e: any) {
      if (!idOrEmail.trim() || !password.trim()) {
        return { success: false, error: 'Please enter both Employee ID/Email and password.' };
      }
      const adminUser: UserProfile = { ...ADMIN_USER, employeeId: idOrEmail };
      saveSession(adminUser, `mock_jwt_admin_${Date.now()}`);
      return { success: true };
    }
  };

  const loginGuest = async () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('jansamadhan_complaints');
    localStorage.removeItem('jansamadhan_notifications');
    sessionStorage.clear();

    try {
      const res = await api.guestLogin();
      saveSession(res.user, res.access_token);
    } catch (e) {
      const guestUser: UserProfile = {
        id: `GUEST-${Date.now().toString(36)}`,
        name: 'Guest Citizen',
        phone: '',
        role: 'guest',
        language: 'en',
      };
      const guestToken = `mock_jwt_guest_${Date.now()}`;
      saveSession(guestUser, guestToken);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('jansamadhan_complaints');
    localStorage.removeItem('jansamadhan_notifications');
    localStorage.removeItem('jansamadhan_chat_session');
    sessionStorage.clear();
  };

  const updateUserProfile = async (updates: Partial<UserProfile>) => {
    if (!user) return;
    try {
      const updated = await api.updateProfile(updates);
      setUser(updated);
      localStorage.setItem(USER_KEY, JSON.stringify(updated));
    } catch (e) {
      const updated = { ...user, ...updates };
      setUser(updated);
      localStorage.setItem(USER_KEY, JSON.stringify(updated));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        token,
        isAuthenticated,
        loginCitizen,
        loginAdmin,
        loginGuest,
        logout,
        updateUserProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
