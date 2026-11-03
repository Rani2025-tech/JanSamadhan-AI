import React from 'react';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  textColor?: string;
  subtitleColor?: string;
  dark?: boolean;
  saffronArc?: boolean;
}

export const Logo: React.FC<LogoProps> = ({
  className = '',
  size = 'md',
  showText = true,
  textColor,
  subtitleColor,
  dark = false,
  saffronArc = true,
}) => {
  const iconDimensions = {
    sm: { w: 42, h: 42 },
    md: { w: 52, h: 52 },
    lg: { w: 68, h: 68 },
    xl: { w: 108, h: 108 },
  }[size];

  const primaryColor = dark ? '#FFFFFF' : '#7A0F2E';
  const saffronColor = '#F28C28';
  const titleClass = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-3xl',
    xl: 'text-5xl font-black',
  }[size];

  return (
    <div className={`flex items-center gap-3.5 ${className}`}>
      {/* 3-people emblem with saffron arc */}
      <svg
        width={iconDimensions.w}
        height={iconDimensions.h}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0 transition-transform duration-300 hover:scale-102"
      >
        {/* Saffron Sweeping Arc */}
        {saffronArc && (
          <path
            d="M 14 62 A 40 40 0 0 1 84 26"
            stroke={saffronColor}
            strokeWidth="7"
            strokeLinecap="round"
          />
        )}
        {/* Center Leader Figure */}
        <circle cx="50" cy="35" r="9.5" fill={primaryColor} />
        {/* Left Citizen Figure */}
        <circle cx="31" cy="45" r="7.5" fill={primaryColor} />
        {/* Right Citizen Figure */}
        <circle cx="69" cy="45" r="7.5" fill={primaryColor} />
        
        {/* Unified Citizen Wave Torso */}
        <path
          d="M 18 74 C 24 62 34 54 50 54 C 66 54 76 62 82 74 C 70 67 58 65 50 65 C 42 65 30 67 18 74 Z"
          fill={primaryColor}
        />
        {/* Bottom Dynamic Swoosh Wave */}
        <path
          d="M 18 77 C 36 71 54 72 82 82 C 64 78 46 78 28 85 C 22 86 18 82 18 77 Z"
          fill={primaryColor}
        />
      </svg>

      {showText && (
        <div className="flex flex-col select-none">
          <div className="flex items-center gap-1.5">
            <span
              className={`tracking-tight ${titleClass} ${
                textColor ? textColor : dark ? 'text-white' : 'text-maroon-800'
              }`}
            >
              JanSamadhan
            </span>
          </div>
          <span
            className={`text-xs font-semibold tracking-wide ${
              subtitleColor
                ? subtitleColor
                : dark
                ? 'text-cream-300/80'
                : 'text-gray-700'
            }`}
          >
            Your Grievance. Our Commitment.
          </span>
        </div>
      )}
    </div>
  );
};
