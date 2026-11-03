import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FilePlus2,
  Upload,
  Mic,
  CheckCircle2,
  AlertCircle,
  Building2,
  MapPin,
  Clock,
  Compass,
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { useComplaints } from '../context/ComplaintContext';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { INDIA_STATES, ALL_STATE_NAMES } from '../data/indiaLocations';
import { UrgencyLevel } from '../types';

export const FileComplaintForm: React.FC = () => {
  const { createComplaint } = useComplaints();
  const { currentLanguageOption, t } = useLanguage();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Water Supply');
  const [urgency, setUrgency] = useState<UrgencyLevel>('Medium');
  
  const initialUserState = user?.state && INDIA_STATES[user.state] ? user.state : 'Odisha';
  const [selectedState, setSelectedState] = useState(initialUserState);
  const availableDistricts = INDIA_STATES[selectedState]?.districts || ['Ganjam'];
  const [district, setDistrict] = useState(user?.district || availableDistricts[0] || 'Ganjam');
  const [area, setArea] = useState('');
  const [pincode, setPincode] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleStateChange = (newState: string) => {
    setSelectedState(newState);
    const districts = INDIA_STATES[newState]?.districts || [];
    setDistrict(districts[0] || '');
  };

  // Department auto-mapping
  const getMappedDepartment = (cat: string) => {
    switch (cat) {
      case 'Water Supply':
        return 'PHED';
      case 'Road Infrastructure':
        return 'PWD';
      case 'Electricity':
        return 'DISCOM';
      case 'Sanitation':
        return 'Municipal Corporation';
      case 'Public Health':
        return 'Health & Family Welfare';
      case 'Ration / PDS':
        return 'Food Supplies & Consumer Welfare';
      default:
        return 'General Administration';
    }
  };

  const department = getMappedDepartment(category);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim() || !area.trim()) {
      setError('Please fill in all required fields (Title, Description, and Area/Location).');
      return;
    }

    setSubmitting(true);
    setError('');

    setTimeout(async () => {
      try {
        const newTicket = await createComplaint({
          title,
          description,
          category,
          department,
          urgency,
          language: currentLanguageOption.enName,
          state: selectedState,
          district,
          area,
          pincode,
        });

        confetti({
          particleCount: 70,
          spread: 60,
          origin: { y: 0.6 },
          colors: ['#7A0F2E', '#F28C28', '#2563EB', '#16A34A'],
        });

        navigate(`/complaints/${newTicket.id}`);
      } catch (err: any) {
        setError(err.message || 'Failed to submit grievance');
        setSubmitting(false);
      }
    }, 400);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300 pb-16">
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
          <FilePlus2 className="w-8 h-8 text-maroon-800" />
          <span>{t('fileViaFormTitle')}</span>
        </h1>
        <p className="text-sm text-gray-600">
          Submit your citizen grievance manually with complete documentation and location details.
        </p>
      </div>

      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-maroon-100 shadow-soft">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-2.5 text-xs text-red-700 font-semibold">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Grievance Title */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
              Grievance Summary / Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="e.g. Drinking water pipeline broken and leaking on main street"
              className="w-full px-4 py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring"
            />
          </div>

          {/* Category & Mapped Department */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                Category <span className="text-red-500">*</span>
              </label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring bg-white"
              >
                <option value="Water Supply">💧 Water Supply (Drinking / Pipeline)</option>
                <option value="Road Infrastructure">🚧 Road Infrastructure (Potholes / Bridges)</option>
                <option value="Electricity">⚡ Electricity & Streetlights</option>
                <option value="Sanitation">🧹 Sanitation & Solid Waste</option>
                <option value="Public Health">🏥 Public Health & Sanitation</option>
                <option value="Ration / PDS">🌾 Ration / Public Distribution (PDS)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                Auto-Assigned Department
              </label>
              <div className="flex items-center gap-2.5 px-4 py-3 rounded-2xl bg-cream-100 border border-maroon-100 text-sm font-bold text-maroon-900">
                <Building2 className="w-4 h-4 text-maroon-800" />
                <span>{department}</span>
                <span className="text-[11px] text-gray-500 font-normal ml-auto">Auto-routed</span>
              </div>
            </div>
          </div>

          {/* Urgency and SLA preview */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                Urgency Level
              </label>
              <select
                value={urgency}
                onChange={e => setUrgency(e.target.value as UrgencyLevel)}
                className="w-full px-4 py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring bg-white"
              >
                <option value="Low">Low (Standard SLA: 10 days)</option>
                <option value="Medium">Medium (Standard SLA: 7 days)</option>
                <option value="High">High (Standard SLA: 3 days)</option>
                <option value="Critical">Critical (Standard SLA: 24 hours)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                Estimated SLA Resolution
              </label>
              <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-cream-100 border border-maroon-100 text-sm font-bold text-amber-900">
                <Clock className="w-4 h-4 text-amber-700" />
                <span>
                  {urgency === 'Critical' ? '24 Hours' : urgency === 'High' ? '3 Days' : '7 Days'} Redressal Target
                </span>
              </div>
            </div>
          </div>

          {/* Location details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                State / UT <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedState}
                onChange={e => handleStateChange(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring bg-white"
              >
                {ALL_STATE_NAMES.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                District <span className="text-red-500">*</span>
              </label>
              <select
                value={district}
                onChange={e => setDistrict(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring bg-white"
              >
                {availableDistricts.map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-1.5 sm:col-span-2">
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                Area / Ward / Street Landmark <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  required
                  value={area}
                  onChange={e => setArea(e.target.value)}
                  placeholder="e.g. Ward 12, Kothrud, Near Bus Stand"
                  className="w-full pl-10 pr-4 py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                Pincode (Optional)
              </label>
              <input
                type="text"
                value={pincode}
                onChange={e => setPincode(e.target.value)}
                placeholder="e.g. 751024"
                className="w-full px-4 py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring"
              />
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
              Detailed Grievance Description <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              rows={4}
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Describe what has happened, when the issue started, and any impact on residents..."
              className="w-full p-4 rounded-2xl border border-gray-200 text-sm text-gray-900 focus-ring"
            />
          </div>

          {/* File Upload Attachment */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
              Supporting Photo / Document / Audio Note (Optional)
            </label>
            <div className="border-2 border-dashed border-maroon-200 rounded-2xl p-6 text-center hover:bg-cream-100/50 transition-colors">
              <Upload className="w-8 h-8 text-maroon-800 mx-auto mb-2 opacity-80" />
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={e => setSelectedFile(e.target.files?.[0] || null)}
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer text-xs sm:text-sm font-bold text-maroon-800 hover:underline"
              >
                {selectedFile ? `Attached: ${selectedFile.name}` : 'Click to upload photo or document (PNG, JPG, PDF up to 10MB)'}
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-4 px-6 rounded-2xl bg-maroon-800 hover:bg-maroon-700 disabled:opacity-50 text-white font-extrabold text-sm sm:text-base tracking-wide shadow-md transition-all flex items-center justify-center gap-2 focus-ring"
            >
              {submitting ? (
                <span className="inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Submit Formal Grievance</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

