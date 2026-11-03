import { Complaint, NotificationItem, UserProfile } from '../types';

export const INITIAL_USER: UserProfile = {
  id: 'USR-8921',
  name: 'Rani Nayak',
  phone: '9876543210',
  email: 'rani.nayak@example.gov.in',
  role: 'citizen',
  language: 'or',
  district: 'Ganjam',
};

export const ADMIN_USER: UserProfile = {
  id: 'EMP-4402',
  name: 'Dr. Alok Mohapatra, OAS',
  phone: '9876500000',
  email: 'alok.mohapatra@odisha.gov.in',
  employeeId: 'OD-ADM-2024-88',
  role: 'admin',
  department: 'Grievance & Public Administration',
  language: 'en',
  district: 'State Secretariat, Bhubaneswar',
};

export const GUEST_USER: UserProfile = {
  id: 'GUEST-0001',
  name: 'Guest Citizen',
  phone: '',
  role: 'guest',
  language: 'en',
};

export const INITIAL_COMPLAINTS: Complaint[] = [
  {
    id: 'GRV-1042',
    title: 'Water Supply Issue – Low pressure and pipeline blockage',
    description: 'Pipeline supplying drinking water to Ward 7, Berhampur has been contaminated and running at extremely low pressure for the past 4 days.',
    department: 'PHED',
    category: 'Water Supply',
    urgency: 'Medium',
    language: 'Odia',
    status: 'In Progress',
    location: {
      district: 'Ganjam',
      area: 'Berhampur, Ward 7',
      pincode: '760001',
      coordinates: [19.3150, 84.7941]
    },
    submittedDate: '28 Oct 2026',
    expectedDate: '05 Nov 2026',
    daysRemaining: 2,
    assignedOfficer: {
      name: 'Er. S. K. Patnaik',
      designation: 'Assistant Executive Engineer',
      department: 'Public Health Engineering Dept (PHED), Berhampur Division',
      phone: '+91 94370 12345'
    },
    statusHistory: [
      {
        status: 'Submitted',
        date: '28 Oct 2026',
        time: '09:30 AM',
        note: 'Grievance registered via AI Voice Assistant in Odia. Ticket auto-classified to PHED.',
        completed: true,
      },
      {
        status: 'Assigned',
        date: '29 Oct 2026',
        time: '11:15 AM',
        officer: 'Er. S. K. Patnaik (PHED, Berhampur)',
        note: 'Assigned to Division Executive Engineer for physical line inspection.',
        completed: true,
      },
      {
        status: 'In Progress',
        date: '30 Oct 2026',
        time: '02:15 PM',
        officer: 'Er. S. K. Patnaik',
        note: 'Pipeline clearance and valve replacement team deployed on ground.',
        completed: true,
        current: true,
      },
      {
        status: 'Resolved',
        date: '05 Nov 2026',
        time: 'Pending',
        note: 'Water flow verification and citizen sign-off pending.',
        completed: false,
      }
    ]
  },
  {
    id: 'GRV-0987',
    title: 'Deep Potholes and Waterlogging on Main Road',
    description: 'Heavy rain caused dangerous potholes near Badambadi Bus Stand, causing multiple two-wheeler accidents.',
    department: 'PWD',
    category: 'Road Infrastructure',
    urgency: 'High',
    language: 'Hindi',
    status: 'Resolved',
    location: {
      district: 'Cuttack',
      area: 'Badambadi, Ward 14',
      pincode: '753012',
      coordinates: [20.4625, 85.8828]
    },
    submittedDate: '15 Oct 2026',
    expectedDate: '20 Oct 2026',
    daysRemaining: 0,
    assignedOfficer: {
      name: 'R. K. Behera',
      designation: 'Sub-Divisional Officer',
      department: 'Public Works Department (PWD)',
      phone: '+91 94371 99887'
    },
    statusHistory: [
      {
        status: 'Submitted',
        date: '15 Oct 2026',
        time: '10:00 AM',
        note: 'Grievance submitted via Web Form with geotagged photo.',
        completed: true,
      },
      {
        status: 'Assigned',
        date: '16 Oct 2026',
        time: '01:00 PM',
        officer: 'R. K. Behera',
        note: 'Assigned to Cuttack Central Roads Maintenance Unit.',
        completed: true,
      },
      {
        status: 'In Progress',
        date: '17 Oct 2026',
        time: '09:45 AM',
        officer: 'Road Maintenance Contractor #4',
        note: 'Bitumen resurfacing and leveling commenced.',
        completed: true,
      },
      {
        status: 'Resolved',
        date: '19 Oct 2026',
        time: '04:30 PM',
        officer: 'R. K. Behera',
        note: 'Pothole patch work completed and certified safe by junior engineer.',
        completed: true,
        current: true,
      }
    ],
    feedback: {
      rating: 5,
      comment: 'Very swift response and clean patch work. Thank you!'
    }
  },
  {
    id: 'GRV-0951',
    title: 'Streetlights Inoperative in Residential Colony',
    description: 'Entire block of 12 LED streetlights on 4th Cross Road has been dark for two weeks.',
    department: 'DISCOM',
    category: 'Electricity',
    urgency: 'Low',
    language: 'English',
    status: 'Resolved',
    location: {
      district: 'Khurda',
      area: 'Patia, Bhubaneswar',
      pincode: '751024',
      coordinates: [20.3533, 85.8195]
    },
    submittedDate: '10 Oct 2026',
    expectedDate: '15 Oct 2026',
    daysRemaining: 0,
    assignedOfficer: {
      name: 'P. Mohanty',
      designation: 'Electrical Line Inspector',
      department: 'TPCODL / DISCOM',
      phone: '+91 94375 55432'
    },
    statusHistory: [
      {
        status: 'Submitted',
        date: '10 Oct 2026',
        time: '08:15 AM',
        note: 'Grievance filed through AI chatbot.',
        completed: true,
      },
      {
        status: 'Assigned',
        date: '11 Oct 2026',
        time: '11:00 AM',
        officer: 'P. Mohanty',
        note: 'Assigned to TPCODL Northern Zone maintenance team.',
        completed: true,
      },
      {
        status: 'In Progress',
        date: '12 Oct 2026',
        time: '03:20 PM',
        officer: 'P. Mohanty',
        note: 'Faulty phase transformer fuse and 4 blown LEDs replaced.',
        completed: true,
      },
      {
        status: 'Resolved',
        date: '14 Oct 2026',
        time: '06:00 PM',
        officer: 'P. Mohanty',
        note: 'All streetlights tested and verified active in evening inspection.',
        completed: true,
        current: true,
      }
    ],
    feedback: {
      rating: 4,
      comment: 'Resolved quickly once inspected.'
    }
  }
];

