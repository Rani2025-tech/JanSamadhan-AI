import React, { useState } from 'react';
import {
  User,
  Phone,
  Mail,
  MapPin,
  Globe,
  Shield,
  Save,
  CheckCircle2,
  Sliders,
  BellRing,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useAccessibility } from '../context/AccessibilityContext';
import { SUPPORTED_LANGUAGES } from '../i18n/languages';
import { INDIA_STATES, ALL_STATE_NAMES } from '../data/indiaLocations';
import { LanguageCode } from '../types';

export const ProfilePage: React.FC = () => {
  const { user, role, updateUserProfile } = useAuth();
  const { currentLanguage, setLanguage, t } = useLanguage();
  const { fontSize, setFontSize, highContrast, toggleHighContrast } = useAccessibility();

  const [name, setName] = useState(user?.name || 'Rani Nayak');
  const [phone, setPhone] = useState(user?.phone || '9876543210');
  const [email, setEmail] = useState(user?.email || 'rani.nayak@example.gov.in');
  
  const initialUserState = user?.state && INDIA_STATES[user.state] ? user.state : 'Odisha';
  const [state, setState] = useState(initialUserState);
  const availableDistricts = INDIA_STATES[state]?.districts || ['Ganjam'];
  const [district, setDistrict] = useState(user?.district || availableDistricts[0] || 'Ganjam');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleStateChange = (newState: string) => {
    setState(newState);
    const districts = INDIA_STATES[newState]?.districts || [];
    setDistrict(districts[0] || '');
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateUserProfile({
      name,
      phone,
      email,
      state,
      district,
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
          <User className="w-8 h-8 text-maroon-800" />
          <span>{t('profile')}</span>
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Manage your personal details, language preference, and notification settings.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Left: User Card & Role */}
        <div className="md:col-span-4 bg-white rounded-3xl p-6 border border-maroon-100 shadow-soft text-center space-y-4">
          <div className="relative inline-block">
            {user?.avatar ? (
              <img
                src={user.avatar}
                alt={name}
                className="w-24 h-24 rounded-full mx-auto object-cover border-4 border-cream-300 shadow-md"
              />
            ) : (
              <div className="w-24 h-24 rounded-full mx-auto bg-maroon-800 text-white flex items-center justify-center text-3xl font-bold border-4 border-cream-300 shadow-md">
                {name.charAt(0)}
              </div>
            )}
            <span className="absolute bottom-1 right-1 w-5 h-5 bg-emerald-500 border-2 border-white rounded-full" />
          </div>

          <div>
            <h2 className="text-lg font-extrabold text-gray-900">{name}</h2>
            <p className="text-xs text-gray-500">{phone || 'Guest Mode'}</p>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-maroon-100 text-maroon-900 text-xs font-bold uppercase tracking-wider">
            <Shield className="w-3.5 h-3.5" />
            <span>Role: {role}</span>
          </div>

          <div className="pt-4 border-t border-gray-100 text-left text-xs space-y-2 text-gray-600">
            <p><strong>Registered ID:</strong> {user?.id || 'USR-8921'}</p>
            <p><strong>District:</strong> {district}</p>
            <p><strong>State:</strong> {state}, India</p>
          </div>
        </div>

        {/* Right: Profile Details Form */}
        <div className="md:col-span-8 bg-white rounded-3xl p-6 sm:p-8 border border-maroon-100 shadow-soft space-y-6">
          <form onSubmit={handleSave} className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <h2 className="text-base font-bold text-gray-900">Personal Information</h2>
              {savedSuccess && (
                <span className="flex items-center gap-1 text-xs text-emerald-600 font-bold animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Changes saved successfully</span>
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700">Mobile Number (+91)</label>
                <input
                  type="text"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring"
                />
              </div>

            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700">State / Union Territory</label>
                <select
                  value={state}
                  onChange={e => handleStateChange(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring bg-white"
                >
                  {ALL_STATE_NAMES.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700">Primary District</label>
                <select
                  value={district}
                  onChange={e => setDistrict(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-900 focus-ring bg-white"
                >
                  {availableDistricts.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Preferred Portal Language */}
            <div className="space-y-2 pt-2">
              <label className="text-xs font-bold text-gray-700 flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-maroon-800" />
                <span>Preferred Language / भाषा</span>
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {SUPPORTED_LANGUAGES.map(l => (
                  <button
                    key={l.code}
                    type="button"
                    onClick={() => setLanguage(l.code)}
                    className={`px-3 py-2 rounded-xl text-xs font-bold border transition-all text-left flex items-center justify-between ${
                      currentLanguage === l.code
                        ? 'bg-maroon-800 text-white border-maroon-800 shadow-xs'
                        : 'bg-cream-100 text-gray-700 border-maroon-100 hover:bg-cream-200'
                    }`}
                  >
                    <span>{l.nativeName}</span>
                    <span className="text-[10px] opacity-75 font-normal">{l.enName}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-maroon-800 hover:bg-maroon-700 text-white font-bold text-sm shadow-md transition-all focus-ring"
              >
                <Save className="w-4 h-4" />
                <span>Save Profile Changes</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

