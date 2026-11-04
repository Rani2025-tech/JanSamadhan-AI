import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Bot,
  Mic,
  Send,
  Sparkles,
  FileCheck,
  RotateCcw,
  CheckCircle2,
  HelpCircle,
  MapPin,
  Briefcase,
  AlertTriangle,
  PhoneCall,
  Volume2,
  VolumeX,
  Pause,
  Play,
  Square,
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { useLanguage } from '../context/LanguageContext';
import { useComplaints } from '../context/ComplaintContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { UrgencyLevel } from '../types';

interface Message {
  sender: 'ai' | 'user';
  text: string;
  time: string;
  langCode?: string;
  faq?: { question: string; answer: string; source: string };
}

const TTS_STORAGE_KEY = 'jansamadhan_tts_auto';

const LANG_SPEECH_MAP: Record<string, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  or: 'or-IN',
  bn: 'bn-IN',
  mr: 'mr-IN',
  ta: 'ta-IN',
  te: 'te-IN',
};

export const AIAssistantPage: React.FC = () => {
  const { t, currentLanguageOption } = useLanguage();
  const { refreshComplaints } = useComplaints();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [sessionId, setSessionId] = useState<string>(() => `CHAT-${Date.now()}`);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'ai',
      text: t('chatGreeting'),
      time: 'Just now',
      langCode: currentLanguageOption.code,
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Extracted ticket preview / confirmation card state from backend slot filler
  const [ticketDraft, setTicketDraft] = useState<any | null>(null);
  const [detectedFaq, setDetectedFaq] = useState<any | null>(null);
  const [showHumanHelp, setShowHumanHelp] = useState(false);

  // Text-To-Speech (TTS) State
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [fallbackNoteIndex, setFallbackNoteIndex] = useState<number | null>(null);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [readAloudAuto, setReadAloudAuto] = useState<boolean>(() => {
    return localStorage.getItem(TTS_STORAGE_KEY) === 'true';
  });

  const isSpeechSynthesisSupported =
    typeof window !== 'undefined' &&
    'speechSynthesis' in window &&
    'SpeechSynthesisUtterance' in window;

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load available voices asynchronously
  useEffect(() => {
    if (!isSpeechSynthesisSupported) return;

    const loadVoices = () => {
      const available = window.speechSynthesis.getVoices();
      if (available && available.length > 0) {
        setVoices(available);
      }
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, [isSpeechSynthesisSupported]);

  // Stop speech on page navigation / unmount
  useEffect(() => {
    return () => {
      if (isSpeechSynthesisSupported) {
        window.speechSynthesis.cancel();
      }
    };
  }, [isSpeechSynthesisSupported]);

  // Reset conversation on user change so new user always starts with a clean slate
  useEffect(() => {
    if (isSpeechSynthesisSupported) {
      window.speechSynthesis.cancel();
    }
    setSpeakingIndex(null);
    setIsPaused(false);
    setSessionId(`CHAT-${Date.now()}`);
    setMessages([
      {
        sender: 'ai',
        text: t('chatGreeting'),
        time: 'Just now',
        langCode: currentLanguageOption.code,
      },
    ]);
    setTicketDraft(null);
    setDetectedFaq(null);
  }, [user?.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, ticketDraft]);

  // If navigated with ?voice=true, auto-trigger voice recognition
  useEffect(() => {
    if (searchParams.get('voice') === 'true') {
      handleVoiceInput();
    }
  }, [searchParams]);

  // Toggle Read Replies Aloud (persisted)
  const toggleReadAloud = () => {
    setReadAloudAuto(prev => {
      const next = !prev;
      localStorage.setItem(TTS_STORAGE_KEY, String(next));
      if (!next && isSpeechSynthesisSupported) {
        window.speechSynthesis.cancel();
        setSpeakingIndex(null);
        setIsPaused(false);
      }
      return next;
    });
  };

  // Find voice with fallback
  const getVoiceForLanguage = (langCode: string) => {
    const targetTag = LANG_SPEECH_MAP[langCode] || `${langCode}-IN`;
    const targetBase = langCode.toLowerCase();

    // 1. Exact match (e.g. "or-IN" or "hi-IN")
    let voice = voices.find(v => v.lang.toLowerCase().replace('_', '-') === targetTag.toLowerCase());

    // 2. Language base match (e.g. "hi" or "or")
    if (!voice) {
      voice = voices.find(v => v.lang.toLowerCase().startsWith(targetBase));
    }

    let isFallback = false;

    // 3. Fallback to Hindi if target language (e.g. Odia) has no native voice installed
    if (!voice && targetBase !== 'hi') {
      isFallback = true;
      voice = voices.find(v => v.lang.toLowerCase().replace('_', '-').startsWith('hi-in')) ||
              voices.find(v => v.lang.toLowerCase().startsWith('hi')) ||
              voices.find(v => v.lang.toLowerCase().replace('_', '-').startsWith('en-in')) ||
              voices[0];
    }

    return { voice, isFallback, targetTag };
  };

  // Speak bot message
  const speakMessage = (index: number, text: string, langCode: string = currentLanguageOption.code) => {
    if (!isSpeechSynthesisSupported) return;

    // If currently speaking this index and paused, resume
    if (speakingIndex === index && isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
      return;
    }

    // If currently speaking this index and playing, pause
    if (speakingIndex === index && !isPaused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Clean markdown and emojis for TTS clarity
    const cleanText = text
      .replace(/[*_~`#]/g, '')
      .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const { voice, isFallback, targetTag } = getVoiceForLanguage(langCode);

    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang;
    } else {
      utterance.lang = targetTag;
    }

    if (isFallback) {
      setFallbackNoteIndex(index);
    } else {
      setFallbackNoteIndex(null);
    }

    utterance.rate = 0.95; // slightly slower for high clarity in Indian languages
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      setSpeakingIndex(index);
      setIsPaused(false);
    };

    utterance.onend = () => {
      setSpeakingIndex(null);
      setIsPaused(false);
    };

    utterance.onerror = () => {
      setSpeakingIndex(null);
      setIsPaused(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (isSpeechSynthesisSupported) {
      window.speechSynthesis.cancel();
      setSpeakingIndex(null);
      setIsPaused(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputValue.trim();
    if (!text) return;

    // Stop ongoing speech on new user message
    stopSpeaking();

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { sender: 'user', text, time }]);
    setInputValue('');
    setIsProcessing(true);

    try {
      // Call backend conversational slot-filling endpoint
      const response = await api.sendChatMessage({
        session_id: sessionId,
        message: text,
        language: currentLanguageOption.code,
        user_id: user?.id,
      });

      setSessionId(response.session_id);

      // If confirmation card returned from slot filler, update draft preview
      if (response.confirmation_card) {
        setTicketDraft(response.confirmation_card);
      }

      if (response.detected_faq) {
        setDetectedFaq(response.detected_faq);
      }

      if ((response as any).suggest_human_agent || response.reply?.includes('1800-123-4567')) {
        setShowHumanHelp(true);
      }

      const botReplyMsg: Message = {
        sender: 'ai',
        text: response.reply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        faq: response.detected_faq,
        langCode: (response as any).language || currentLanguageOption.code,
      };

      setMessages(prev => {
        const nextMsgs = [...prev, botReplyMsg];
        const newBotIndex = nextMsgs.length - 1;

        // Auto-read aloud if toggle is enabled
        if (readAloudAuto && isSpeechSynthesisSupported) {
          setTimeout(() => {
            speakMessage(newBotIndex, botReplyMsg.text, botReplyMsg.langCode);
          }, 200);
        }

        return nextMsgs;
      });

      // If user confirmed and grievance was filed directly in DB
      if (response.ready_to_file && response.filed_complaint) {
        confetti({
          particleCount: 90,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#7A0F2E', '#F28C28', '#2563EB', '#16A34A'],
        });

        await refreshComplaints();

        setTimeout(() => {
          navigate(`/complaints/${response.filed_complaint!.id}`);
        }, 1500);
      }
    } catch (e: any) {
      const fallbackMsg: Message = {
        sender: 'ai',
        text: `I understood your input. Which district or city is this grievance located in?`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        langCode: currentLanguageOption.code,
      };

      setMessages(prev => {
        const nextMsgs = [...prev, fallbackMsg];
        if (readAloudAuto && isSpeechSynthesisSupported) {
          setTimeout(() => {
            speakMessage(nextMsgs.length - 1, fallbackMsg.text, fallbackMsg.langCode);
          }, 200);
        }
        return nextMsgs;
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Speech Recognition (Mic)
  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser. Please type your message.');
      return;
    }

    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      // Configure mic language code matching the selected language
      recognition.lang = LANG_SPEECH_MAP[currentLanguageOption.code] || 'en-IN';
      recognition.interimResults = false;

      setIsListening(true);
      recognition.start();

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsListening(false);
        handleSendMessage(transcript);
      };

      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
    } catch (e) {
      setIsListening(false);
    }
  };

  const handleConfirmAndFile = () => {
    handleSendMessage('Yes, confirm and file this grievance.');
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
            <span>{t('navAIAssistant')}</span>
            <span className="text-xs bg-saffron-100 text-saffron-800 font-bold px-3 py-1 rounded-full border border-saffron-300">
              Conversational Slot Filling ({currentLanguageOption.nativeName})
            </span>
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Speak or type naturally. The AI asks for missing location details, checks public FAQs, and generates a verified ticket.
          </p>
        </div>

        {/* Global Read Replies Aloud Toggle */}
        {isSpeechSynthesisSupported && (
          <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-full border border-maroon-100 shadow-xs">
            <button
              type="button"
              onClick={toggleReadAloud}
              className={`flex items-center gap-2 text-xs font-bold transition-colors ${
                readAloudAuto ? 'text-maroon-900' : 'text-gray-500'
              }`}
              title="Toggle automatic speech for AI replies" aria-label="Toggle read replies aloud"
            >
              <div
                className={`w-4 h-4 rounded-full flex items-center justify-center transition-colors ${
                  readAloudAuto ? 'bg-maroon-800 text-white' : 'bg-gray-200 text-gray-600'
                }`}
              >
                {readAloudAuto ? <Volume2 className="w-2.5 h-2.5" /> : <VolumeX className="w-2.5 h-2.5" />}
              </div>
              <span>Read replies aloud</span>
              <span
                className={`ml-1 text-[10px] px-2 py-0.5 rounded-full font-bold ${
                  readAloudAuto ? 'bg-saffron-100 text-saffron-900' : 'bg-gray-100 text-gray-600'
                }`}
              >
                {readAloudAuto ? 'ON' : 'OFF'}
              </span>
            </button>

            {speakingIndex !== null && (
              <div className="flex items-center gap-1 pl-2 border-l border-gray-200">
                <button
                  type="button"
                  onClick={() => {
                    if (isPaused) {
                      window.speechSynthesis.resume();
                      setIsPaused(false);
                    } else {
                      window.speechSynthesis.pause();
                      setIsPaused(true);
                    }
                  }}
                  className="p-1 hover:bg-cream-100 rounded text-maroon-800"
                  title={isPaused ? 'Resume speech' : 'Pause speech'} aria-label={isPaused ? 'Resume speech' : 'Pause speech'}
                >
                  {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                </button>
                <button
                  type="button"
                  onClick={stopSpeaking}
                  className="p-1 hover:bg-cream-100 rounded text-red-600"
                  title="Stop speech" aria-label="Stop speech"
                >
                  <Square className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Grid: Left Chat Stream + Right Draft Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: Chat Stream */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-maroon-100 shadow-soft flex flex-col h-[650px] overflow-hidden">
          {/* Chat Header */}
          <div className="bg-gradient-to-r from-maroon-900 to-maroon-800 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center border border-white/20">
                <Bot className="w-6 h-6 text-saffron-300" />
              </div>
              <div>
                <div className="font-bold text-sm">JanSamadhan AI Redressal Bot</div>
                <div className="text-xs text-cream-200/80">
                  Active Language: {currentLanguageOption.nativeName} ({currentLanguageOption.enName})
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  stopSpeaking();
                  setSessionId(`CHAT-${Date.now()}`);
                  setMessages([{ sender: 'ai', text: t('chatGreeting'), time: 'Just now', langCode: currentLanguageOption.code }]);
                  setTicketDraft(null);
                  setDetectedFaq(null);
                }}
                className="p-2 rounded-full hover:bg-white/10 text-cream-200 transition-colors"
                title="Reset Conversation"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages Body */}
          <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-cream-100/40">
            {messages.map((msg, idx) => {
              const isAi = msg.sender === 'ai';
              const isCurrentlySpeaking = speakingIndex === idx;

              return (
                <div
                  key={idx}
                  className={`flex gap-3 ${isAi ? 'justify-start' : 'justify-end'}`}
                >
                  {isAi && (
                    <div className="w-8 h-8 rounded-full bg-maroon-800 text-white flex-shrink-0 flex items-center justify-center text-xs shadow-xs">
                      <Bot className="w-4 h-4 text-saffron-300" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm leading-relaxed ${
                      isAi
                        ? 'bg-white text-gray-800 border border-maroon-100 rounded-bl-none'
                        : 'bg-maroon-800 text-white rounded-br-none'
                    }`}
                  >
                    <p className="whitespace-pre-line">{msg.text}</p>

                    {/* RAG FAQ Callout if detected */}
                    {msg.faq && (
                      <div className="mt-3 p-3 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-900 space-y-1">
                        <div className="font-bold flex items-center gap-1.5">
                          <HelpCircle className="w-3.5 h-3.5 text-blue-700" />
                          <span>Public Policy FAQ ({msg.faq.source.replace('.md', '')}):</span>
                        </div>
                        <p className="font-semibold text-gray-800">{msg.faq.question}</p>
                        <p className="text-gray-600 line-clamp-3">{msg.faq.answer}</p>
                      </div>
                    )}

                    {/* Footer: Time + TTS Speaker Controls */}
                    <div className="flex items-center justify-between gap-3 mt-2 pt-1 border-t border-gray-100/60">
                      {isAi && isSpeechSynthesisSupported ? (
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => speakMessage(idx, msg.text, msg.langCode || currentLanguageOption.code)}
                            className={`p-1 rounded-full transition-all flex items-center gap-1 text-[11px] font-bold ${
                              isCurrentlySpeaking
                                ? 'bg-saffron-100 text-saffron-900 ring-2 ring-saffron-400'
                                : 'text-gray-500 hover:text-maroon-900 hover:bg-cream-100'
                            }`}
                            title={isCurrentlySpeaking ? (isPaused ? 'Resume speaking' : 'Pause speaking') : 'Read reply aloud'} aria-label="Listen to message"
                          >
                            <Volume2 className={`w-3.5 h-3.5 ${isCurrentlySpeaking && !isPaused ? 'animate-pulse text-maroon-800' : ''}`} />
                            <span className="text-[10px]">
                              {isCurrentlySpeaking ? (isPaused ? 'Paused' : 'Playing') : 'Listen'}
                            </span>
                          </button>

                          {isCurrentlySpeaking && (
                            <button
                              type="button"
                              onClick={stopSpeaking}
                              className="p-1 rounded text-red-600 hover:bg-red-50 text-[10px] font-semibold flex items-center"
                              title="Stop speaking" aria-label="Stop speaking"
                            >
                              <Square className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      ) : (
                        <span />
                      )}

                      <span
                        className={`text-[10px] ${
                          isAi ? 'text-gray-400' : 'text-cream-200/70'
                        }`}
                      >
                        {msg.time}
                      </span>
                    </div>

                    {/* Fallback Note if Odia/native voice not installed on device */}
                    {isAi && fallbackNoteIndex === idx && (
                      <div className="mt-2 text-[11px] text-amber-800 bg-amber-50/80 px-2.5 py-1 rounded-lg border border-amber-200/70 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3 text-amber-600 flex-shrink-0" />
                        <span>Voice not available for this language on your device</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isProcessing && (
              <div className="flex items-center gap-2 text-xs text-maroon-800 bg-cream-200 px-4 py-2 rounded-full w-max animate-pulse">
                <Sparkles className="w-4 h-4 text-saffron-500 animate-spin" />
                <span>{t('analyzingGrievance')}</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Sample Prompts */}
          <div className="px-4 py-2 bg-cream-200/60 border-t border-maroon-100 flex items-center gap-2 overflow-x-auto text-xs">
            <span className="text-gray-500 font-bold flex-shrink-0">Quick actions:</span>
            <a
              href="tel:18001234567"
              className="px-3 py-1 bg-amber-100 hover:bg-amber-200 border border-amber-300 rounded-full text-amber-950 font-bold whitespace-nowrap shadow-xs flex items-center gap-1.5"
            >
              <PhoneCall className="w-3 h-3 text-maroon-800" />
              <span>Talk to a Human (1800-123-4567)</span>
            </a>
            <button
              onClick={() => handleSendMessage('Ward 7 Berhampur re pani pipe phatiki kadua pani asuchi 4 days hela')}
              className="px-3 py-1 bg-white hover:bg-cream-100 border border-maroon-100 rounded-full text-maroon-900 whitespace-nowrap shadow-xs"
            >
              💧 Odishlish: Water pipe leak
            </button>
            <button
              onClick={() => handleSendMessage('Station road par bohot bada pothole hai accident ho gaya')}
              className="px-3 py-1 bg-white hover:bg-cream-100 border border-maroon-100 rounded-full text-maroon-900 whitespace-nowrap shadow-xs"
            >
              🚧 Hinglish: Pothole on road
            </button>
            <button
              onClick={() => handleSendMessage('How to report contaminated drinking water?')}
              className="px-3 py-1 bg-white hover:bg-cream-100 border border-maroon-100 rounded-full text-maroon-900 whitespace-nowrap shadow-xs"
            >
              ❓ RAG FAQ: Water rules
            </button>
          </div>

          {/* Talk to Human Banner if confidence low or requested */}
          {showHumanHelp && (
            <div className="mx-4 mt-2 p-3 bg-amber-50 border border-amber-300 rounded-2xl flex items-center justify-between text-xs text-amber-950 shadow-sm animate-in fade-in slide-in-from-bottom-2">
              <div className="flex items-center gap-2">
                <PhoneCall className="w-4 h-4 text-amber-700 flex-shrink-0" />
                <div>
                  <span className="font-bold">Need Human Officer Review?</span>
                  <p className="text-[11px] text-amber-800">Our 24x7 toll-free helpline is available for immediate escalation.</p>
                </div>
              </div>
              <a
                href="tel:18001234567"
                className="px-3 py-1.5 rounded-full bg-maroon-800 text-white font-bold text-xs hover:bg-maroon-700 shadow-xs flex items-center gap-1.5 focus-ring flex-shrink-0"
              >
                <PhoneCall className="w-3.5 h-3.5 text-saffron-300" />
                <span>Call 1800-123-4567</span>
              </a>
            </div>
          )}

          {/* Input Bar */}
          <div className="p-4 bg-white border-t border-maroon-100">
            <form
              onSubmit={e => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-3"
            >
              <button
                type="button"
                onClick={handleVoiceInput}
                className={`p-3 rounded-full transition-all focus-ring ${
                  isListening
                    ? 'bg-red-500 text-white animate-bounce'
                    : 'bg-cream-300 text-maroon-800 hover:bg-cream-400'
                }`}
                title={isListening ? 'Listening...' : `Speak in ${currentLanguageOption.nativeName}`} aria-label={isListening ? "Stop voice dictation" : "Start voice dictation"}
              >
                <Mic className="w-5 h-5" />
              </button>

              <input
                type="text"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                placeholder={t('chatPlaceholder')}
                className="flex-1 bg-cream-100 border border-maroon-200 rounded-full px-5 py-3 text-sm text-gray-800 placeholder-gray-400 focus-ring"
              />

              <button
                type="submit"
                disabled={!inputValue.trim()}
                className="p-3 rounded-full bg-maroon-800 hover:bg-maroon-700 disabled:opacity-40 text-white transition-colors focus-ring"
                aria-label="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>

        {/* RIGHT COLUMN: Confirmation Card & Slot Filling State */}
        <div className="lg:col-span-5 bg-white rounded-3xl p-6 border border-maroon-100 shadow-soft space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-gray-100">
            <FileCheck className="w-5 h-5 text-maroon-800" />
            <h2 className="text-base font-bold text-gray-900">
              Live Conversational Slot Filling Card
            </h2>
          </div>

          {ticketDraft ? (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="bg-cream-100/80 p-5 rounded-2xl border border-maroon-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-maroon-900 uppercase tracking-wider">
                    {ticketDraft.department || 'PHED'}
                  </span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 font-bold">
                    {ticketDraft.urgency || 'Medium'} Urgency
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-gray-900">
                    {ticketDraft.title || ticketDraft.description}
                  </h3>
                  <p className="text-xs text-gray-600 mt-1">
                    {ticketDraft.description}
                  </p>
                </div>

                <div className="pt-2 border-t border-maroon-100 text-xs space-y-1.5 text-gray-700">
                  <div className="flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-maroon-800" />
                    <span>Category: <strong>{ticketDraft.category}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-maroon-800" />
                    <span>Location: <strong>{ticketDraft.area}, {ticketDraft.district}</strong></span>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-amber-50 rounded-2xl border border-amber-200 text-xs text-amber-900">
                ⚡ <strong>Confirmation Required:</strong> All slots are filled. Click the button below or reply "Yes" to register this official ticket.
              </div>

              <button
                type="button"
                onClick={handleConfirmAndFile}
                className="w-full py-4 px-6 rounded-2xl bg-maroon-800 hover:bg-maroon-700 text-white font-extrabold text-sm tracking-wide shadow-md transition-all flex items-center justify-center gap-2 focus-ring"
              >
                <CheckCircle2 className="w-5 h-5" />
                <span>Confirm & Register Grievance</span>
              </button>
            </div>
          ) : (
            <div className="bg-cream-100/50 rounded-2xl p-8 text-center border border-dashed border-maroon-200 space-y-3">
              <Bot className="w-10 h-10 text-maroon-800/40 mx-auto" />
              <p className="text-xs text-gray-500">
                Describe your issue in the assistant on the left. The slot filling system will ask for any missing details (such as district or landmark) and present the confirmation card here.
              </p>
            </div>
          )}

          {/* RAG Knowledge Base Panel */}
          {detectedFaq && (
            <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-200 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-blue-900">
                <HelpCircle className="w-4 h-4 text-blue-700" />
                <span>RAG Verified Public Service Guideline</span>
              </div>
              <p className="text-xs font-bold text-gray-900">{detectedFaq.question}</p>
              <p className="text-xs text-gray-700 leading-relaxed">{detectedFaq.answer}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
