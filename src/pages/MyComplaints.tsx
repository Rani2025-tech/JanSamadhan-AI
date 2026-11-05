import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search,
  Filter,
  Plus,
  Calendar,
  Briefcase,
  Droplet,
  Globe,
  ChevronRight,
  FileDown,
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import { useLanguage } from '../context/LanguageContext';
import { StatusBadge } from '../components/common/StatusBadge';

export const MyComplaints: React.FC = () => {
  const { complaints, loading } = useComplaints();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [selectedStatus, setSelectedStatus] = useState<string>('All');
  const [selectedDept, setSelectedDept] = useState<string>('All');

  // Filter complaints
  const filtered = complaints.filter(comp => {
    const matchesSearch =
      comp.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      comp.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      comp.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      comp.location.district.toLowerCase().includes(searchQuery.toLowerCase()) ||
      comp.department.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      selectedStatus === 'All' ? true : comp.status.toLowerCase() === selectedStatus.toLowerCase();

    const matchesDept =
      selectedDept === 'All' ? true : comp.department === selectedDept;

    return matchesSearch && matchesStatus && matchesDept;
  });

  const departments = ['All', ...Array.from(new Set(complaints.map(c => c.department)))];

  const handleDownloadSummary = () => {
    const content = `JanSamadhan - Grievance Registry Summary\nGenerated: ${new Date().toLocaleString()}\n\n` +
      filtered.map(c => `Ticket: ${c.id}\nTitle: ${c.title}\nDept: ${c.department}\nStatus: ${c.status}\nExpected: ${c.expectedDate}\n-----------------------`).join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `JanSamadhan_Complaints_${Date.now()}.txt`;
    a.click();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
            {t('navMyComplaints')}
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Track real-time progress, service level agreements (SLA), and official action notes.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleDownloadSummary}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-maroon-200 text-maroon-800 text-xs sm:text-sm font-semibold hover:bg-cream-100 shadow-xs focus-ring"
          >
            <FileDown className="w-4 h-4" />
            <span>Export Summary</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/assistant')}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-maroon-800 text-white text-xs sm:text-sm font-bold hover:bg-maroon-700 shadow-sm focus-ring"
          >
            <Plus className="w-4 h-4" />
            <span>File New Grievance</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-maroon-100 shadow-soft space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search by ID, keyword, district or department..."
              className="w-full pl-10 pr-4 py-2.5 bg-cream-100/60 border border-maroon-100 rounded-2xl text-sm focus-ring text-gray-900 placeholder-gray-400"
            />
          </div>

          {/* Department dropdown filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={selectedDept}
              onChange={e => setSelectedDept(e.target.value)}
              className="bg-cream-100/60 border border-maroon-100 rounded-2xl px-4 py-2.5 text-xs sm:text-sm font-semibold text-gray-700 focus-ring"
            >
              {departments.map(d => (
                <option key={d} value={d}>
                  {d === 'All' ? 'All Departments' : d}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Status Pill Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          {['All', 'In Progress', 'Assigned', 'Submitted', 'Resolved'].map(st => {
            const isSelected = selectedStatus === st;
            return (
              <button
                key={st}
                type="button"
                onClick={() => setSelectedStatus(st)}
                className={`px-4 py-1.5 rounded-full font-bold transition-all focus-ring whitespace-nowrap ${
                  isSelected
                    ? 'bg-maroon-800 text-white shadow-sm'
                    : 'bg-cream-200/80 text-gray-700 hover:bg-cream-300'
                }`}
              >
                {st}
              </button>
            );
          })}
        </div>
      </div>

      {/* Complaints List */}
      <div className="space-y-4">
        {loading ? (
          <div className="space-y-4">
            <div className="bg-white rounded-3xl p-8 border border-maroon-100 animate-pulse h-32" />
            <div className="bg-white rounded-3xl p-8 border border-maroon-100 animate-pulse h-32" />
          </div>
        ) : complaints.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border border-maroon-100 shadow-soft space-y-4">
            <div className="w-14 h-14 rounded-full bg-cream-200 text-maroon-800 flex items-center justify-center mx-auto shadow-xs">
              <FileDown className="w-7 h-7" />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-extrabold text-gray-900">No complaints yet. File your first grievance</h3>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                You haven't filed any grievances yet. Once submitted, your ticket timeline and status will be tracked here.
              </p>
            </div>
            <div className="pt-2 flex items-center justify-center gap-3 flex-wrap">
              <button
                type="button"
                onClick={() => navigate('/assistant')}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-maroon-800 text-white text-xs sm:text-sm font-bold hover:bg-maroon-700 shadow-sm transition-all"
              >
                <span>File via AI Assistant</span>
              </button>
              <button
                type="button"
                onClick={() => navigate('/file-form')}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white border border-maroon-200 text-maroon-900 text-xs sm:text-sm font-bold hover:bg-cream-100 shadow-xs transition-all"
              >
                <span>File via Form</span>
              </button>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border border-maroon-100 shadow-soft space-y-3">
            <div className="w-12 h-12 rounded-full bg-cream-200 text-maroon-800 flex items-center justify-center mx-auto">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-gray-900">No grievances found</h3>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              No matching complaints found for your filters. Try clearing your search or status selection.
            </p>
          </div>
        ) : (
          filtered.map(comp => (
            <div
              key={comp.id}
              onClick={() => navigate(`/complaints/${comp.id}`)}
              className="bg-white rounded-3xl p-5 sm:p-6 border border-maroon-100 shadow-soft hover:shadow-soft-lg hover:border-maroon-300 transition-all duration-200 cursor-pointer group space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="text-base font-extrabold text-maroon-900 group-hover:underline">
                    {comp.id}
                  </span>
                  <StatusBadge status={comp.status} size="md" />
                  <span className="text-xs text-gray-500">
                    Filed on: <strong>{comp.submittedDate}</strong>
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-gray-400" />
                    <span>SLA: <strong>{comp.expectedDate}</strong></span>
                  </span>
                  {comp.status !== 'Resolved' && (
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 font-bold text-xs">
                      {comp.daysRemaining} days left
                    </span>
                  )}
                </div>
              </div>

              <div>
                <h2 className="text-base font-bold text-gray-900 group-hover:text-maroon-900">
                  {comp.title}
                </h2>
                <p className="text-xs sm:text-sm text-gray-600 mt-1 line-clamp-2">
                  {comp.description}
                </p>
              </div>

              {/* Chips + Action */}
              <div className="flex items-center justify-between pt-2 border-t border-gray-100 flex-wrap gap-2 text-xs">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                    <Briefcase className="w-3.5 h-3.5" />
                    <span>{comp.department}</span>
                  </span>

                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-cyan-50 text-cyan-700 font-semibold border border-cyan-200">
                    <Droplet className="w-3.5 h-3.5" />
                    <span>{comp.category}</span>
                  </span>

                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-purple-50 text-purple-700 font-semibold border border-purple-200">
                    <Globe className="w-3.5 h-3.5" />
                    <span>{comp.language}</span>
                  </span>

                  <span className="text-gray-500 font-medium">
                    📍 {comp.location.area}, {comp.location.district}
                  </span>
                </div>

                <div className="flex items-center gap-1 text-maroon-800 font-bold group-hover:translate-x-1 transition-transform">
                  <span>View Details & Timeline</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

