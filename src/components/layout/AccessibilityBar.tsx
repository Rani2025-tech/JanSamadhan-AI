import React from 'react';
import { Sun, Phone } from 'lucide-react';
import { useAccessibility } from '../../context/AccessibilityContext';

interface AccessibilityBarProps {
  className?: string;
}

export const AccessibilityBar: React.FC<AccessibilityBarProps> = ({ className = '' }) => {
  const { fontSize, setFontSize, highContrast, toggleHighContrast, helplinePhone } = useAccessibility();

  return (
    <div
      className={`inline-flex items-center gap-3 bg-white/70 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-maroon-100 shadow-sm text-sm text-gray-800 ${className}`}
      role="toolbar"
      aria-label="Accessibility tools"
    >
      {/* Font Size controls */}
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => setFontSize('large')}
          title="Increase font size (A+)"
          aria-label="Increase font size (A+)"
          className={`px-1.5 py-0.5 rounded text-xs font-bold transition-colors focus-ring ${
            fontSize === 'large'
              ? 'bg-maroon-800 text-white'
              : 'hover:bg-cream-200 text-gray-700'
          }`}
        >
          A+
        </button>
        <button
          type="button"
          onClick={() => setFontSize('normal')}
          title="Normal font size (A)"
          aria-label="Normal font size (A)"
          className={`px-1.5 py-0.5 rounded text-xs font-semibold transition-colors focus-ring ${
            fontSize === 'normal'
              ? 'bg-maroon-800 text-white'
              : 'hover:bg-cream-200 text-gray-700'
          }`}
        >
          A
        </button>
        <button
          type="button"
          onClick={() => setFontSize('small')}
          title="Decrease font size (A-)"
          aria-label="Decrease font size (A-)"
          className={`px-1.5 py-0.5 rounded text-xs font-medium transition-colors focus-ring ${
            fontSize === 'small'
              ? 'bg-maroon-800 text-white'
              : 'hover:bg-cream-200 text-gray-700'
          }`}
        >
          A-
        </button>
      </div>

      <div className="h-4 w-[1px] bg-maroon-200" aria-hidden="true" />

      {/* High Contrast Toggle */}
      <button
        type="button"
        onClick={toggleHighContrast}
        title={highContrast ? "Normal contrast" : "Toggle high contrast"}
        aria-label="Toggle high contrast"
        className={`p-1 rounded-full transition-colors focus-ring ${
          highContrast ? 'bg-amber-400 text-black' : 'text-gray-700 hover:text-maroon-800 hover:bg-cream-200'
        }`}
      >
        <Sun className="w-4 h-4" />
      </button>

      <div className="h-4 w-[1px] bg-maroon-200" aria-hidden="true" />

      {/* Helpline Tel Link */}
      <a
        href={`tel:${helplinePhone.replace(/-/g, '')}`}
        className="flex items-center gap-1.5 font-semibold text-maroon-800 hover:text-maroon-900 transition-colors focus-ring rounded-full px-1"
        title="Toll Free Citizen Helpline"
        aria-label={`Call Citizen Helpline ${helplinePhone}`}
      >
        <Phone className="w-3.5 h-3.5 text-maroon-800 fill-maroon-800" />
        <span className="text-xs sm:text-sm font-bold tracking-tight">{helplinePhone}</span>
      </a>
    </div>
  );
};

