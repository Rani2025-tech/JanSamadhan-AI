import {
  UserProfile,
  Complaint,
  NotificationItem,
  ChatMessage,
  HotspotRecord,
  LanguageCode,
  UrgencyLevel,
} from '../types';

const API_BASE = '/api';

let isApiOffline = false;
const offlineListeners: ((offline: boolean) => void)[] = [];

export function subscribeToApiOffline(listener: (offline: boolean) => void) {
  offlineListeners.push(listener);
  return () => {
    const idx = offlineListeners.indexOf(listener);
    if (idx !== -1) offlineListeners.splice(idx, 1);
  };
}

export function setApiOffline(offline: boolean) {
  if (isApiOffline !== offline) {
    isApiOffline = offline;
    offlineListeners.forEach(l => l(offline));
  }
}

async function fetchWithStatus(url: string, init?: RequestInit): Promise<Response> {
  try {
    const res = await fetch(url, init);
    setApiOffline(false);
    return res;
  } catch (err) {
    setApiOffline(true);
    throw err;
  }
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('jansamadhan_jwt') || sessionStorage.getItem('jansamadhan_jwt');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // Health & Offline Detection
  async checkHealth(): Promise<{ status: string; gemini_active: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        setApiOffline(false);
        return res.json();
      }
      setApiOffline(true);
      return { status: 'offline', gemini_active: false };
    } catch {
      setApiOffline(true);
      return { status: 'offline', gemini_active: false };
    }
  },

  // Auth
  async sendOtp(mobile: string): Promise<{ success: boolean; message: string; mock_otp?: string }> {
    const res = await fetchWithStatus(`${API_BASE}/auth/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: mobile }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to send OTP');
    }
    return res.json();
  },

  async verifyOtp(mobile: string, otp: string): Promise<{ access_token: string; user: UserProfile }> {
    const res = await fetchWithStatus(`${API_BASE}/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: mobile, otp }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Invalid OTP');
    }
    return res.json();
  },

  async adminLogin(idOrEmail: string, password: string): Promise<{ access_token: string; user: UserProfile }> {
    const res = await fetchWithStatus(`${API_BASE}/auth/admin-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_or_email: idOrEmail, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Admin login failed');
    }
    return res.json();
  },

  async guestLogin(): Promise<{ access_token: string; user: UserProfile }> {
    const res = await fetchWithStatus(`${API_BASE}/auth/guest-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      throw new Error('Guest login failed');
    }
    return res.json();
  },

  async getMe(): Promise<UserProfile> {
    const res = await fetchWithStatus(`${API_BASE}/auth/me`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error('Not authenticated');
    }
    return res.json();
  },

  async updateProfile(updates: Partial<UserProfile>): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/auth/profile`, {
      method: 'PUT',
      headers: getAuthHeader(),
      body: JSON.stringify(updates),
    });
    if (!res.ok) {
      throw new Error('Failed to update profile');
    }
    return res.json();
  },

  // Complaints
  async getComplaints(params?: {
    status?: string;
    department?: string;
    urgency?: string;
    district?: string;
    search?: string;
    user_id?: string;
  }): Promise<Complaint[]> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v && v !== 'all') query.set(k, v);
      });
    }
    const res = await fetchWithStatus(`${API_BASE}/complaints?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch complaints');
    }
    return res.json();
  },

  async getComplaint(id: string): Promise<Complaint> {
    const res = await fetchWithStatus(`${API_BASE}/complaints/${id}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error('Complaint not found');
    }
    return res.json();
  },

  async createComplaint(data: {
    title: string;
    description: string;
    category?: string;
    department?: string;
    sub_category?: string;
    urgency?: UrgencyLevel;
    district?: string;
    area?: string;
    pincode?: string;
    lat?: number;
    lng?: number;
    language?: string;
  }): Promise<Complaint> {
    const res = await fetchWithStatus(`${API_BASE}/complaints`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to submit complaint');
    }
    return res.json();
  },

  async updateComplaintStatus(
    id: string,
    status: string,
    note?: string,
    officerName?: string
  ): Promise<Complaint> {
    const res = await fetchWithStatus(`${API_BASE}/complaints/${id}/status`, {
      method: 'PUT',
      headers: getAuthHeader(),
      body: JSON.stringify({
        status,
        note,
        officer: officerName,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update status');
    }
    return res.json();
  },

  async updateComplaintAdmin(
    id: string,
    updates: {
      category?: string;
      department?: string;
      urgency?: string;
      assigned_officer_name?: string;
      assigned_officer_designation?: string;
      assigned_officer_dept?: string;
      assigned_officer_phone?: string;
    }
  ): Promise<Complaint> {
    const res = await fetchWithStatus(`${API_BASE}/complaints/${id}/admin-update`, {
      method: 'PATCH',
      headers: getAuthHeader(),
      body: JSON.stringify(updates),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update complaint');
    }
    return res.json();
  },

  async checkDuplicate(data: {
    description: string;
    category: string;
    district: string;
    area?: string;
    lat?: number;
    lng?: number;
  }): Promise<{ is_duplicate: boolean; duplicate_of?: string; similarity_score?: number; reason?: string }> {
    const res = await fetchWithStatus(`${API_BASE}/complaints/check-duplicate`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      return { is_duplicate: false };
    }
    return res.json();
  },

  async submitFeedback(id: string, rating: number, comment?: string): Promise<{ success: boolean; message: string }> {
    const res = await fetchWithStatus(`${API_BASE}/complaints/${id}/feedback`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify({ rating, comment }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to submit feedback');
    }
    return res.json();
  },

  // Notifications
  async getNotifications(unreadOnly = false): Promise<NotificationItem[]> {
    const res = await fetchWithStatus(`${API_BASE}/notifications?unread_only=${unreadOnly}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch notifications');
    }
    return res.json();
  },

  async markNotificationRead(id: string): Promise<void> {
    await fetch(`${API_BASE}/notifications/${id}/read`, {
      method: 'PUT',
      headers: getAuthHeader(),
    });
  },

  async markAllNotificationsRead(): Promise<void> {
    await fetch(`${API_BASE}/notifications/read-all`, {
      method: 'PUT',
      headers: getAuthHeader(),
    });
  },

  // Admin & Analytics
  async getAdminStats(): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/stats`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch admin stats');
    }
    return res.json();
  },

  async getEvalResults(): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/eval-results`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch eval results');
    }
    return res.json();
  },

  async getImpactStates(): Promise<any> {
    const res = await fetchWithStatus(`${API_BASE}/impact/states`);
    if (!res.ok) {
      throw new Error('Failed to fetch impact states');
    }
    return res.json();
  },

  async getImpactStates(): Promise<any> {
    const res = await fetchWithStatus(`${API_BASE}/impact/states`);
    if (!res.ok) {
      throw new Error('Failed to fetch impact states');
    }
    return res.json();
  },

  async getHotspots(params?: { view?: 'national' | 'district'; state?: string }): Promise<HotspotRecord[]> {
    const query = new URLSearchParams();
    if (params?.view) query.set('view', params.view);
    if (params?.state) query.set('state', params.state);
    const res = await fetch(`${API_BASE}/admin/hotspots?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch grievance hotspots');
    }
    return res.json();
  },

  // AI Chat
  async sendChatMessage(data: {
    session_id?: string;
    message: string;
    language?: string;
    user_id?: string;
  }): Promise<{
    session_id: string;
    reply: string;
    language: string;
    state: string;
    intent: string;
    category?: string;
    department?: string;
    urgency?: string;
    district?: string;
    area?: string;
    pincode?: string;
    extracted_data?: Record<string, any>;
    needs_confirmation?: boolean;
    confirmation_card?: any;
    filed_complaint?: any;
  }> {
    const res = await fetchWithStatus(`${API_BASE}/chat/message`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to send message');
    }
    return res.json();
  },
};
