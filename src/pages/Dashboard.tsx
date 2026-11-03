import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Users,
  Clock,
  CheckCircle2,
  Calendar,
  MessageSquare,
  Mic,
  Bot,
  FileEdit,
  ChevronRight,
  ArrowRight,
  Droplet,
  Flame,
  Globe,
  Briefcase,
  AlertTriangle,
  Radio,
  Check,
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useComplaints } from '../context/ComplaintContext';
import { useNotifications } from '../context/NotificationContext';
import { BuildingIllustration } from '../components/common/BuildingIllustration';
import { StatusBadge } from '../components/common/StatusBadge';

export const Dashboard: React.FC = () => {
  const { t } = useLanguage();
  const { complaints, userStats } = useComplaints();
  const { userUpdates, announcements } = useNotifications();
  const navigate = useNavigate();

  // Primary active complaint for stepper timeline
  const activeComplaint = complaints.find(c => c.status === 'In Progress') || complaints[0];

  // Helper to extract date from status history
  const getStatusDate = (statusKey: string) => {
    if (!activeComplaint) return '—';
    const item = activeComplaint.statusHistory.find(h => h.status === statusKey);
    return item?.completed && item.date !== 'Pending' ? item.date : '—';
  };

  // 3 Complaint rows as required by note 7
  const displayComplaints = complaints.slice(0, 3);

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-12">
      {/* 1. HERO BANNER */}
      <div className="relative bg-gradient-to-r from-cream-300 via-cream-200 to-cream-300 rounded-3xl p-6 sm:p-8 border border-maroon-100 shadow-sm overflow-hidden">
        {/* Subtle architectural building background on the right */}
        <div className="absolute right-0 bottom-0 w-2/5 sm:w-1/3 max-w-[340px] opacity-40 pointer-events-none select-none">
          <BuildingIllustration variant="subtle" className="w-full h-auto" />
        </div>

        <div className="relative z-10 max-w-xl space-y-3">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-maroon-900 tracking-tight">
            {t('dashboardWelcome')}
          </h1>
          <p className="text-sm sm:text-base font-medium text-gray-700">
            {t('dashboardSubtext')}
          </p>

          <div className="pt-2 flex items-center gap-3 flex-wrap">
            <button
              type="button"
              onClick={() => navigate('/assistant')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-maroon-800 hover:bg-maroon-700 text-white text-xs sm:text-sm font-bold shadow-md transition-all duration-200 focus-ring"
            >
              <MessageSquare className="w-4 h-4 fill-white" />
              <span>{t('chatWithAssistant')}</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/assistant?voice=true')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white hover:bg-cream-100 text-maroon-900 border border-maroon-200 text-xs sm:text-sm font-bold shadow-xs transition-all duration-200 focus-ring"
            >
              <Mic className="w-4 h-4 text-maroon-800" />
              <span>{t('speakComplaint')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. QUICK ACTION CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: File via Assistant */}
        <Link
          to="/assistant"
          className="bg-gradient-to-r from-maroon-800 to-maroon-900 text-white rounded-2xl p-5 shadow-soft hover:shadow-soft-lg flex items-center justify-between group transition-all duration-200 focus-ring"
        >
          <div className="flex items-center gap-4">
            <div className="w-13 h-13 rounded-2xl bg-white/15 flex items-center justify-center flex-shrink-0 border border-white/20">
              <Bot className="w-7 h-7 text-saffron-300" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold tracking-tight">
                {t('fileViaAssistantTitle')}
              </h2>
              <p className="text-xs sm:text-sm text-cream-200/80">
                {t('fileViaAssistantDesc')}
              </p>
            </div>
          </div>
          <ChevronRight className="w-6 h-6 text-cream-200 group-hover:translate-x-1 transition-transform" />
        </Link>

        {/* Card 2: File via Form */}
        <Link
          to="/file-form"
          className="bg-white rounded-2xl p-5 border border-maroon-100 shadow-soft hover:shadow-soft-lg flex items-center justify-between group transition-all duration-200 focus-ring"
        >
          <div className="flex items-center gap-4">
            <div className="w-13 h-13 rounded-2xl bg-maroon-50 flex items-center justify-center flex-shrink-0 border border-maroon-200">
              <FileEdit className="w-7 h-7 text-maroon-800" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight">
                {t('fileViaFormTitle')}
              </h2>
              <p className="text-xs sm:text-sm text-gray-600">
                {t('fileViaFormDesc')}
              </p>
            </div>
          </div>
          <ChevronRight className="w-6 h-6 text-maroon-800 group-hover:translate-x-1 transition-transform" />
        </Link>
      </div>

      {/* 3. STATS STRIP (LOGGED-IN USER'S OWN NUMBERS) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total */}
        <div className="bg-white rounded-2xl p-4 sm:p-5 border border-maroon-100 shadow-soft flex items-center gap-4 hover:border-maroon-200 transition-all">
          <div className="w-12 h-12 rounded-2xl bg-maroon-100 flex items-center justify-center flex-shrink-0">
            <Users className="w-6 h-6 text-maroon-800" />
          </div>
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              {t('statTotal')}
            </div>
            <div className="text-2xl font-black text-gray-900">
              {userStats.total}
            </div>
          </div>
        </div>

        {/* Open */}
        <div className="bg-white rounded-2xl p-4 sm:p-5 border border-maroon-100 shadow-soft flex items-center gap-4 hover:border-maroon-200 transition-all">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 flex items-center justify-center flex-shrink-0">
            <Clock className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              {t('statOpen')}
            </div>
            <div className="text-2xl font-black text-gray-900">
              {userStats.open}
            </div>
          </div>
        </div>

        {/* Resolved */}
        <div className="bg-white rounded-2xl p-4 sm:p-5 border border-maroon-100 shadow-soft flex items-center gap-4 hover:border-maroon-200 transition-all">
          <div className="w-12 h-12 rounded-2xl bg-emerald-100 flex items-center justify-center flex-shrink-0">
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              {t('statResolved')}
            </div>
            <div className="text-2xl font-black text-gray-900">
              {userStats.resolved}
            </div>
          </div>
        </div>

        {/* Avg Resolution Time */}
        <div className="bg-white rounded-2xl p-4 sm:p-5 border border-maroon-100 shadow-soft flex items-center gap-4 hover:border-maroon-200 transition-all">
          <div className="w-12 h-12 rounded-2xl bg-blue-100 flex items-center justify-center flex-shrink-0">
            <Calendar className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              {t('statAvgTime')}
            </div>
            <div className="text-2xl font-black text-gray-900">
              {userStats.avgResolutionDays}{' '}
              <span className="text-xs font-bold text-gray-500">{t('statDays')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. MAIN TWO-COLUMN SPLIT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: Your Complaints + Stepper + 3 Rows */}
        <div className="lg:col-span-7 space-y-5">
          <div className="bg-white rounded-3xl p-5 sm:p-6 border border-maroon-100 shadow-soft space-y-6">
            
            {/* Header with "View All ->" link */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-6 bg-maroon-800 rounded-full" />
                <h2 className="text-lg font-black text-gray-900 tracking-tight">
                  {t('yourComplaints')}
                </h2>
              </div>
              <Link
                to="/complaints"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-maroon-800 hover:text-maroon-900 hover:underline focus-ring rounded-lg px-2 py-1"
              >
                <span>{t('viewAll')}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Stepper Progress Bar for latest active complaint */}
            {activeComplaint && (
              <div className="bg-cream-100/60 rounded-2xl p-4 border border-maroon-100/60">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-2 font-medium">
                  <span className="font-bold text-maroon-900">
                    Latest Timeline: {activeComplaint.id}
                  </span>
                  <span className="text-gray-500">
                    Status: <strong className="text-amber-700">{activeComplaint.status}</strong>
                  </span>
                </div>

                {/* Stepper track */}
                <div className="relative flex items-center justify-between mt-3 px-2 sm:px-4">
                  {/* Connecting line */}
                  <div className="absolute left-6 right-6 top-3 h-[2px] bg-gray-200 -z-0" />
                  
                  {/* Step 1: Submitted (Maroon) */}
                  <div className="flex flex-col items-center text-center relative z-10">
                    <div className="w-7 h-7 rounded-full bg-maroon-800 text-white flex items-center justify-center shadow-xs">
                      <Check className="w-4 h-4 stroke-[3]" />
                    </div>
                    <span className="text-xs font-bold text-maroon-900 mt-1.5">
                      {t('statusSubmitted')}
                    </span>
                    <span className="text-[10px] text-gray-500">
                      {getStatusDate('Submitted')}
                    </span>
                  </div>

                  {/* Step 2: Assigned (Blue) */}
                  <div className="flex flex-col items-center text-center relative z-10">
                    <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-xs">
                      <Check className="w-4 h-4 stroke-[3]" />
                    </div>
                    <span className="text-xs font-bold text-blue-900 mt-1.5">
                      {t('statusAssigned')}
                    </span>
                    <span className="text-[10px] text-gray-500">
                      {getStatusDate('Assigned')}
                    </span>
                  </div>

                  {/* Step 3: In Progress (Amber) */}
                  <div className="flex flex-col items-center text-center relative z-10">
                    <div className="w-7 h-7 rounded-full bg-amber-500 text-white flex items-center justify-center shadow-xs ring-4 ring-amber-100">
                      <Clock className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-bold text-amber-700 mt-1.5">
                      {t('statusInProgress')}
                    </span>
                    <span className="text-[10px] text-gray-500">
                      {getStatusDate('In Progress')}
                    </span>
                  </div>

                  {/* Step 4: Resolved (Pending) */}
                  <div className="flex flex-col items-center text-center relative z-10">
                    <div className="w-7 h-7 rounded-full bg-white border-2 border-gray-300 text-gray-400 flex items-center justify-center">
                      <span className="w-2 h-2 rounded-full bg-gray-300" />
                    </div>
                    <span className="text-xs font-medium text-gray-500 mt-1.5">
                      {t('statusResolved')}
                    </span>
                    <span className="text-[10px] text-gray-400">
                      {getStatusDate('Resolved')}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* 3 Complaint Rows (GRV-1042, GRV-0987, GRV-0951) */}
            <div className="space-y-3">
              {displayComplaints.map(comp => {
                const isWater = comp.category.toLowerCase().includes('water');
                return (
                  <div
                    key={comp.id}
                    onClick={() => navigate(`/complaints/${comp.id}`)}
                    className="p-4 rounded-2xl bg-cream-100/50 hover:bg-cream-200/60 border border-maroon-100 hover:border-maroon-300 shadow-xs hover:shadow-soft transition-all duration-200 cursor-pointer group space-y-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        {/* Icon circle */}
                        <div
                          className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 ${
                            isWater ? 'bg-maroon-100 text-maroon-800' : 'bg-saffron-100 text-saffron-800'
                          }`}
                        >
                          {isWater ? <Droplet className="w-5 h-5 fill-current" /> : <Flame className="w-5 h-5" />}
                        </div>

                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-extrabold text-sm text-gray-900 group-hover:text-maroon-900">
                              {comp.id}
                            </span>
                            <StatusBadge status={comp.status} size="sm" />
                          </div>
                          <p className="text-xs sm:text-sm font-semibold text-gray-800 mt-0.5 line-clamp-1">
                            {comp.title}
                          </p>
                          <p className="text-[11px] text-gray-500">
                            {comp.location.area}, {comp.location.district}
                          </p>
                        </div>
                      </div>

                      <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-maroon-800 group-hover:translate-x-1 transition-all flex-shrink-0" />
                    </div>

                    {/* Meta Chips: Department, Category, Urgency, Language */}
                    <div className="flex items-center gap-2 flex-wrap pt-1 text-[11px]">
                      {/* Department Chip */}
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                        <Briefcase className="w-3 h-3" />
                        <span>{comp.department}</span>
                      </span>

                      {/* Category Chip */}
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-cyan-50 text-cyan-700 font-semibold border border-cyan-200">
                        <Droplet className="w-3 h-3" />
                        <span>{comp.category}</span>
                      </span>

                      {/* Urgency Chip */}
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 font-semibold border border-amber-200">
                        <AlertTriangle className="w-3 h-3" />
                        <span>{comp.urgency}</span>
                      </span>

                      {/* Language Chip */}
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 font-semibold border border-purple-200">
                        <Globe className="w-3 h-3" />
                        <span>{comp.language}</span>
                      </span>

                      {/* SLA Countdown & Expected Resolution */}
                      <div className="ml-auto flex items-center gap-2 text-xs">
                        <span className="text-gray-500 flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-gray-400" />
                          <span>{t('expectedResolution')}: <strong>{comp.expectedDate}</strong></span>
                        </span>
                        {comp.status !== 'Resolved' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 font-bold text-[10px]">
                            {comp.daysRemaining} {t('daysLeft')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

          </div>
        </div>

        {/* RIGHT COLUMN: Split into My Updates (User data) + Announcements (Platform news) */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* 1. MY UPDATES (USER DATA FEED) */}
          <div className="bg-white rounded-3xl p-5 sm:p-6 border border-maroon-100 shadow-soft space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-5 bg-maroon-800 rounded-full" />
                <h3 className="font-bold text-gray-900 text-base">
                  {t('myUpdates')}
                </h3>
              </div>
              <Link
                to="/notifications?tab=updates"
                className="text-xs font-bold text-maroon-800 hover:underline inline-flex items-center gap-1"
              >
                <span>{t('viewAll')}</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="space-y-3">
              {userUpdates.length === 0 ? (
                <p className="text-xs text-gray-500 italic">{t('noUpdatesYet')}</p>
              ) : (
                userUpdates.map(item => (
                  <div
                    key={item.id}
                    className="flex gap-3 text-xs leading-relaxed p-2.5 rounded-xl bg-cream-100/50 hover:bg-cream-200 transition-colors"
                  >
                    <span className="w-2 h-2 rounded-full bg-maroon-800 mt-1.5 flex-shrink-0" />
                    <div className="space-y-0.5">
                      <p className="font-semibold text-gray-900">{item.message}</p>
                      <p className="text-[10px] text-gray-500">{item.timestamp}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 2. ANNOUNCEMENTS (PLATFORM NEWS - FUTURE DATE REQUIREMENT) */}
          <div className="bg-white rounded-3xl p-5 sm:p-6 border border-maroon-100 shadow-soft space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-5 bg-saffron-500 rounded-full" />
                <h3 className="font-bold text-gray-900 text-base">
                  {t('announcements')}
                </h3>
              </div>
              <span className="text-[11px] font-bold text-saffron-700 bg-saffron-50 px-2 py-0.5 rounded-full border border-saffron-200">
                Official
              </span>
            </div>

            <div className="space-y-3">
              {announcements.map(ann => (
                <div
                  key={ann.id}
                  className="flex gap-3 text-xs leading-relaxed p-2.5 rounded-xl bg-saffron-50/40 border border-saffron-100 hover:bg-saffron-50/70 transition-colors"
                >
                  <Radio className="w-4 h-4 text-saffron-600 flex-shrink-0 mt-0.5" />
                  <div className="space-y-0.5">
                    <p className="font-semibold text-gray-900">{ann.message}</p>
                    <p className="text-[10px] text-gray-500">{ann.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

