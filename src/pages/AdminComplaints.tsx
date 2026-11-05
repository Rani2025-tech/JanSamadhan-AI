import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  Search,
  AlertTriangle,
  X,
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { Complaint, ComplaintStatus } from '../types';

export const AdminComplaints: React.FC = () => {
  const { complaints, updateStatus, adminUpdateComplaint } = useComplaints();
  const navigate = useNavigate();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [deptFilter, setDeptFilter] = useState('All');
  const [stateFilter, setStateFilter] = useState('All');

  // Edit / status update modal
  const [selectedComp, setSelectedComp] = useState<Complaint | null>(null);
  const [newStatus, setNewStatus] = useState<ComplaintStatus>('In Progress');
  const [editCategory, setEditCategory] = useState('');
  const [editDepartment, setEditDepartment] = useState('');
  const [officerNote, setOfficerNote] = useState('');

  const uniqueStates = Array.from(new Set(complaints.map(c => c.location.state || 'Odisha'))).sort();

  const filtered = complaints.filter(c => {
    const compState = c.location.state || 'Odisha';
    const matchSearch =
      c.id.toLowerCase().includes(search.toLowerCase()) ||
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.location.district.toLowerCase().includes(search.toLowerCase()) ||
      compState.toLowerCase().includes(search.toLowerCase()) ||
      c.department.toLowerCase().includes(search.toLowerCase());

    const matchStatus = statusFilter === 'All' ? true : c.status === statusFilter;
    const matchDept = deptFilter === 'All' ? true : c.department === deptFilter;
    const matchState = stateFilter === 'All' ? true : compState === stateFilter;

    return matchSearch && matchStatus && matchDept && matchState;
  });

  const handleOpenActionModal = (comp: Complaint) => {
    setSelectedComp(comp);
    setNewStatus(comp.status);
    setEditCategory(comp.category);
    setEditDepartment(comp.department);
    setOfficerNote('');
  };

  const handleSaveAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedComp || !officerNote.trim()) return;

    if (editCategory !== selectedComp.category || editDepartment !== selectedComp.department) {
      await adminUpdateComplaint(selectedComp.id, {
        category: editCategory,
        department: editDepartment,
      });
    }

    await updateStatus(selectedComp.id, newStatus, officerNote, 'Duty Officer Alok Mohapatra');
    setSelectedComp(null);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
            <Shield className="w-8 h-8 text-maroon-800" />
            <span>Grievance Redressal Registry (Admin)</span>
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Review, reassign, update operational status, and inspect SLA compliance across all citizen tickets.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-maroon-100 shadow-soft flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by Ticket ID, Citizen area, Department..."
            className="w-full pl-10 pr-4 py-2.5 rounded-2xl bg-cream-100/60 border border-maroon-100 text-sm focus-ring"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={stateFilter}
            onChange={e => setStateFilter(e.target.value)}
            className="px-4 py-2.5 rounded-2xl bg-cream-100/60 border border-maroon-100 text-xs sm:text-sm font-semibold text-gray-700 focus-ring"
          >
            <option value="All">All States</option>
            {uniqueStates.map(st => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-4 py-2.5 rounded-2xl bg-cream-100/60 border border-maroon-100 text-xs sm:text-sm font-semibold text-gray-700 focus-ring"
          >
            <option value="All">All Statuses</option>
            <option value="Submitted">Submitted</option>
            <option value="Assigned">Assigned</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
          </select>

          <select
            value={deptFilter}
            onChange={e => setDeptFilter(e.target.value)}
            className="px-4 py-2.5 rounded-2xl bg-cream-100/60 border border-maroon-100 text-xs sm:text-sm font-semibold text-gray-700 focus-ring"
          >
            <option value="All">All Departments</option>
            <option value="PHED">PHED</option>
            <option value="PWD">PWD</option>
            <option value="DISCOM">DISCOM</option>
          </select>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-3xl border border-maroon-100 shadow-soft overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead>
              <tr className="bg-cream-100/80 border-b border-maroon-100 text-maroon-900 font-bold uppercase tracking-wider text-[11px]">
                <th className="py-3.5 px-4">Ticket ID</th>
                <th className="py-3.5 px-4">Grievance & Location</th>
                <th className="py-3.5 px-4">Dept / Category</th>
                <th className="py-3.5 px-4">Urgency</th>
                <th className="py-3.5 px-4">SLA Deadline</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map(comp => (
                <tr key={comp.id} className="hover:bg-cream-50 transition-colors">
                  <td className="py-4 px-4 font-extrabold text-maroon-900 whitespace-nowrap">
                    {comp.id}
                  </td>
                  <td className="py-4 px-4 max-w-xs">
                    <div className="font-bold text-gray-900 line-clamp-1">{comp.title}</div>
                    <div className="text-xs text-gray-500">
                      {comp.location.area}, {comp.location.district}{comp.location.state ? ` (${comp.location.state})` : ''}
                    </div>
                    {(comp.needs_human_review || (comp.ai_confidence !== undefined && comp.ai_confidence < 0.60)) && (
                      <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                        <AlertTriangle className="w-2.5 h-2.5 text-amber-700" />
                        Needs Human Review
                      </span>
                    )}
                  </td>
                  <td className="py-4 px-4 whitespace-nowrap">
                    <span className="font-bold text-blue-800">{comp.department}</span>
                    <div className="text-xs text-gray-500">{comp.category}</div>
                  </td>
                  <td className="py-4 px-4 whitespace-nowrap">
                    <StatusBadge status={comp.urgency} size="sm" />
                  </td>
                  <td className="py-4 px-4 whitespace-nowrap text-xs">
                    <div className="font-bold text-gray-800">{comp.expectedDate}</div>
                    {comp.status !== 'Resolved' && (
                      <span className="text-amber-800 font-semibold">{comp.daysRemaining} days left</span>
                    )}
                  </td>
                  <td className="py-4 px-4 whitespace-nowrap">
                    <StatusBadge status={comp.status} size="sm" />
                  </td>
                  <td className="py-4 px-4 text-right whitespace-nowrap space-x-2">
                    <button
                      type="button"
                      onClick={() => handleOpenActionModal(comp)}
                      className="px-3 py-1.5 rounded-full bg-maroon-800 text-white font-bold text-xs hover:bg-maroon-700 shadow-xs focus-ring"
                    >
                      Update
                    </button>
                    <button
                      type="button"
                      onClick={() => navigate(`/complaints/${comp.id}`)}
                      className="px-3 py-1.5 rounded-full bg-cream-200 text-maroon-900 font-bold text-xs hover:bg-cream-300 focus-ring"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action Update Modal */}
      {selectedComp && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl border border-maroon-200 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-maroon-800" />
                <h3 className="font-bold text-base text-gray-900">
                  Update Grievance {selectedComp.id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedComp(null)}
                className="p-1 rounded-full text-gray-400 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs text-gray-700 bg-cream-100 p-4 rounded-2xl space-y-2 border border-maroon-100">
              <div className="flex items-center justify-between">
                <span className="font-bold text-maroon-900">Original Title: {selectedComp.title}</span>
                {selectedComp.ai_confidence && (
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[11px] border border-emerald-300">
                    AI Confidence: {Math.round(selectedComp.ai_confidence * 100)}%
                  </span>
                )}
              </div>

              {selectedComp.translated_text_en && (
                <div className="p-2.5 bg-white rounded-xl border border-maroon-100/60 text-xs">
                  <span className="font-bold text-gray-900 block mb-0.5">🌐 English Translation:</span>
                  <p className="text-gray-700 italic">"{selectedComp.translated_text_en}"</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 pt-1 text-[11px] text-gray-600">
                <p><strong>Location:</strong> {selectedComp.location.area}, {selectedComp.location.district}</p>
                <p><strong>Department:</strong> {selectedComp.department}</p>
                {selectedComp.sentiment && (
                  <p><strong>Citizen Sentiment:</strong> <span className="font-bold text-amber-800">{selectedComp.sentiment}</span></p>
                )}
                <p><strong>Language:</strong> {selectedComp.language}</p>
              </div>
            </div>

            <form onSubmit={handleSaveAction} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-700 uppercase">Category</label>
                  <select
                    value={editCategory}
                    onChange={e => setEditCategory(e.target.value)}
                    className="w-full p-2.5 rounded-2xl border border-gray-200 text-xs font-semibold text-gray-900 focus-ring"
                  >
                    <option value="Water Supply">Water Supply</option>
                    <option value="Road Infrastructure">Road Infrastructure</option>
                    <option value="Electricity">Electricity</option>
                    <option value="Sanitation">Sanitation</option>
                    <option value="Public Health">Public Health</option>
                    <option value="Ration / PDS">Ration / PDS</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-700 uppercase">Department</label>
                  <select
                    value={editDepartment}
                    onChange={e => setEditDepartment(e.target.value)}
                    className="w-full p-2.5 rounded-2xl border border-gray-200 text-xs font-semibold text-gray-900 focus-ring"
                  >
                    <option value="PHED">PHED</option>
                    <option value="PWD">PWD</option>
                    <option value="DISCOM">DISCOM</option>
                    <option value="Municipal Corp">Municipal Corp</option>
                    <option value="Health & Family Welfare">Health & Family Welfare</option>
                    <option value="Food Supplies & Consumer Welfare">Food Supplies & Consumer Welfare</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700 uppercase">Set New Status</label>
                <select
                  value={newStatus}
                  onChange={e => setNewStatus(e.target.value as ComplaintStatus)}
                  className="w-full p-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring"
                >
                  <option value="Submitted">Submitted</option>
                  <option value="Assigned">Assigned</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700 uppercase">Officer Action Remark</label>
                <textarea
                  required
                  rows={3}
                  value={officerNote}
                  onChange={e => setOfficerNote(e.target.value)}
                  placeholder="e.g. Field inspection completed. Valve repaired and water pressure restored."
                  className="w-full p-3 rounded-2xl border border-gray-200 text-xs text-gray-900 focus-ring"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedComp(null)}
                  className="px-4 py-2.5 rounded-full bg-gray-100 text-gray-700 font-bold text-xs hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-full bg-maroon-800 text-white font-bold text-xs hover:bg-maroon-700 shadow-xs focus-ring"
                >
                  Save & Publish Status
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

