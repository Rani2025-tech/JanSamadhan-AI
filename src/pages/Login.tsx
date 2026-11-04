import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  User,
  Shield,
  Phone,
  ChevronDown,
  Send,
  UserPlus,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  Check,
  ArrowRight,
  ShieldCheck,
  Mic,
} from 'lucide-react';
import { AccessibilityBar } from '../components/layout/AccessibilityBar';
import { useLanguage } from '../context/LanguageContext';
import { useAccessibility } from '../context/AccessibilityContext';
import { useAuth } from '../context/AuthContext';
import { SUPPORTED_LANGUAGES } from '../i18n/languages';
import loginBg from '../assets/images/logo-bg.png';

const ROW_1_LANG_CODES = ['hi', 'or', 'bn', 'mr'];
const ROW_2_LANG_CODES = ['ta', 'te', 'en'];

export const Login: React.FC = () => {
  const { currentLanguage, setLanguage, t } = useLanguage();
  const { highContrast } = useAccessibility();
  const { loginCitizen, loginAdmin, loginGuest } = useAuth();
  const navigate = useNavigate();

  // Tab: 'citizen' or 'admin'
  const [activeTab, setActiveTab] = useState<'citizen' | 'admin'>('citizen');

  // Citizen OTP Flow State
  const [mobileNumber, setMobileNumber] = useState('');
  const [mobileError, setMobileError] = useState('');
  const [mobileTouched, setMobileTouched] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpValues, setOtpValues] = useState<string[]>(['1', '2', '3', '4', '5', '6']);
  const [otpError, setOtpError] = useState('');
  const [resendTimer, setResendTimer] = useState(30);

  // Admin Login State
  const [adminId, setAdminId] = useState('OD-ADM-2024-88');
  const [adminPassword, setAdminPassword] = useState('Admin@2026');
  const [showPassword, setShowPassword] = useState(false);
  const [adminError, setAdminError] = useState('');

  // Loading state
  const [loading, setLoading] = useState(false);

  // OTP inputs refs
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Timer countdown for OTP resend
  useEffect(() => {
    let interval: any;
    if (otpSent && resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer(prev => prev - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [otpSent, resendTimer]);

  // Mobile number validation: 10 digits, starts with 6-9
  const validateMobile = (num: string) => {
    const clean = num.replace(/\D/g, '');
    if (clean.length === 0) {
      return 'Mobile number is required.';
    }
    if (!/^[6-9]/.test(clean)) {
      return 'Mobile number must start with 6, 7, 8, or 9.';
    }
    if (clean.length !== 10) {
      return 'Mobile number must be exactly 10 digits.';
    }
    return '';
  };

  const handleMobileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 10);
    setMobileNumber(val);
    if (mobileTouched) {
      setMobileError(validateMobile(val));
    }
  };

  const handleSendOtp = (e: React.FormEvent) => {
    e.preventDefault();
    setMobileTouched(true);
    const err = validateMobile(mobileNumber);
    if (err) {
      setMobileError(err);
      return;
    }
    setMobileError('');
    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      setOtpSent(true);
      setResendTimer(30);
      setOtpValues(['1', '2', '3', '4', '5', '6']);
    }, 450);
  };

  const handleOtpChange = (index: number, val: string) => {
    const digit = val.slice(-1);
    const newOtp = [...otpValues];
    newOtp[index] = digit;
    setOtpValues(newOtp);

    // Auto-focus next input
    if (digit && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpValues[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const enteredOtp = otpValues.join('');
    if (enteredOtp.length < 6) {
      setOtpError('Please enter all 6 digits of the OTP.');
      return;
    }

    setLoading(true);
    setOtpError('');
    const res = await loginCitizen(mobileNumber, enteredOtp);
    setLoading(false);

    if (res.success) {
      navigate('/dashboard');
    } else {
      setOtpError(res.error || t('otpError'));
    }
  };

  const handleAdminSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminId.trim() || !adminPassword.trim()) {
      setAdminError(t('adminError'));
      return;
    }

    setLoading(true);
    setAdminError('');
    const res = await loginAdmin(adminId, adminPassword);
    setLoading(false);

    if (res.success) {
      navigate('/admin');
    } else {
      setAdminError(res.error || t('adminError'));
    }
  };

  const [guestLoading, setGuestLoading] = useState(false);

  const handleGuestLogin = async () => {
    setGuestLoading(true);
    setMobileError('');
    try {
      await loginGuest();
      navigate('/dashboard');
    } catch (err: any) {
      setMobileError('Failed to initialize guest session. Please try again.');
    } finally {
      setGuestLoading(false);
    }
  };

  return (
    <div
      className={`relative w-full selection:bg-maroon-100 flex flex-col justify-between ${
        highContrast ? 'bg-black text-white' : 'bg-[#FFF6EE] text-gray-900'
      } lg:h-screen lg:overflow-hidden min-h-screen`}
    >
      {/* 1. Full-Page Background Illustration (fixed to min-h-screen, object-bottom) */}
      {!highContrast && (
        <img
          src={loginBg}
          alt=""
          className="absolute inset-0 w-full h-full object-cover object-bottom pointer-events-none z-0"
        />
      )}

      {/* 2. Top-Right Utility Accessibility Bar (fixed with 24px margin) */}
      <div className="fixed top-5 right-5 sm:top-6 sm:right-6 z-30">
        <AccessibilityBar className="bg-white/85 shadow-sm border border-maroon-100" />
      </div>

      {/* 3. Main Page Grid (desktop >= 1024px: ~58% left, ~36% right, 4% outer padding) */}
      <div className="relative z-10 w-full px-[4%] py-5 lg:py-0 flex-1 flex items-center">
        <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-6 items-center">
          
          {/* ================= LEFT COLUMN (~58%) ================= */}
          <div className="lg:col-span-7 flex flex-col justify-start space-y-5 lg:space-y-6 lg:pt-2">
            
            {/* a) ONE Brand Block Only */}
            <div className="flex items-center gap-4 sm:gap-5">
              {/* Logo icon ~110px */}
              <img
                src="/assets/logo.svg"
                alt="JanSamadhan Logo"
                className="w-20 h-20 sm:w-24 sm:h-24 xl:w-28 xl:h-28 object-contain flex-shrink-0"
              />

              {/* Vertical 2px maroon divider */}
              <div className="w-[2px] h-18 sm:h-22 xl:h-24 bg-maroon-800 flex-shrink-0" />

              {/* Wordmark and Tagline */}
              <div className="flex flex-col select-none">
                <span className="text-4xl sm:text-5xl xl:text-[66px] font-black text-maroon-800 tracking-tight leading-none">
                  JanSamadhan
                </span>
                <div className="relative pt-1 sm:pt-2">
                  <p className="text-base sm:text-xl xl:text-2xl font-bold text-[#2B2B2B] tracking-tight">
                    {t('brandTagline')}
                  </p>
                  {/* Maroon curved swoosh underline path */}
                  <svg
                    className="w-48 sm:w-60 xl:w-72 h-3 sm:h-3.5 text-maroon-800 mt-0.5"
                    viewBox="0 0 240 12"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M 2 8 C 60 1 150 1 238 10"
                      stroke="#7A0F2E"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* c) Voice Teaser Pill (soft pink #FBE4E1, rounded-full, inline-flex) */}
            <div>
              <div className="inline-flex items-center gap-2.5 bg-[#FBE4E1] border border-maroon-200/80 px-4 py-2 rounded-full shadow-xs">
                <div className="w-6 h-6 rounded-full bg-maroon-800 text-white flex items-center justify-center flex-shrink-0">
                  <Mic className="w-3.5 h-3.5 text-saffron-300" />
                </div>
                <span className="text-xs sm:text-sm font-semibold text-maroon-900">
                  {t('voiceTeaser')}
                </span>
              </div>
            </div>

            {/* d) Language Chips (Row 1: 4 chips, Row 2: 2 chips centered) */}
            <div className="space-y-3 max-w-[760px]">
              {/* Row 1 (Hindi, Odia, Bengali, Marathi) */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-3.5">
                {ROW_1_LANG_CODES.map(code => {
                  const lang = SUPPORTED_LANGUAGES.find(l => l.code === code)!;
                  const isSelected = currentLanguage === lang.code;
                  return (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => setLanguage(lang.code)}
                      className={`h-[64px] sm:h-[70px] rounded-2xl px-3 py-2 flex items-center justify-between border transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon-800 focus-visible:ring-offset-2 ${
                        isSelected
                          ? 'bg-maroon-800 text-white border-maroon-800 shadow-md font-bold'
                          : 'bg-white/80 hover:bg-white text-gray-900 border-maroon-100/90 shadow-xs backdrop-blur-xs'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`text-2xl sm:text-3xl font-extrabold flex items-center justify-center w-8 h-8 rounded-xl ${
                            isSelected ? 'text-white' : 'text-maroon-800'
                          }`}
                        >
                          {lang.nativeChar}
                        </span>
                        <div className="text-left leading-tight">
                          <div className={`text-xs sm:text-sm font-bold ${isSelected ? 'text-white' : 'text-gray-900'}`}>
                            {lang.nativeName}
                          </div>
                          <div className={`text-[11px] sm:text-xs ${isSelected ? 'text-cream-200' : 'text-gray-500 font-medium'}`}>
                            {lang.enName}
                          </div>
                        </div>
                      </div>

                      {isSelected && (
                        <span className="w-5 h-5 rounded-full bg-white text-maroon-800 flex items-center justify-center flex-shrink-0 shadow-xs ml-1">
                          <Check className="w-3.5 h-3.5 stroke-[3]" />
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Row 2 (Tamil, Telugu, English - Centered below Row 1) */}
              <div className="flex flex-wrap justify-center gap-3 sm:gap-3.5">
                {ROW_2_LANG_CODES.map(code => {
                  const lang = SUPPORTED_LANGUAGES.find(l => l.code === code)!;
                  const isSelected = currentLanguage === lang.code;
                  return (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => setLanguage(lang.code)}
                      className={`w-[136px] sm:w-[165px] xl:w-[175px] h-[64px] sm:h-[70px] rounded-2xl px-3 py-2 flex items-center justify-between border transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon-800 focus-visible:ring-offset-2 ${
                        isSelected
                          ? 'bg-maroon-800 text-white border-maroon-800 shadow-md font-bold'
                          : 'bg-white/80 hover:bg-white text-gray-900 border-maroon-100/90 shadow-xs backdrop-blur-xs'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`text-2xl sm:text-3xl font-extrabold flex items-center justify-center w-8 h-8 rounded-xl ${
                            isSelected ? 'text-white' : 'text-maroon-800'
                          }`}
                        >
                          {lang.nativeChar}
                        </span>
                        <div className="text-left leading-tight">
                          <div className={`text-xs sm:text-sm font-bold ${isSelected ? 'text-white' : 'text-gray-900'}`}>
                            {lang.nativeName}
                          </div>
                          <div className={`text-[11px] sm:text-xs ${isSelected ? 'text-cream-200' : 'text-gray-500 font-medium'}`}>
                            {lang.code === 'en' ? 'EN' : lang.enName}
                          </div>
                        </div>
                      </div>

                      {isSelected && (
                        <span className="w-5 h-5 rounded-full bg-white text-maroon-800 flex items-center justify-center flex-shrink-0 shadow-xs ml-1">
                          <Check className="w-3.5 h-3.5 stroke-[3]" />
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Reserved breathing space so building remains visible in the lower-left */}
            <div className="h-24 lg:h-36 xl:h-44 pointer-events-none" />
          </div>

          {/* ================= RIGHT COLUMN (~36% with ~2.5% right margin) ================= */}
          <div className="lg:col-span-5 flex justify-center lg:justify-end lg:pr-[2.5%]">
            <div className="w-full max-w-[420px] xl:max-w-[460px] bg-white rounded-3xl shadow-xl border border-maroon-100/70 p-6 sm:p-7 space-y-4 sm:space-y-5 transition-all">
              
              {/* Card Header: 3-people emblem -> Welcome to JanSamadhan -> Login to continue */}
              <div className="text-center space-y-1">
                <div className="flex justify-center mb-1">
                  {/* Clean 3-people emblem in maroon matching design-reference */}
                  <svg className="w-14 h-11 text-maroon-800" viewBox="0 0 100 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="50" cy="22" r="10" fill="#7A0F2E" />
                    <circle cx="28" cy="34" r="8" fill="#7A0F2E" />
                    <circle cx="72" cy="34" r="8" fill="#7A0F2E" />
                    <path d="M 16 64 C 24 52 34 44 50 44 C 66 44 76 52 84 64 C 70 58 58 56 50 56 C 42 56 30 58 16 64 Z" fill="#7A0F2E" />
                    <path d="M 18 68 C 36 61 54 63 82 72 C 64 68 46 68 28 75 C 22 76 18 72 18 68 Z" fill="#7A0F2E" />
                  </svg>
                </div>
                <h2 className="text-2xl sm:text-[27px] font-black text-maroon-800 tracking-tight">
                  {t('welcomeTitle')}
                </h2>
                <p className="text-xs sm:text-sm font-medium text-gray-600">
                  {t('loginSubtitle')}
                </p>
              </div>

              {/* Segmented Toggle: Citizen / Admin */}
              <div className="p-1 bg-[#FBE4E1] rounded-2xl flex items-center border border-maroon-200/50">
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('citizen');
                    setOtpSent(false);
                  }}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-xs sm:text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon-800 ${
                    activeTab === 'citizen'
                      ? 'bg-maroon-800 text-white font-bold shadow-sm'
                      : 'text-maroon-800 hover:text-maroon-900 font-semibold'
                  }`}
                >
                  <User className="w-4 h-4" />
                  <span>{t('tabCitizen')}</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('admin');
                    setOtpSent(false);
                  }}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-xs sm:text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon-800 ${
                    activeTab === 'admin'
                      ? 'bg-maroon-800 text-white font-bold shadow-sm'
                      : 'text-maroon-800 hover:text-maroon-900 font-semibold'
                  }`}
                >
                  <Shield className="w-4 h-4" />
                  <span>{t('tabAdmin')}</span>
                </button>
              </div>

              {/* TAB 1: CITIZEN FLOW */}
              {activeTab === 'citizen' && (
                <div className="space-y-4">
                  {!otpSent ? (
                    <form onSubmit={handleSendOtp} className="space-y-3.5">
                      {/* Segmented Phone Field as Flex Siblings */}
                      <div className="space-y-1">
                        <div
                          className={`flex items-center h-12 bg-white border rounded-xl px-3 transition-all focus-within:ring-2 focus-within:ring-maroon-800/30 ${
                            mobileError
                              ? 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/20'
                              : 'border-gray-300 focus-within:border-maroon-800'
                          }`}
                        >
                          {/* Left Segment: Phone icon + +91 + ChevronDown */}
                          <div className="flex items-center gap-1 text-gray-700 select-none pr-2.5 flex-shrink-0">
                            <Phone className="w-4 h-4 text-gray-700" />
                            <span className="text-sm font-bold text-gray-800">+91</span>
                            <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
                          </div>

                          {/* Vertical divider */}
                          <div className="w-[1px] h-6 bg-gray-300 flex-shrink-0 mr-3" />

                          {/* Right Segment: Number Input */}
                          <input
                            type="tel"
                            maxLength={10}
                            value={mobileNumber}
                            onChange={handleMobileChange}
                            placeholder="Enter Mobile Number"
                            className="w-full h-full bg-transparent border-0 outline-none p-0 text-sm sm:text-base font-semibold text-gray-900 placeholder:text-gray-400 focus:ring-0"
                          />
                        </div>

                        <div className="flex items-center justify-between text-xs pt-1 flex-wrap gap-1">
                          {mobileError ? (
                            <p className="text-red-600 font-semibold flex items-center gap-1">
                              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                              <span>{mobileError}</span>
                            </p>
                          ) : (
                            <p className="text-gray-700 font-medium">
                              {t('otpSendNote')}
                            </p>
                          )}
                          <button
                            type="button"
                            onClick={() => {
                              setMobileNumber('9876543210');
                              setMobileError('');
                            }}
                            className="text-maroon-800 font-bold hover:underline ml-auto"
                          >
                            Demo: Rani Nayak
                          </button>
                        </div>
                      </div>

                      {/* Send OTP: Full width, solid maroon, paper-plane Send icon, rounded-full, h-12 */}
                      <button
                        type="submit"
                        disabled={loading}
                        className="w-full h-12 rounded-full bg-maroon-800 hover:bg-maroon-900 active:scale-[0.99] text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon-800 focus-visible:ring-offset-2"
                      >
                        {loading ? (
                          <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <>
                            <Send className="w-4 h-4" />
                            <span>{t('sendOtp')}</span>
                          </>
                        )}
                      </button>

                      {/* Divider: Line - "OR" - Line */}
                      <div className="relative flex items-center justify-center my-2">
                        <div className="absolute inset-0 flex items-center">
                          <div className="w-full border-t border-gray-200" />
                        </div>
                        <div className="relative bg-white px-3 text-xs font-bold text-gray-400 uppercase tracking-wider">
                          OR
                        </div>
                      </div>

                      {/* Continue as Guest */}
                      <button
                        type="button"
                        onClick={handleGuestLogin}
                        disabled={loading || guestLoading}
                        className="w-full h-11 flex items-center justify-center gap-2 rounded-2xl border border-gray-200 hover:border-maroon-800 text-gray-700 hover:text-maroon-800 font-bold text-xs sm:text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon-800 disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        {guestLoading ? (
                          <span className="inline-block w-4 h-4 border-2 border-maroon-800 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <>
                            <UserPlus className="w-4 h-4 text-maroon-800" />
                            <span>{t('continueAsGuest')}</span>
                          </>
                        )}
                      </button>

                      {/* Info Note in Pale Pink Rounded Box with (i) Icon */}
                      <div className="bg-[#FBE4E1] border border-maroon-200/60 rounded-2xl p-2.5 text-xs text-maroon-900 flex items-center gap-2.5">
                        <span className="w-4 h-4 rounded-full bg-maroon-800 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                          i
                        </span>
                        <span className="font-medium leading-snug">
                          {t('guestNotice')}
                        </span>
                      </div>
                    </form>
                  ) : (
                    /* 6-box OTP Flow */
                    <form onSubmit={handleVerifyOtp} className="space-y-4">
                      <div className="text-center space-y-1">
                        <p className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                          {t('enterOtpFor')}
                        </p>
                        <div className="flex items-center justify-center gap-2">
                          <span className="font-extrabold text-sm text-gray-900">+91 {mobileNumber}</span>
                          <button
                            type="button"
                            onClick={() => {
                              setOtpSent(false);
                              setOtpError('');
                            }}
                            className="text-xs font-bold text-maroon-800 hover:underline"
                          >
                            {t('changeNumber')}
                          </button>
                        </div>
                      </div>

                      <div className="flex justify-center gap-2 sm:gap-2.5 py-1">
                        {otpValues.map((digit, idx) => (
                          <input
                            key={idx}
                            ref={el => (otpRefs.current[idx] = el)}
                            type="text"
                            inputMode="numeric"
                            maxLength={1}
                            value={digit}
                            onChange={e => handleOtpChange(idx, e.target.value)}
                            onKeyDown={e => handleOtpKeyDown(idx, e)}
                            className="w-10 sm:w-11 h-12 sm:h-13 text-center text-lg font-black text-gray-900 bg-white border border-gray-300 rounded-xl focus:border-maroon-800 focus:ring-2 focus:ring-maroon-800/30 transition-all"
                          />
                        ))}
                      </div>

                      {otpError && (
                        <p className="text-xs text-red-600 font-semibold text-center flex items-center justify-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                          <span>{otpError}</span>
                        </p>
                      )}

                      <button
                        type="submit"
                        disabled={loading}
                        className="w-full h-12 rounded-full bg-maroon-800 hover:bg-maroon-900 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon-800"
                      >
                        {loading ? (
                          <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <>
                            <span>{t('verifyOtp')}</span>
                            <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </button>

                      <div className="text-center">
                        {resendTimer > 0 ? (
                          <span className="text-xs font-medium text-gray-500">
                            {t('resendIn')} <strong className="text-maroon-800">{resendTimer}s</strong>
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => {
                              setResendTimer(30);
                              setOtpValues(['1', '2', '3', '4', '5', '6']);
                            }}
                            className="text-xs font-bold text-maroon-800 hover:underline"
                          >
                            {t('resendOtp')}
                          </button>
                        )}
                      </div>
                    </form>
                  )}
                </div>
              )}

              {/* TAB 2: ADMIN FLOW (Shown ONLY when Admin tab is active) */}
              {activeTab === 'admin' && (
                <form onSubmit={handleAdminSubmit} className="space-y-3.5">
                  <div className="space-y-1">
                    <div className="flex items-center h-12 bg-white border border-gray-300 rounded-xl px-3 transition-all focus-within:ring-2 focus-within:ring-maroon-800/30 focus-within:border-maroon-800">
                      <Lock className="w-4 h-4 text-gray-500 mr-2.5 flex-shrink-0" />
                      <input
                        type="text"
                        value={adminId}
                        onChange={e => setAdminId(e.target.value)}
                        placeholder={t('employeePlaceholder')}
                        className="w-full h-full bg-transparent border-0 outline-none p-0 text-sm font-semibold text-gray-900 placeholder:text-gray-400 focus:ring-0"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center h-12 bg-white border border-gray-300 rounded-xl px-3 transition-all focus-within:ring-2 focus-within:ring-maroon-800/30 focus-within:border-maroon-800">
                      <Lock className="w-4 h-4 text-gray-500 mr-2.5 flex-shrink-0" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={adminPassword}
                        onChange={e => setAdminPassword(e.target.value)}
                        placeholder={t('passwordPlaceholder')}
                        className="w-full h-full bg-transparent border-0 outline-none p-0 text-sm font-semibold text-gray-900 placeholder:text-gray-400 focus:ring-0"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        aria-label={showPassword ? "Hide password" : "Show password"}
                        className="text-gray-400 hover:text-gray-600 ml-2 focus-visible:outline-none"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {adminError && (
                    <p className="text-xs text-red-600 font-semibold flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                      <span>{adminError}</span>
                    </p>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full h-12 rounded-full bg-maroon-800 hover:bg-maroon-900 active:scale-[0.99] text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-maroon-800"
                  >
                    {loading ? (
                      <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>{t('loginBtn')}</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>

                  <div className="text-center pt-1">
                    <button
                      type="button"
                      onClick={() => alert('Password reset link sent to registered officer email.')}
                      className="text-xs font-semibold text-gray-700 hover:text-maroon-800 hover:underline"
                    >
                      {t('forgotPassword')}
                    </button>
                  </div>
                </form>
              )}

            </div>
          </div>

        </div>
      </div>

      {/* 4. Footer on the Maroon Wave (Bottom-left, white text, shield icon) */}
      <div className="relative z-20 pb-3 sm:pb-4 px-[4%] w-full flex items-center justify-start">
        <div className="flex items-center gap-2 text-white/95 text-xs font-medium drop-shadow-xs">
          <ShieldCheck className="w-4 h-4 text-white flex-shrink-0" />
          <span>
            {t('agreePrefix')}{' '}
            <Link to="/terms" className="underline hover:text-white font-semibold">
              {t('terms')}
            </Link>{' '}
            &{' '}
            <Link to="/privacy" className="underline hover:text-white font-semibold">
              {t('privacy')}
            </Link>.
          </span>
        </div>
      </div>
    </div>
  );
};
