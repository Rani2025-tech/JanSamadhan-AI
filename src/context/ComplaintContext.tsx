import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Complaint, ComplaintStatus, UrgencyLevel } from '../types';
import { INITIAL_COMPLAINTS } from '../data/mockData';
import { useNotifications } from './NotificationContext';
import { api } from '../services/api';

interface ComplaintContextType {
  complaints: Complaint[];
  userStats: {
    total: number;
    open: number;
    resolved: number;
    avgResolutionDays: number;
  };
  loading: boolean;
  getComplaintById: (id: string) => Complaint | undefined;
  createComplaint: (data: {
    title: string;
    description: string;
    category: string;
    department: string;
    urgency: UrgencyLevel;
    language: string;
    state?: string;
    district: string;
    area: string;
    pincode?: string;
  }) => Promise<Complaint>;
  updateStatus: (
    id: string,
    newStatus: ComplaintStatus,
    officerNote: string,
    officerName?: string
  ) => Promise<void>;
  submitFeedback: (id: string, rating: number, comment?: string) => Promise<void>;
  adminUpdateComplaint: (id: string, updates: { category?: string; department?: string; urgency?: UrgencyLevel; status?: ComplaintStatus }) => Promise<void>;
  refreshComplaints: () => Promise<void>;
}

const ComplaintContext = createContext<ComplaintContextType | undefined>(undefined);

const STORAGE_KEY = 'jansamadhan_complaints';

export const ComplaintProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { addNotification } = useNotifications();
  const [loading, setLoading] = useState(false);

  const [complaints, setComplaints] = useState<Complaint[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return INITIAL_COMPLAINTS;
      }
    }
    return INITIAL_COMPLAINTS;
  });

  const refreshComplaints = async () => {
    setLoading(true);
    try {
      const data = await api.getComplaints();
      if (data && data.length > 0) {
        setComplaints(data);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      }
    } catch (e) {
      // Offline fallback: keep cached complaints
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshComplaints();
  }, []);

  // Compute stats dynamically from active list
  const total = complaints.length;
  const open = complaints.filter(c => c.status !== 'Resolved').length;
  const resolved = complaints.filter(c => c.status === 'Resolved').length;
  const avgResolutionDays = 6;

  const userStats = {
    total,
    open,
    resolved,
    avgResolutionDays,
  };

  const getComplaintById = (id: string) => {
    return complaints.find(c => c.id.toLowerCase() === id.toLowerCase());
  };

  const createComplaint = async (data: {
    title: string;
    description: string;
    category: string;
    department: string;
    urgency: UrgencyLevel;
    language: string;
    state?: string;
    district: string;
    area: string;
    pincode?: string;
  }): Promise<Complaint> => {
    try {
      const created = await api.createComplaint(data);
      const updated = [created, ...complaints.filter(c => c.id !== created.id)];
      setComplaints(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return created;
    } catch (e) {
      // Local fallback creation
      const nextNumber = 1043 + complaints.length - 3;
      const newId = `GRV-${nextNumber}`;
      const today = new Date();
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const formattedDate = `${today.getDate()} ${months[today.getMonth()]} 2026`;
      const expDate = new Date(today);
      expDate.setDate(today.getDate() + 7);
      const expFormatted = `${expDate.getDate()} ${months[expDate.getMonth()]} 2026`;

      const newComplaint: Complaint = {
        id: newId,
        title: data.title,
        description: data.description,
        department: data.department,
        category: data.category,
        urgency: data.urgency,
        language: data.language,
        status: 'Submitted',
        location: {
          state: data.state || 'Odisha',
          district: data.district,
          area: data.area,
          pincode: data.pincode,
          coordinates: [20.2961, 85.8245]
        },
        submittedDate: formattedDate,
        expectedDate: expFormatted,
        daysRemaining: 7,
        statusHistory: [
          {
            status: 'Submitted',
            date: formattedDate,
            time: today.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            note: `Grievance registered in ${data.language}. Assigned ticket ID ${newId}.`,
            completed: true,
            current: true,
          }
        ]
      };

      const updated = [newComplaint, ...complaints];
      setComplaints(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return newComplaint;
    }
  };

  const updateStatus = async (
    id: string,
    newStatus: ComplaintStatus,
    officerNote: string,
    officerName?: string
  ) => {
    try {
      const updatedComp = await api.updateComplaintStatus(id, newStatus, officerNote, officerName);
      const updated = complaints.map(c => (c.id === id ? updatedComp : c));
      setComplaints(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      const today = new Date();
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const formattedDate = `${today.getDate()} ${months[today.getMonth()]} 2026`;

      const updated = complaints.map(c => {
        if (c.id.toLowerCase() !== id.toLowerCase()) return c;
        const newHistory = c.statusHistory.map(h => {
          if (h.status === newStatus) {
            return {
              ...h,
              date: formattedDate,
              time: today.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              officer: officerName || h.officer || 'Duty Officer',
              note: officerNote,
              completed: true,
              current: true,
            };
          }
          return { ...h, current: false };
        });

        return {
          ...c,
          status: newStatus,
          statusHistory: newHistory,
          daysRemaining: newStatus === 'Resolved' ? 0 : c.daysRemaining,
        };
      });

      setComplaints(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    }
  };

  const submitFeedback = async (id: string, rating: number, comment?: string) => {
    try {
      const updatedComp = await api.submitFeedback(id, rating, comment);
      const updated = complaints.map(c => (c.id === id ? updatedComp : c));
      setComplaints(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      const updated = complaints.map(c => {
        if (c.id.toLowerCase() !== id.toLowerCase()) return c;
        return { ...c, feedback: { rating, comment } };
      });
      setComplaints(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    }
  };

  const adminUpdateComplaint = async (
    id: string,
    updates: { category?: string; department?: string; urgency?: UrgencyLevel; status?: ComplaintStatus }
  ) => {
    try {
      const updatedComp = await api.adminUpdateComplaint(id, updates);
      const updated = complaints.map(c => (c.id === id ? updatedComp : c));
      setComplaints(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      const updated = complaints.map(c => {
        if (c.id.toLowerCase() !== id.toLowerCase()) return c;
        return {
          ...c,
          category: updates.category || c.category,
          department: updates.department || c.department,
          urgency: updates.urgency || c.urgency,
          status: updates.status || c.status,
          needs_human_review: false,
        };
      });
      setComplaints(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    }
  };

  return (
    <ComplaintContext.Provider
      value={{
        complaints,
        userStats,
        loading,
        getComplaintById,
        createComplaint,
        updateStatus,
        submitFeedback,
        adminUpdateComplaint,
        refreshComplaints,
      }}
    >
      {children}
    </ComplaintContext.Provider>
  );
};

export const useComplaints = (): ComplaintContextType => {
  const context = useContext(ComplaintContext);
  if (!context) {
    throw new Error('useComplaints must be used within a ComplaintProvider');
  }
  return context;
};
