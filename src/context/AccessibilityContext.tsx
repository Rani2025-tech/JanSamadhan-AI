import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type FontSize = 'small' | 'normal' | 'large';

interface AccessibilityContextType {
  fontSize: FontSize;
  setFontSize: (size: FontSize) => void;
  highContrast: boolean;
  toggleHighContrast: () => void;
  helplinePhone: string;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

const FONT_SIZE_STORAGE = 'jansamadhan_font_size';
const HIGH_CONTRAST_STORAGE = 'jansamadhan_high_contrast';

export const AccessibilityProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [fontSize, setFontSizeState] = useState<FontSize>(() => {
    const saved = localStorage.getItem(FONT_SIZE_STORAGE) as FontSize | null;
    return saved === 'small' || saved === 'normal' || saved === 'large' ? saved : 'normal';
  });

  const [highContrast, setHighContrastState] = useState<boolean>(() => {
    return localStorage.getItem(HIGH_CONTRAST_STORAGE) === 'true';
  });

  const helplinePhone = '1800-123-4567';

  const setFontSize = (size: FontSize) => {
    setFontSizeState(size);
    localStorage.setItem(FONT_SIZE_STORAGE, size);
  };

  const toggleHighContrast = () => {
    setHighContrastState(prev => {
      const next = !prev;
      localStorage.setItem(HIGH_CONTRAST_STORAGE, String(next));
      return next;
    });
  };

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('font-size-small', 'font-size-normal', 'font-size-large');
    if (fontSize === 'small') {
      root.classList.add('font-size-small');
    } else if (fontSize === 'large') {
      root.classList.add('font-size-large');
    } else {
      root.classList.add('font-size-normal');
    }
  }, [fontSize]);

  useEffect(() => {
    const root = document.documentElement;
    if (highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }
  }, [highContrast]);

  return (
    <AccessibilityContext.Provider
      value={{
        fontSize,
        setFontSize,
        highContrast,
        toggleHighContrast,
        helplinePhone,
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = (): AccessibilityContextType => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

