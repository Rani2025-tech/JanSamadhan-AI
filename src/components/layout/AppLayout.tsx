import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { BottomNav } from './BottomNav';
import { FloatingChatButton } from '../common/FloatingChatButton';
import { OfflineBanner } from '../common/OfflineBanner';
import { useLanguage } from '../../context/LanguageContext';

export const AppLayout: React.FC = () => {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen flex flex-col bg-cream-400 text-gray-900 transition-colors duration-200">
      {/* Offline Status Warning Banner */}
      <OfflineBanner />

      <div className="flex-1 flex min-h-0">
        {/* Desktop Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 pb-16 md:pb-6">
        {/* Top Navbar */}
        <Navbar />

        {/* Page View */}
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full transition-all">
          <Outlet />
        </main>

        {/* Standard Footer */}
        <footer className="mt-auto py-4 px-6 text-center text-xs text-gray-500 border-t border-maroon-100/60 bg-cream-300/40">
          <p className="flex items-center justify-center gap-2 flex-wrap">
            <span>{t('footerText')}</span>
          </p>
        </footer>
      </div>
    </div>

      {/* Mobile Bottom Navigation */}
      <BottomNav />

      {/* Persistent Floating Chat Button */}
      <FloatingChatButton />
    </div>
  );
};

