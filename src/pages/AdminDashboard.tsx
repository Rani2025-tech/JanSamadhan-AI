import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Shield,
  BarChart3,
  Users,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  MapPin,
  Filter,
  FileText,
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import { useAuth } from '../context/AuthContext';
import { PLATFORM_STATS, HOTSPOT_DATA } from '../data/mockData';
import { StatusBadge } from '../components/common/StatusBadge';

export const AdminDashboard: React.FC = () => {
  const { complaints } = useComplaints();
  const { user, role, loginAdmin } = useAuth();
  const navigate = useNavigate();

  const [selectedDeptFilter, setSelectedDeptFilter] = useState('All');

  const deptMetrics = [
    { name: 'PHED (Water)', total: 3420, open: 610, resolved: 2810, sla: '95%' },
    { name: 'PWD (Roads)', total: 4180, open: 1120, resolved: 3060, sla: '89%' },
    { name: 'DISCOM (Power)', total: 2890, open: 740, resolved: 2150, sla: '92%' },
    { name: 'Municipal Corp', total: 1990, open: 740, resolved: 1250, sla: '88%' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Admin Header */}
      <div className="bg-gradient-to-r from-maroon-900 via-maroon-800 to-maroon-900 text-white rounded-3xl p-6 sm:p-8 shadow-soft-lg flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-saffron-500/30 text-saffron-300 border border-saffron-400/40 text-xs font-bold uppercase tracking-wider">
            <Shield className="w-3.5 h-3.5" />
            <span>Nodal Officer Command Center</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
            Administrative Grievance Operations
          </h1>
          <p className="text-xs sm:text-sm text-cream-200/80 max-w-xl">
            Live telemetry of civic grievances across India with AI auto-routing and SLA enforcement.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/admin/complaints"
            className="px-5 py-2.5 rounded-full bg-saffron-500 hover:bg-saffron-400 text-white font-bold text-xs sm:text-sm shadow-md transition-colors"
          >
            Manage Grievances
          </Link>
          <Link
            to="/hotspots"
            className="px-5 py-2.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-white font-bold text-xs sm:text-sm transition-colors"
          >
            Hotspot Map
          </Link>
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-3xl p-5 border border-maroon-100 shadow-soft">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase">State Total</span>
            <Users className="w-5 h-5 text-maroon-800" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-gray-900 mt-2">
            {PLATFORM_STATS.totalComplaints.toLocaleString()}
          </div>
          <p className="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+14.2% redressed this month</span>
          </p>
        </div>

        <div className="bg-white rounded-3xl p-5 border border-maroon-100 shadow-soft">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase">Active / In Progress</span>
            <Clock className="w-5 h-5 text-amber-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-amber-600 mt-2">
            {PLATFORM_STATS.openComplaints.toLocaleString()}
          </div>
          <p className="text-[11px] text-gray-500 font-medium mt-1">
            Across 4 key public departments
          </p>
        </div>

        <div className="bg-white rounded-3xl p-5 border border-maroon-100 shadow-soft">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase">Resolved</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-emerald-600 mt-2">
            {PLATFORM_STATS.resolvedComplaints.toLocaleString()}
          </div>
          <p className="text-[11px] text-emerald-700 font-semibold mt-1">
            {PLATFORM_STATS.satisfactionRate}% satisfaction score
          </p>
        </div>

        <div className="bg-white rounded-3xl p-5 border border-maroon-100 shadow-soft">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase">Avg SLA Turnaround</span>
            <AlertTriangle className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-black text-gray-900 mt-2">
            {PLATFORM_STATS.avgResolutionDays} <span className="text-sm font-bold text-gray-500">days</span>
          </div>
          <p className="text-[11px] text-emerald-600 font-semibold mt-1">
            Target SLA: 7.0 days
          </p>
        </div>
      </div>

      {/* Department Breakdown Table & SLA Compliance */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left: Department Breakdown */}
        <div className="lg:col-span-8 bg-white rounded-3xl p-6 border border-maroon-100 shadow-soft space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-extrabold text-gray-900">
              Department Performance & SLA Adherence
            </h2>
            <Link
              to="/admin/complaints"
              className="text-xs font-bold text-maroon-800 hover:underline flex items-center gap-1"
            >
              <span>View All Records</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400 font-bold uppercase tracking-wider">
                  <th className="pb-3">Department</th>
                  <th className="pb-3">Total Complaints</th>
                  <th className="pb-3">Open Backlog</th>
                  <th className="pb-3">Resolved</th>
                  <th className="pb-3">SLA Adherence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-medium text-gray-800">
                {deptMetrics.map(dept => (
                  <tr key={dept.name} className="hover:bg-cream-100/50 transition-colors">
                    <td className="py-3 font-bold text-maroon-900">{dept.name}</td>
                    <td className="py-3">{dept.total.toLocaleString()}</td>
                    <td className="py-3 font-bold text-amber-700">{dept.open.toLocaleString()}</td>
                    <td className="py-3 font-bold text-emerald-700">{dept.resolved.toLocaleString()}</td>
                    <td className="py-3">
                      <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                        {dept.sla}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Real-time Grievance Stream */}
        <div className="lg:col-span-4 bg-white rounded-3xl p-6 border border-maroon-100 shadow-soft space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-extrabold text-gray-900">
              Live Escalations
            </h2>
            <span className="flex h-2 w-2 rounded-full bg-red-600 animate-pulse" />
          </div>

          <div className="space-y-3">
            {complaints.map(comp => (
              <div
                key={comp.id}
                onClick={() => navigate(`/complaints/${comp.id}`)}
                className="p-3.5 rounded-2xl bg-cream-100/60 hover:bg-cream-200 border border-maroon-100/80 transition-colors cursor-pointer space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-maroon-900">{comp.id}</span>
                  <StatusBadge status={comp.status} size="sm" />
                </div>
                <p className="text-xs font-semibold text-gray-800 line-clamp-1">
                  {comp.title}
                </p>
                <div className="flex items-center justify-between text-[11px] text-gray-500">
                  <span>{comp.department}</span>
                  <span>{comp.location.district}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

