import { Complaint, NotificationItem, UserProfile, ComplaintStatus, UrgencyLevel, HotspotRecord } from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || '/api';

let isApiOffline = false;
let offlineListeners: ((offline: boolean) => void)[] = [];

export function subscribeToApiStatus(listener: (offline: boolean) => void) {
  offlineListeners.push(listener);
  listener(isApiOffline);
  return () => {
    offlineListeners = offlineListeners.filter(l => l !== listener);
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
      body: JSON.stringify({ mobile }),
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
      body: JSON.stringify({ mobile, otp }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to verify OTP');
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
    userId?: string;
    status?: string;
    department?: string;
    state?: string;
    district?: string;
    search?: string;
  }): Promise<Complaint[]> {
    const query = new URLSearchParams();
    if (params?.userId) query.set('user_id', params.userId);
    if (params?.status) query.set('status', params.status);
    if (params?.department) query.set('department', params.department);
    if (params?.state) query.set('state', params.state);
    if (params?.district) query.set('district', params.district);
    if (params?.search) query.set('search', params.search);

    const res = await fetch(`${API_BASE}/complaints?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch complaints');
    }
    return res.json();
  },

  async getComplaintById(id: string): Promise<Complaint> {
    const res = await fetch(`${API_BASE}/complaints/${id}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch complaint ${id}`);
    }
    return res.json();
  },

  async createComplaint(data: {
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
  }): Promise<Complaint> {
    const res = await fetch(`${API_BASE}/complaints`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to file complaint');
    }
    return res.json();
  },

  async checkDuplicate(data: {
    text: string;
    district: string;
    category: string;
  }): Promise<{ is_duplicate: boolean; confidence: number; matched_complaint_id?: string; matched_title?: string; message: string }> {
    const res = await fetch(`${API_BASE}/complaints/check-duplicate`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      return { is_duplicate: false, confidence: 0, message: '' };
    }
    return res.json();
  },

  async updateComplaintStatus(
    id: string,
    status: ComplaintStatus,
    officerNote: string,
    officerName?: string
  ): Promise<Complaint> {
    const res = await fetch(`${API_BASE}/complaints/${id}/status`, {
      method: 'PUT',
      headers: getAuthHeader(),
      body: JSON.stringify({
        status,
        officer_note: officerNote,
        officer_name: officerName,
      }),
    });
    if (!res.ok) {
      throw new Error('Failed to update complaint status');
    }
    return res.json();
  },

  async submitFeedback(id: string, rating: number, comment?: string): Promise<Complaint> {
    const res = await fetch(`${API_BASE}/complaints/${id}/feedback`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify({ rating, comment }),
    });
    if (!res.ok) {
      throw new Error('Failed to submit feedback');
    }
    return res.json();
  },

  async adminUpdateComplaint(
    id: string,
    updates: { category?: string; department?: string; urgency?: string; status?: string }
  ): Promise<Complaint> {
    const res = await fetch(`${API_BASE}/complaints/${id}/admin-update`, {
      method: 'PATCH',
      headers: getAuthHeader(),
      body: JSON.stringify(updates),
    });
    if (!res.ok) {
      throw new Error('Failed to update complaint');
    }
    return res.json();
  },

  // Notifications
  async getNotifications(): Promise<NotificationItem[]> {
    const res = await fetch(`${API_BASE}/notifications`, {
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
    state: string;
    slots: Record<string, any>;
    ready_to_file: boolean;
    confirmation_card?: any;
    filed_complaint?: Complaint;
    detected_faq?: { question: string; answer: string; source: string; similarity: number };
  }> {
    const res = await fetch(`${API_BASE}/chat/message`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Chat request failed');
    }
    return res.json();
  },
};