export const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'NOTIF-1',
    title: 'Status Update: GRV-1042',
    message: 'GRV-1042 assigned to PHED, Berhampur. Work team deployed on site.',
    timestamp: '30 Oct 2026 • 2:15 PM',
    type: 'update',
    read: false,
    relatedGrvId: 'GRV-1042',
  },
  {
    id: 'NOTIF-2',
    title: 'New AI Assistant Capabilities',
    message: 'New feature: Chat with JanSamadhan Assistant in 6 Indian languages with voice input.',
    timestamp: '25 Oct 2026 • 11:00 AM',
    type: 'announcement',
    read: false,
  },
  {
    id: 'NOTIF-3',
    title: 'Scheduled Maintenance Notice',
    message: 'System maintenance scheduled on 10 Nov 2026 from 02:00 AM to 04:00 AM IST.',
    timestamp: '24 Oct 2026 • 06:30 PM',
    type: 'announcement',
    read: true,
  }
];

export const PLATFORM_STATS = {
  totalComplaints: 12480,
  openComplaints: 3210,
  resolvedComplaints: 9270,
  avgResolutionDays: 7.5,
  satisfactionRate: 94.2,
  districtsCovered: 30,
};

export const HOTSPOT_DATA = [
  { district: 'Ganjam', lat: 19.3150, lng: 84.7941, active: 412, resolved: 1240, dominantCategory: 'Water Supply', severity: 'Critical' },
  { district: 'Cuttack', lat: 20.4625, lng: 85.8828, active: 289, resolved: 980, dominantCategory: 'Road Infrastructure', severity: 'High' },
  { district: 'Khurda (Bhubaneswar)', lat: 20.2961, lng: 85.8245, active: 380, resolved: 2150, dominantCategory: 'Sanitation', severity: 'Medium' },
  { district: 'Sambalpur', lat: 21.4669, lng: 83.9812, active: 164, resolved: 620, dominantCategory: 'Electricity', severity: 'Medium' },
  { district: 'Balasore', lat: 21.4934, lng: 86.9135, active: 210, resolved: 710, dominantCategory: 'Drainage', severity: 'High' },
  { district: 'Sundargarh (Rourkela)', lat: 22.2604, lng: 84.8536, active: 195, resolved: 830, dominantCategory: 'Public Health', severity: 'Medium' },
  { district: 'Koraput', lat: 18.8135, lng: 82.7118, active: 140, resolved: 410, dominantCategory: 'Ration / PDS', severity: 'Low' },
  { district: 'Puri', lat: 19.8135, lng: 85.8312, active: 175, resolved: 890, dominantCategory: 'Sanitation & Pilgrimage', severity: 'Medium' }
];

