import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Search, Bell, ChevronDown, User, LogOut, Shield, Globe, Sparkles } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useNotifications } from '../../context/NotificationContext';
import { useAuth } from '../../context/AuthContext';
import { AccessibilityBar } from './AccessibilityBar';
import { LanguageCode } from '../../types';

interface NavbarProps {
  onSearch?: (query: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onSearch }) => {
  const { currentLanguage, setLanguage, currentLanguageOption, languages, t } = useLanguage();
  const { unreadCount } = useNotifications();
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();

  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const langRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (langRef.current && !langRef.current.contains(event.target as Node)) {
        setLangDropdownOpen(false);
      }
      if (userRef.current && !userRef.current.contains(event.target as Node)) {
        setUserDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      if (onSearch) {
        onSearch(searchQuery.trim());
      } else {
        // If it starts with GRV or has digits, redirect directly to complaint or complaints list
        const cleanId = searchQuery.trim().toUpperCase();
        if (cleanId.startsWith('GRV-')) {
          navigate(`/complaints/${cleanId}`);
        } else {
          navigate(`/complaints?search=${encodeURIComponent(searchQuery.trim())}`);
        }
      }
    }
  };

  const handleSelectLanguage = (code: LanguageCode) => {
    setLanguage(code);
    setLangDropdownOpen(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-30 bg-cream-400/90 backdrop-blur-md border-b border-maroon-100/70 px-4 lg:px-8 py-3 transition-colors">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Language Selector & Global Search */}
        <div className="flex items-center gap-3 sm:gap-4 flex-1 max-w-2xl">
          {/* Top Bar Language Switcher */}
          <div className="relative" ref={langRef}>
            <button
              type="button"
              onClick={() => setLangDropdownOpen(prev => !prev)}
              className="flex items-center gap-2 bg-white px-3.5 py-2 rounded-full border border-maroon-100 shadow-sm text-sm font-semibold text-gray-800 hover:border-maroon-300 focus-ring"
              aria-expanded={langDropdownOpen}
              aria-label="Select Language"
            >
              <Globe className="w-4 h-4 text-maroon-800" />
              <span>{currentLanguageOption.nativeName}</span>
              <span className="text-xs text-gray-500 font-normal">({currentLanguageOption.enName})</span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-500 transition-transform duration-200" />
            </button>

            {langDropdownOpen && (
              <div className="absolute left-0 mt-2 w-56 rounded-2xl bg-white shadow-soft-lg border border-maroon-100 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Select Language
                </div>
                <div className="divide-y divide-gray-100">
                  {languages.map(lang => (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => handleSelectLanguage(lang.code)}
                      className={`w-full text-left px-3.5 py-2 flex items-center justify-between hover:bg-cream-200 transition-colors ${
                        currentLanguage === lang.code ? 'bg-maroon-50 font-bold text-maroon-900' : 'text-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-maroon-100 text-maroon-900 text-xs font-bold">
                          {lang.nativeChar}
                        </span>
                        <div>
                          <div className="text-sm">{lang.nativeName}</div>
                          <div className="text-xs text-gray-500 font-normal">{lang.enName}</div>
                        </div>
                      </div>
                      {currentLanguage === lang.code && (
                        <span className="text-xs text-maroon-800 font-bold">✓</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Search bar */}
          <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md hidden md:block">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder={t('searchPlaceholder')}
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-maroon-100 rounded-full placeholder-gray-400 shadow-sm focus-ring focus:border-maroon-800"
            />
          </form>
        </div>

        {/* Right: Accessibility toolbar + Notifications + User Avatar */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Accessibility bar in top header (hidden on very small screens, visible on sm+) */}
          <div className="hidden lg:block">
            <AccessibilityBar />
          </div>

          {/* Notifications Bell */}
          <Link
            to="/notifications"
            className="relative p-2.5 rounded-full bg-white border border-maroon-100 shadow-sm text-gray-700 hover:text-maroon-800 hover:bg-cream-200 transition-colors focus-ring"
            title="Notifications"
            aria-label={`Notifications, ${unreadCount} unread`}
          >
            <Bell className="w-5 h-5 text-gray-700" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-5 min-w-[20px] px-1 items-center justify-center rounded-full bg-red-600 text-white text-[11px] font-bold shadow-sm animate-pulse-subtle">
                {unreadCount}
              </span>
            )}
          </Link>

          {/* User Menu */}
          <div className="relative" ref={userRef}>
            <button
              type="button"
              onClick={() => setUserDropdownOpen(prev => !prev)}
              className="flex items-center gap-2.5 bg-white pl-2 pr-3 py-1.5 rounded-full border border-maroon-100 shadow-sm hover:border-maroon-300 focus-ring"
              aria-expanded={userDropdownOpen}
              aria-label="User profile menu"
            >
              {user?.avatar ? (
                <img
                  src={user.avatar}
                  alt={user.name}
                  className="w-7 h-7 rounded-full object-cover border border-maroon-200"
                />
              ) : (
                <div className="w-7 h-7 rounded-full bg-maroon-800 text-white flex items-center justify-center text-xs font-bold">
                  {user?.name?.charAt(0) || 'U'}
                </div>
              )}
              <span className="text-sm font-semibold text-gray-800 max-w-[120px] truncate hidden sm:inline-block">
                {user?.name || 'Citizen'}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
            </button>

            {userDropdownOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-white shadow-soft-lg border border-maroon-100 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-4 py-2 border-b border-gray-100">
                  <div className="font-bold text-gray-900 text-sm">{user?.name}</div>
                  <div className="text-xs text-gray-500 truncate">{user?.phone || user?.email || 'Guest Mode'}</div>
                  <div className="mt-1.5 flex items-center gap-1.5">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-maroon-100 text-maroon-800 uppercase tracking-wider">
                      {role === 'admin' ? 'Officer / Admin' : role === 'guest' ? 'Guest Citizen' : 'Citizen'}
                    </span>
                  </div>
                </div>

                <div className="py-1">
                  <Link
                    to="/profile"
                    onClick={() => setUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-4 py-2 text-sm text-gray-700 hover:bg-cream-200 transition-colors"
                  >
                    <User className="w-4 h-4 text-maroon-800" />
                    <span>{t('profile')}</span>
                  </Link>

                  {role === 'admin' && (
                    <Link
                      to="/admin"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2 text-sm text-maroon-800 font-semibold hover:bg-maroon-50 transition-colors"
                    >
                      <Shield className="w-4 h-4" />
                      <span>{t('navAdminDashboard')}</span>
                    </Link>
                  )}

                  <Link
                    to="/impact"
                    onClick={() => setUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-4 py-2 text-sm text-gray-700 hover:bg-cream-200 transition-colors"
                  >
                    <Sparkles className="w-4 h-4 text-saffron-500" />
                    <span>{t('navImpact')}</span>
                  </Link>
                </div>

                <div className="border-t border-gray-100 pt-1">
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors font-medium"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>{t('logout')}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

