export type UserRole = 'citizen' | 'admin' | 'guest';

export type LanguageCode = 'en' | 'hi' | 'or' | 'bn' | 'mr' | 'ta' | 'te';

export interface LanguageOption {
  code: LanguageCode;
  nativeChar: string;
  nativeName: string;
  enName: string;
}

export type UrgencyLevel = 'Low' | 'Medium' | 'High' | 'Critical';

export type ComplaintStatus = 'Submitted' | 'Assigned' | 'In Progress' | 'Resolved';

export interface StatusHistoryItem {
  status: ComplaintStatus;
  date: string;       // e.g. "28 Oct 2026"
  time?: string;      // e.g. "10:30 AM"
  officer?: string;
  note: string;
  completed: boolean;
  current?: boolean;
}

export interface Complaint {
  id: string; // e.g. "GRV-1042"
  title: string;
  description: string;
  department: string; // e.g. "PHED", "PWD", "DISCOM"
  category: string;   // e.g. "Water Supply", "Roads", "Electricity"
  urgency: UrgencyLevel;
  language: string;   // e.g. "Odia", "Hindi", "Bengali"
  status: ComplaintStatus;
  location: {
    state?: string;
    district: string;
    area: string;
    pincode?: string;
    coordinates?: [number, number]; // [lat, lng]
  };
  submittedDate: string; // "28 Oct 2026"
  expectedDate: string;  // "05 Nov 2026"
  daysRemaining: number; // e.g. 2 ("2 days left")
  assignedOfficer?: {
    name: string;
    designation: string;
    department: string;
    phone?: string;
  };
  statusHistory: StatusHistoryItem[];
  attachments?: { name: string; url: string; type: string }[];
  feedback?: {
    rating: number;
    comment?: string;
  };
  citizenPhone?: string;
  ai_confidence?: number;
  needs_human_review?: boolean;
  translated_text_en?: string;
  sentiment?: string;
  ai_summary?: string;
  duplicate_of_id?: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  timestamp: string; // e.g. "30 Oct 2026 • 2:15 PM"
  type: 'update' | 'announcement';
  read: boolean;
  relatedGrvId?: string;
  actionUrl?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  phone: string;
  email?: string;
  role: UserRole;
  language: LanguageCode;
  state?: string;
  district?: string;
  employeeId?: string;
  department?: string;
  avatar?: string;
}

export interface PlatformStats {
  total: number;
  open: number;
  resolved: number;
  avgResolutionDays: number;
}

export interface HotspotRecord {
  state?: string;
  district: string;
  total_complaints: number;
  open_count: number;
  resolved_count: number;
  top_category: string;
  critical_count: number;
  average_urgency: number;
  severity: 'green' | 'amber' | 'red';
}


