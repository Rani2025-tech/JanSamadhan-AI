import React, { useState } from 'react';
import { MessageSquare, Mic, X, Bot, Send, Sparkles } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useComplaints } from '../../context/ComplaintContext';
import { UrgencyLevel } from '../../types';

export const FloatingChatButton: React.FC = () => {
  const { t, currentLanguageOption } = useLanguage();
  const { createComplaint } = useComplaints();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Array<{ sender: 'ai' | 'user'; text: string; time: string; card?: any }>>([
    {
      sender: 'ai',
      text: t('chatGreeting'),
      time: 'Just now',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleOpen = () => {
    setIsOpen(prev => !prev);
  };

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userText = inputValue.trim();
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Append user message
    setMessages(prev => [...prev, { sender: 'user', text: userText, time: nowTime }]);
    setInputValue('');
    setIsSubmitting(true);

    // AI smart processing simulation
    setTimeout(() => {
      // Analyze text for category, department, location
      let category = 'Water Supply';
      let department = 'PHED';
      let urgency: UrgencyLevel = 'Medium';
      let district = 'Ganjam';
      let area = 'Ward 8, Berhampur';

      const lower = userText.toLowerCase();
      if (lower.includes('road') || lower.includes('pothole') || lower.includes('street') || lower.includes('rasta')) {
        category = 'Road Infrastructure';
        department = 'PWD';
        urgency = 'High';
        area = 'Main Road Junction';
      } else if (lower.includes('electric') || lower.includes('power') || lower.includes('light') || lower.includes('transformer')) {
        category = 'Electricity';
        department = 'DISCOM';
        urgency = 'High';
        area = 'Block C Residential';
      } else if (lower.includes('garbage') || lower.includes('clean') || lower.includes('drain') || lower.includes('waste')) {
        category = 'Sanitation';
        department = 'Municipal Corporation';
        urgency = 'Medium';
        area = 'Market Street';
      }

      // Auto-create complaint ticket
      const newTicket = createComplaint({
        title: userText.length > 50 ? userText.slice(0, 48) + '...' : userText,
        description: userText,
        category,
        department,
        urgency,
        language: currentLanguageOption.enName,
        district,
        area,
      });

      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          text: `Thank you! I have understood your grievance and drafted a formal redressal ticket. It has been registered under ${department} for prompt resolution.`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          card: newTicket,
        },
      ]);
      setIsSubmitting(false);
    }, 1200);
  };

  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser. Please type your message.');
      return;
    }

    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = currentLanguageOption.code === 'or' ? 'or-IN' : currentLanguageOption.code === 'hi' ? 'hi-IN' : 'en-IN';
      recognition.interimResults = false;

      setIsListening(true);
      recognition.start();

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };
    } catch (e) {
      setIsListening(false);
    }
  };

  return (
    <>
      {/* Floating Action Trigger Button */}
      <div className="fixed bottom-20 md:bottom-8 right-6 z-40 flex items-center gap-3">
        {/* Tooltip pill matching screenshot */}
        {!isOpen && (
          <div
            onClick={toggleOpen}
            className="hidden sm:flex items-center gap-2 bg-gray-900/90 text-white text-xs font-semibold px-3 py-1.5 rounded-xl shadow-lg cursor-pointer hover:bg-black transition-all duration-200 animate-in fade-in slide-in-from-right-2"
          >
            <span>{t('askAssistant')}</span>
            <span className="text-saffron-400">✨</span>
          </div>
        )}

        {/* The Button: Chat bubble with mic badge */}
        <button
          type="button"
          onClick={toggleOpen}
          aria-label={t('askAssistant')}
          className="relative w-14 h-14 rounded-full bg-maroon-800 hover:bg-maroon-700 text-white shadow-soft-lg flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 focus-ring"
        >
          {isOpen ? (
            <X className="w-6 h-6 text-white" />
          ) : (
            <>
              {/* Chat bubble icon */}
              <MessageSquare className="w-6 h-6 text-white fill-white" />
              {/* Small Mic badge */}
              <span className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-saffron-500 text-white flex items-center justify-center shadow-md border-2 border-white">
                <Mic className="w-3.5 h-3.5" />
              </span>
            </>
          )}
        </button>
      </div>

      {/* Interactive Chat Assistant Modal Drawer */}
      {isOpen && (
        <div className="fixed bottom-24 md:bottom-24 right-4 sm:right-8 z-50 w-[92vw] sm:w-[420px] max-h-[580px] h-[80vh] bg-white rounded-3xl shadow-2xl border border-maroon-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-maroon-900 via-maroon-800 to-maroon-900 text-white px-5 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Robot icon reused from File via Assistant */}
              <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center border border-white/20">
                <Bot className="w-6 h-6 text-saffron-300" />
              </div>
              <div>
                <div className="font-bold text-sm leading-tight flex items-center gap-1.5">
                  <span>JanSamadhan AI</span>
                  <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                </div>
                <div className="text-[11px] text-cream-200/80">
                  Multilingual Citizen Grievance Assistant ({currentLanguageOption.nativeName})
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-full hover:bg-white/10 text-cream-200 transition-colors focus-ring"
              aria-label="Close Assistant"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Chat Messages Body */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3.5 bg-cream-100/50">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'ai' && (
                  <div className="w-7 h-7 rounded-full bg-maroon-800 text-white flex-shrink-0 flex items-center justify-center text-xs">
                    <Bot className="w-4 h-4 text-saffron-300" />
                  </div>
                )}

                <div
                  className={`max-w-[82%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm shadow-sm leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-maroon-800 text-white rounded-br-none'
                      : 'bg-white text-gray-800 border border-maroon-100 rounded-bl-none'
                  }`}
                >
                  <p>{msg.text}</p>
                  
                  {/* Generated Ticket Card Preview if present */}
                  {msg.card && (
                    <div className="mt-2.5 pt-2 border-t border-maroon-100 bg-cream-200/70 p-2.5 rounded-xl text-xs space-y-1 text-gray-900">
                      <div className="font-bold text-maroon-900 flex items-center justify-between">
                        <span>{msg.card.id}</span>
                        <span className="text-[10px] bg-maroon-800 text-white px-2 py-0.5 rounded-full">
                          {msg.card.department}
                        </span>
                      </div>
                      <div className="text-gray-700 font-medium truncate">{msg.card.title}</div>
                      <div className="text-[11px] text-gray-600 flex justify-between pt-1">
                        <span>SLA: {msg.card.expectedDate}</span>
                        <span className="text-amber-700 font-bold">2 days left</span>
                      </div>
                    </div>
                  )}

                  <span
                    className={`block text-[10px] mt-1 text-right ${
                      msg.sender === 'user' ? 'text-cream-200/70' : 'text-gray-400'
                    }`}
                  >
                    {msg.time}
                  </span>
                </div>
              </div>
            ))}

            {isSubmitting && (
              <div className="flex items-center gap-2 text-xs text-maroon-800 italic bg-cream-200 px-3 py-1.5 rounded-full w-max">
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                <span>{t('analyzingGrievance')}</span>
              </div>
            )}
          </div>

          {/* Quick Grievance Templates Chips */}
          <div className="px-3 py-1.5 bg-cream-200/60 border-t border-maroon-100 flex items-center gap-2 overflow-x-auto text-[11px]">
            <span className="text-gray-500 font-medium flex-shrink-0">Quick:</span>
            <button
              onClick={() => setInputValue('Drinking water pipe leaking in my street')}
              className="px-2.5 py-1 bg-white hover:bg-maroon-50 border border-maroon-100 rounded-full text-maroon-900 whitespace-nowrap shadow-xs"
            >
              💧 Water leak
            </button>
            <button
              onClick={() => setInputValue('Street lights not working for past 5 days')}
              className="px-2.5 py-1 bg-white hover:bg-maroon-50 border border-maroon-100 rounded-full text-maroon-900 whitespace-nowrap shadow-xs"
            >
              💡 Streetlight issue
            </button>
            <button
              onClick={() => setInputValue('Pothole causing severe traffic problem')}
              className="px-2.5 py-1 bg-white hover:bg-maroon-50 border border-maroon-100 rounded-full text-maroon-900 whitespace-nowrap shadow-xs"
            >
              🚧 Road repair
            </button>
          </div>

          {/* Chat Input Bar */}
          <div className="p-3 bg-white border-t border-maroon-100">
            <form
              onSubmit={e => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <button
                type="button"
                onClick={handleVoiceInput}
                className={`p-2.5 rounded-full transition-colors focus-ring ${
                  isListening
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-cream-300 text-maroon-800 hover:bg-cream-400'
                }`}
                title={isListening ? 'Listening...' : 'Speak your complaint'}
                aria-label="Speak complaint"
              >
                <Mic className="w-4 h-4" />
              </button>

              <input
                type="text"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                placeholder={t('chatPlaceholder')}
                className="flex-1 bg-cream-100 border border-maroon-200 rounded-full px-4 py-2 text-xs sm:text-sm text-gray-800 placeholder-gray-400 focus-ring"
              />

              <button
                type="submit"
                disabled={!inputValue.trim()}
                className="p-2.5 rounded-full bg-maroon-800 hover:bg-maroon-700 disabled:opacity-40 text-white transition-colors focus-ring"
                aria-label="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

