import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Home,
  Bot,
  FileText,
  FilePlus2,
  Bell,
  User,
  LogOut,
  ShieldAlert,
  MapPin,
  BarChart3,
} from 'lucide-react';
import { Logo } from '../common/Logo';
import { BuildingIllustration } from '../common/BuildingIllustration';
import { useNotifications } from '../../context/NotificationContext';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

export const Sidebar: React.FC = () => {
  const { unreadCount } = useNotifications();
  const { role, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3.5 px-4 py-3 rounded-2xl text-sm font-semibold transition-all duration-200 group focus-ring ${
      isActive
        ? 'bg-cream-400 text-maroon-900 shadow-md translate-x-1 font-bold'
        : 'text-cream-200/90 hover:bg-maroon-700/70 hover:text-white'
    }`;

  return (
    <aside
      className="hidden md:flex flex-col justify-between w-64 lg:w-72 bg-maroon-800 text-white min-h-screen px-4 py-6 border-r border-maroon-900 relative overflow-hidden select-none"
      aria-label="Main Navigation"
    >
      <div className="relative z-10">
        {/* Logo at top */}
        <div className="px-2 mb-8">
          <Logo size="md" dark />
        </div>

        {/* Navigation list */}
        <nav className="space-y-1.5" aria-label="Sidebar Menu">
          <NavLink to="/dashboard" className={navItemClass}>
            <Home className="w-5 h-5 flex-shrink-0 text-current" />
            <span>{t('navDashboard')}</span>
          </NavLink>

          <NavLink to="/assistant" className={navItemClass}>
            <Bot className="w-5 h-5 flex-shrink-0 text-current" />
            <span>{t('navAIAssistant')}</span>
          </NavLink>

          <NavLink to="/complaints" className={navItemClass}>
            <FileText className="w-5 h-5 flex-shrink-0 text-current" />
            <span>{t('navMyComplaints')}</span>
          </NavLink>

          <NavLink to="/file-form" className={navItemClass}>
            <FilePlus2 className="w-5 h-5 flex-shrink-0 text-current" />
            <span>{t('navFileViaForm')}</span>
          </NavLink>

          <NavLink to="/notifications" className={navItemClass}>
            <div className="relative flex items-center justify-center">
              <Bell className="w-5 h-5 flex-shrink-0 text-current" />
            </div>
            <span className="flex-1">{t('navNotifications')}</span>
            {unreadCount > 0 && (
              <span className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 text-xs font-bold rounded-full bg-red-600 text-white shadow-sm">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </NavLink>

          <NavLink to="/profile" className={navItemClass}>
            <User className="w-5 h-5 flex-shrink-0 text-current" />
            <span>{t('navProfile')}</span>
          </NavLink>

          {/* Additional features: Hotspot map & Public Impact */}
          <div className="pt-4 mt-4 border-t border-maroon-700/60">
            <div className="px-4 pb-2 text-[11px] font-bold tracking-wider uppercase text-cream-300/60">
              Insights & Public Data
            </div>

            {role === 'admin' && (
              <NavLink to="/hotspots" className={navItemClass}>
                <MapPin className="w-5 h-5 flex-shrink-0 text-current" />
                <span>{t('navHotspotMap')}</span>
              </NavLink>
            )}

            <NavLink to="/impact" className={navItemClass}>
              <BarChart3 className="w-5 h-5 flex-shrink-0 text-current" />
              <span>{t('navImpact')}</span>
            </NavLink>

            {role === 'admin' && (
              <NavLink to="/admin" className={navItemClass}>
                <ShieldAlert className="w-5 h-5 flex-shrink-0 text-saffron-400" />
                <span className="text-saffron-300">{t('navAdminDashboard')}</span>
              </NavLink>
            )}
          </div>
        </nav>
      </div>

      {/* Bottom Area: Logout & Watermark Building Illustration */}
      <div className="relative z-10 pt-6">
        <button
          type="button"
          onClick={handleLogout}
          className="w-full flex items-center gap-3.5 px-4 py-3 rounded-2xl text-sm font-semibold text-cream-200/90 hover:bg-maroon-700 hover:text-white transition-all duration-200 focus-ring"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          <span>{t('navLogout')}</span>
        </button>

        {/* Subtle Building Illustration Watermark as seen in screenshot */}
        <div className="mt-4 px-2 opacity-25 pointer-events-none select-none">
          <BuildingIllustration variant="silhouette" className="w-full h-24 text-cream-300" />
        </div>
      </div>

      {/* Decorative gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-maroon-900/40 via-transparent to-maroon-950/80 pointer-events-none" />
    </aside>
  );
};

