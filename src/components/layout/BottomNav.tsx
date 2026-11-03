import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Bot, FileText, FilePlus2, Bell, User } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';
import { useLanguage } from '../../context/LanguageContext';

export const BottomNav: React.FC = () => {
  const { unreadCount } = useNotifications();
  const { t } = useLanguage();

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex flex-col items-center justify-center py-2 px-1 text-[10px] font-semibold transition-colors duration-150 ${
      isActive
        ? 'text-maroon-800 font-bold'
        : 'text-gray-500 hover:text-maroon-700'
    }`;

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-maroon-100 shadow-lg px-2 py-1 flex items-center justify-around"
      aria-label="Mobile Navigation"
    >
      <NavLink to="/dashboard" className={navItemClass}>
        <Home className="w-5 h-5 mb-0.5" />
        <span>{t('navDashboard')}</span>
      </NavLink>

      <NavLink to="/assistant" className={navItemClass}>
        <Bot className="w-5 h-5 mb-0.5" />
        <span>{t('navAIAssistant')}</span>
      </NavLink>

      <NavLink to="/complaints" className={navItemClass}>
        <FileText className="w-5 h-5 mb-0.5" />
        <span>{t('navMyComplaints')}</span>
      </NavLink>

      <NavLink to="/file-form" className={navItemClass}>
        <FilePlus2 className="w-5 h-5 mb-0.5" />
        <span>{t('navFileViaForm')}</span>
      </NavLink>

      <NavLink to="/notifications" className={navItemClass}>
        <div className="relative">
          <Bell className="w-5 h-5 mb-0.5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-2 flex h-4 min-w-[16px] px-1 items-center justify-center rounded-full bg-red-600 text-white text-[9px] font-bold">
              {unreadCount}
            </span>
          )}
        </div>
        <span>{t('navNotifications')}</span>
      </NavLink>

      <NavLink to="/profile" className={navItemClass}>
        <User className="w-5 h-5 mb-0.5" />
        <span>{t('navProfile')}</span>
      </NavLink>
    </nav>
  );
};

