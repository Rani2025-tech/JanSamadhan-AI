import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { NotificationItem } from '../types';
import { INITIAL_NOTIFICATIONS } from '../data/mockData';
import { api } from '../services/api';

interface NotificationContextType {
  notifications: NotificationItem[];
  unreadCount: number;
  userUpdates: NotificationItem[];
  announcements: NotificationItem[];
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  addNotification: (item: Omit<NotificationItem, 'id' | 'read' | 'timestamp'>) => void;
  refreshNotifications: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

const STORAGE_KEY = 'jansamadhan_notifications';

export const NotificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return INITIAL_NOTIFICATIONS;
      }
    }
    return INITIAL_NOTIFICATIONS;
  });

  const refreshNotifications = async () => {
    try {
      const data = await api.getNotifications();
      if (data && data.length > 0) {
        setNotifications(data);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      }
    } catch (e) {
      // Offline fallback
    }
  };

  useEffect(() => {
    refreshNotifications();
  }, []);

  const saveNotifications = (items: NotificationItem[]) => {
    setNotifications(items);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  };

  const unreadCount = notifications.filter(n => !n.read).length;
  const userUpdates = notifications.filter(n => n.type === 'update');
  const announcements = notifications.filter(n => n.type === 'announcement');

  const markAsRead = async (id: string) => {
    const updated = notifications.map(n => (n.id === id ? { ...n, read: true } : n));
    saveNotifications(updated);
    try {
      await api.markNotificationRead(id);
    } catch (e) {
      // local updated
    }
  };

  const markAllAsRead = async () => {
    const updated = notifications.map(n => ({ ...n, read: true }));
    saveNotifications(updated);
    try {
      await api.markAllNotificationsRead();
    } catch (e) {
      // local updated
    }
  };

  const addNotification = (item: Omit<NotificationItem, 'id' | 'read' | 'timestamp'>) => {
    const now = new Date();
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const timeStr = `${now.getDate()} ${months[now.getMonth()]} 2026 • ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

    const newNotif: NotificationItem = {
      ...item,
      id: `NOTIF-${Date.now()}`,
      timestamp: timeStr,
      read: false,
    };
    saveNotifications([newNotif, ...notifications]);
  };

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        userUpdates,
        announcements,
        markAsRead,
        markAllAsRead,
        addNotification,
        refreshNotifications,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};
