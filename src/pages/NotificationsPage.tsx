import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Bell,
  CheckCheck,
  Radio,
  FileText,
  ArrowRight,
} from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';
import { useLanguage } from '../context/LanguageContext';

export const NotificationsPage: React.FC = () => {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [activeFilter, setActiveFilter] = useState<'all' | 'update' | 'announcement'>(
    (searchParams.get('tab') as any) || 'all'
  );

  const filtered = notifications.filter(item => {
    if (activeFilter === 'all') return true;
    return item.type === activeFilter;
  });

  const handleItemClick = (item: any) => {
    markAsRead(item.id);
    if (item.relatedGrvId) {
      navigate(`/complaints/${item.relatedGrvId}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
            <Bell className="w-8 h-8 text-maroon-800" />
            <span>{t('navNotifications')}</span>
            {unreadCount > 0 && (
              <span className="bg-red-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">
                {unreadCount} unread
              </span>
            )}
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Real-time status alerts for your grievances and official platform announcements.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={markAllAsRead}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-maroon-200 text-maroon-900 text-xs sm:text-sm font-semibold hover:bg-cream-100 shadow-xs focus-ring"
          >
            <CheckCheck className="w-4 h-4 text-maroon-800" />
            <span>Mark all as read</span>
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 pb-2">
        <button
          type="button"
          onClick={() => setActiveFilter('all')}
          className={`px-4 py-2 rounded-2xl text-xs sm:text-sm font-bold transition-colors focus-ring ${
            activeFilter === 'all'
              ? 'bg-maroon-800 text-white shadow-xs'
              : 'text-gray-600 hover:text-maroon-800 hover:bg-cream-200'
          }`}
        >
          All ({notifications.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveFilter('update')}
          className={`px-4 py-2 rounded-2xl text-xs sm:text-sm font-bold transition-colors focus-ring ${
            activeFilter === 'update'
              ? 'bg-maroon-800 text-white shadow-xs'
              : 'text-gray-600 hover:text-maroon-800 hover:bg-cream-200'
          }`}
        >
          {t('myUpdates')} ({notifications.filter(n => n.type === 'update').length})
        </button>

        <button
          type="button"
          onClick={() => setActiveFilter('announcement')}
          className={`px-4 py-2 rounded-2xl text-xs sm:text-sm font-bold transition-colors focus-ring ${
            activeFilter === 'announcement'
              ? 'bg-maroon-800 text-white shadow-xs'
              : 'text-gray-600 hover:text-maroon-800 hover:bg-cream-200'
          }`}
        >
          {t('announcements')} ({notifications.filter(n => n.type === 'announcement').length})
        </button>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border border-maroon-100 shadow-soft space-y-3">
            <Bell className="w-10 h-10 text-gray-300 mx-auto" />
            <p className="text-sm font-bold text-gray-700">
              {activeFilter === 'update'
                ? 'No grievance updates yet'
                : activeFilter === 'announcement'
                ? 'No official announcements yet'
                : 'No notifications yet'}
            </p>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              {activeFilter === 'update'
                ? 'When an assigned officer reviews or resolves your grievance, you will receive real-time alerts here.'
                : 'System alerts and department notices will appear here.'}
            </p>
          </div>
        ) : (
          filtered.map(item => {
            const isAnnouncement = item.type === 'announcement';
            return (
              <div
                key={item.id}
                onClick={() => handleItemClick(item)}
                className={`bg-white rounded-3xl p-5 border shadow-soft hover:shadow-soft-lg transition-all duration-200 cursor-pointer flex items-start gap-4 ${
                  item.read ? 'border-maroon-100 opacity-90' : 'border-maroon-300 ring-1 ring-maroon-200 bg-cream-50/70'
                }`}
              >
                {/* Icon */}
                <div
                  className={`w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0 ${
                    isAnnouncement ? 'bg-saffron-100 text-saffron-800' : 'bg-maroon-100 text-maroon-800'
                  }`}
                >
                  {isAnnouncement ? <Radio className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                </div>

                {/* Content */}
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <h2 className="text-sm sm:text-base font-bold text-gray-900 flex items-center gap-2">
                      <span>{item.title}</span>
                      {!item.read && (
                        <span className="w-2 h-2 rounded-full bg-red-600 flex-shrink-0" />
                      )}
                    </h2>
                    <span className="text-[11px] font-semibold text-gray-400 whitespace-nowrap">
                      {item.timestamp}
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm text-gray-700 leading-relaxed">
                    {item.message}
                  </p>

                  {item.relatedGrvId && (
                    <div className="pt-1.5 flex items-center gap-1.5 text-xs font-bold text-maroon-800 hover:underline">
                      <span>Track Grievance {item.relatedGrvId}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

