import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Briefcase,
  MapPin,
  User,
  Phone,
  ShieldCheck,
  FileCheck2,
  Printer,
  Star,
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  Send,
} from 'lucide-react';
import { useComplaints } from '../context/ComplaintContext';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { ComplaintStatus } from '../types';

export const ComplaintDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { getComplaintById, updateStatus, submitFeedback } = useComplaints();
  const { role, user } = useAuth();
  const { t } = useLanguage();

  const complaint = getComplaintById(id || '');

  // Admin status update modal / form state
  const [adminStatus, setAdminStatus] = useState<ComplaintStatus>('In Progress');
  const [adminNote, setAdminNote] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  // Feedback state for citizen on resolved ticket
  const [rating, setRating] = useState(complaint?.feedback?.rating || 5);
  const [feedbackComment, setFeedbackComment] = useState(complaint?.feedback?.comment || '');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(!!complaint?.feedback);

  if (!complaint) {
    return (
      <div className="bg-white rounded-3xl p-12 text-center border border-maroon-100 shadow-soft space-y-4 max-w-xl mx-auto my-12">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
        <h2 className="text-xl font-bold text-gray-900">Grievance Not Found</h2>
        <p className="text-sm text-gray-500">
          The requested complaint ID <strong className="text-maroon-800">{id}</strong> does not exist in the system.
        </p>
        <button
          onClick={() => navigate('/complaints')}
          className="px-6 py-2.5 rounded-full bg-maroon-800 text-white font-bold text-sm"
        >
          Back to Grievance List
        </button>
      </div>
    );
  }

  const handleAdminUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminNote.trim()) {
      alert('Please enter an action remark.');
      return;
    }
    setIsUpdating(true);
    setTimeout(() => {
      updateStatus(complaint.id, adminStatus, adminNote, user?.name || 'Authorized Officer');
      setIsUpdating(false);
      setAdminNote('');
      alert(`Grievance ${complaint.id} status updated to ${adminStatus}!`);
    }, 500);
  };

  const handleFeedbackSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitFeedback(complaint.id, rating, feedbackComment);
    setFeedbackSubmitted(true);
    alert('Thank you for rating the grievance redressal service!');
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-xs sm:text-sm font-bold text-maroon-800 hover:text-maroon-900 hover:underline focus-ring rounded-lg px-2 py-1"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{t('backToDashboard')}</span>
        </button>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-maroon-200 text-maroon-900 text-xs sm:text-sm font-semibold hover:bg-cream-100 shadow-xs focus-ring"
          >
            <Printer className="w-4 h-4" />
            <span>Print Acknowledgment</span>
          </button>
        </div>
      </div>

      {/* Main Ticket Banner */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-maroon-100 shadow-soft space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-100">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-2xl font-black text-maroon-900">{complaint.id}</span>
              <StatusBadge status={complaint.status} size="lg" />
              <StatusBadge status={complaint.urgency} size="sm" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 pt-1">
              {complaint.title}
            </h1>
          </div>

          <div className="bg-cream-100 border border-maroon-100 p-3.5 rounded-2xl text-xs space-y-1 flex-shrink-0">
            <div className="text-gray-500">Service Level Agreement (SLA):</div>
            <div className="font-bold text-gray-900 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-maroon-800" />
              <span>Target: {complaint.expectedDate}</span>
            </div>
            {complaint.status !== 'Resolved' ? (
              <div className="text-amber-800 font-bold">
                ⏳ {complaint.daysRemaining} days remaining
              </div>
            ) : (
              <div className="text-emerald-700 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Resolved within SLA timeline</span>
              </div>
            )}
          </div>
        </div>

        {/* Timeline Stepper from StatusHistory */}
        <div className="space-y-4">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <Clock className="w-4 h-4 text-maroon-800" />
            <span>Official Redressal Timeline (Status History)</span>
          </h2>

          <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-2 before:bottom-2 before:w-[2px] before:bg-maroon-200">
            {complaint.statusHistory.map((step, idx) => {
              const isDone = step.completed;
              return (
                <div key={idx} className="relative group">
                  {/* Step circle */}
                  <div
                    className={`absolute -left-6 sm:-left-8 top-1 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-xs ${
                      isDone
                        ? 'bg-maroon-800 text-white'
                        : 'bg-white border-2 border-gray-300 text-gray-400'
                    }`}
                  >
                    {isDone ? '✓' : idx + 1}
                  </div>

                  {/* Step details */}
                  <div className="bg-cream-100/60 p-4 rounded-2xl border border-maroon-100/80 space-y-1">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <span className="font-extrabold text-sm text-gray-900">
                        {step.status}
                      </span>
                      <span className="text-xs font-semibold text-gray-500">
                        {step.date} {step.time ? `• ${step.time}` : ''}
                      </span>
                    </div>

                    <p className="text-xs sm:text-sm text-gray-700">{step.note}</p>

                    {step.officer && (
                      <div className="pt-1 text-xs text-maroon-900 font-semibold flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                        <span>Action By: {step.officer}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detailed Metadata Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-100">
          {/* Grievance Details */}
          <div className="bg-cream-100/50 p-4 rounded-2xl border border-maroon-100/60 space-y-2">
            <h3 className="font-bold text-xs uppercase tracking-wider text-gray-500">
              Grievance Details
            </h3>
            <div className="text-xs space-y-1.5 text-gray-700">
              <p><strong>Department:</strong> {complaint.department}</p>
              <p><strong>Category:</strong> {complaint.category}</p>
              <p><strong>Primary Language:</strong> {complaint.language}</p>
              <p><strong>Location:</strong> {complaint.location.area}, {complaint.location.district} (PIN: {complaint.location.pincode || 'N/A'})</p>
              <p><strong>Description:</strong> {complaint.description}</p>
            </div>
          </div>

          {/* Assigned Officer / Nodal Unit */}
          <div className="bg-cream-100/50 p-4 rounded-2xl border border-maroon-100/60 space-y-2">
            <h3 className="font-bold text-xs uppercase tracking-wider text-gray-500">
              Assigned Nodal Officer
            </h3>
            {complaint.assignedOfficer ? (
              <div className="text-xs space-y-1.5 text-gray-700">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-maroon-800" />
                  <span className="font-bold text-gray-900">{complaint.assignedOfficer.name}</span>
                </div>
                <p className="text-gray-600">{complaint.assignedOfficer.designation}</p>
                <p className="text-gray-600">{complaint.assignedOfficer.department}</p>
                {complaint.assignedOfficer.phone && (
                  <p className="text-maroon-800 font-semibold flex items-center gap-1">
                    <Phone className="w-3 h-3" />
                    <span>{complaint.assignedOfficer.phone}</span>
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic">Automated routing in progress to department desk.</p>
            )}
          </div>
        </div>

        {/* CITIZEN FEEDBACK SECTION (If resolved) */}
        {complaint.status === 'Resolved' && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
              <FileCheck2 className="w-5 h-5 text-emerald-700" />
              <span>Citizen Redressal Satisfaction Rating</span>
            </div>

            {feedbackSubmitted ? (
              <div className="text-xs text-emerald-800 space-y-1">
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map(star => (
                    <Star
                      key={star}
                      className={`w-4 h-4 ${star <= rating ? 'fill-amber-400 text-amber-400' : 'text-gray-300'}`}
                    />
                  ))}
                  <span className="font-bold ml-2">{rating}/5 Stars</span>
                </div>
                {feedbackComment && <p className="italic">"{feedbackComment}"</p>}
                <p className="text-[11px] text-emerald-700 pt-1 font-semibold">
                  Thank you! Your feedback helps us maintain quality governance.
                </p>
              </div>
            ) : (
              <form onSubmit={handleFeedbackSubmit} className="space-y-3">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-gray-700 font-medium">Your rating:</span>
                  {[1, 2, 3, 4, 5].map(star => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="p-1 focus-ring rounded"
                    >
                      <Star
                        className={`w-5 h-5 ${star <= rating ? 'fill-amber-400 text-amber-400' : 'text-gray-300'}`}
                      />
                    </button>
                  ))}
                </div>

                <textarea
                  value={feedbackComment}
                  onChange={e => setFeedbackComment(e.target.value)}
                  placeholder="Share remarks on how well the grievance was redressed..."
                  rows={2}
                  className="w-full text-xs p-3 rounded-xl border border-emerald-300 bg-white focus-ring"
                />

                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-700 text-white font-bold rounded-xl text-xs hover:bg-emerald-800 shadow-xs focus-ring"
                >
                  Submit Citizen Feedback
                </button>
              </form>
            )}
          </div>
        )}

        {/* OFFICER / ADMIN ACTION PANEL (If role is admin) */}
        {role === 'admin' && (
          <div className="bg-maroon-50 border border-maroon-200 rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-maroon-900 font-bold text-sm">
              <ShieldCheck className="w-5 h-5 text-maroon-800" />
              <span>Officer Administrative Override & Status Update</span>
            </div>

            <form onSubmit={handleAdminUpdate} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
              <div className="md:col-span-4 space-y-1">
                <label className="text-xs font-bold text-gray-700">Update Status</label>
                <select
                  value={adminStatus}
                  onChange={e => setAdminStatus(e.target.value as ComplaintStatus)}
                  className="w-full p-2.5 rounded-xl border border-maroon-200 bg-white text-xs font-semibold focus-ring"
                >
                  <option value="Submitted">Submitted</option>
                  <option value="Assigned">Assigned</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </div>

              <div className="md:col-span-6 space-y-1">
                <label className="text-xs font-bold text-gray-700">Official Action Note</label>
                <input
                  type="text"
                  value={adminNote}
                  onChange={e => setAdminNote(e.target.value)}
                  placeholder="e.g. Field inspection completed, valves repaired."
                  className="w-full p-2.5 rounded-xl border border-maroon-200 bg-white text-xs focus-ring"
                />
              </div>

              <div className="md:col-span-2">
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="w-full py-2.5 px-4 bg-maroon-800 hover:bg-maroon-700 text-white font-bold text-xs rounded-xl shadow-xs focus-ring flex items-center justify-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Update</span>
                </button>
              </div>
            </form>
          </div>
        )}

      </div>
    </div>
  );
};

