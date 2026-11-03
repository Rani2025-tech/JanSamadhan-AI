import React from 'react';

interface BuildingProps {
  className?: string;
  variant?: 'full' | 'subtle' | 'silhouette';
}

export const BuildingIllustration: React.FC<BuildingProps> = ({
  className = '',
  variant = 'full',
}) => {
  const isSubtle = variant === 'subtle';
  const isSilhouette = variant === 'silhouette';

  const fillColor = isSilhouette
    ? 'currentColor'
    : isSubtle
    ? 'rgba(210, 160, 150, 0.45)'
    : '#C88373';

  const domeColor = isSilhouette ? 'currentColor' : '#B86F5F';
  const roofColor = isSilhouette ? 'currentColor' : '#A45848';
  const columnColor = isSilhouette ? 'currentColor' : '#DDB0A3';
  const treeColor = isSilhouette ? 'transparent' : '#5E744A';
  const treeDark = isSilhouette ? 'transparent' : '#455734';

  return (
    <svg
      viewBox="0 0 800 380"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      preserveAspectRatio="xMidYMax meet"
    >
      {!isSilhouette && (
        <g opacity={isSubtle ? 0.3 : 0.6}>
          {/* Subtle birds in flight */}
          <path d="M 320 70 Q 325 64 330 70 Q 335 64 340 70" stroke="#8D6257" strokeWidth="1.8" fill="none" strokeLinecap="round" />
          <path d="M 345 80 Q 349 75 353 80 Q 357 75 361 80" stroke="#8D6257" strokeWidth="1.6" fill="none" strokeLinecap="round" />
          <path d="M 360 65 Q 363 61 366 65 Q 369 61 372 65" stroke="#8D6257" strokeWidth="1.5" fill="none" strokeLinecap="round" />
        </g>
      )}

      {/* Main Ground Base Plinth */}
      <rect x="140" y="310" width="520" height="25" rx="3" fill={roofColor} opacity={isSilhouette ? 0.6 : 0.9} />
      <rect x="160" y="295" width="480" height="15" rx="2" fill={fillColor} />
      
      {/* Central Grand Portico */}
      <polygon points="320,175 480,175 400,125" fill={roofColor} />
      <rect x="330" y="175" width="140" height="120" fill={columnColor} opacity={isSilhouette ? 0.8 : 0.95} />

      {/* Central Columns */}
      <g fill={roofColor} opacity={isSilhouette ? 0.9 : 0.85}>
        <rect x="345" y="180" width="10" height="115" rx="2" />
        <rect x="370" y="180" width="10" height="115" rx="2" />
        <rect x="395" y="180" width="10" height="115" rx="2" />
        <rect x="420" y="180" width="10" height="115" rx="2" />
        <rect x="445" y="180" width="10" height="115" rx="2" />
      </g>

      {/* Central Grand Dome Drum */}
      <rect x="360" y="80" width="80" height="45" rx="2" fill={columnColor} />
      {/* Dome Drum Columns */}
      <g fill={roofColor} opacity="0.6">
        <rect x="368" y="85" width="4" height="40" />
        <rect x="382" y="85" width="4" height="40" />
        <rect x="398" y="85" width="4" height="40" />
        <rect x="414" y="85" width="4" height="40" />
        <rect x="428" y="85" width="4" height="40" />
      </g>
      {/* Central Grand Dome */}
      <path
        d="M 355 80 C 355 35 445 35 445 80 Z"
        fill={domeColor}
      />
      {/* Dome Spire / Kalash Finial */}
      <rect x="398" y="18" width="4" height="20" fill={roofColor} />
      <circle cx="400" cy="16" r="4.5" fill="#F28C28" />

      {/* Left Wing */}
      <rect x="180" y="210" width="150" height="85" fill={fillColor} />
      <rect x="175" y="200" width="160" height="10" fill={roofColor} />
      {/* Left wing windows */}
      <g fill={roofColor} opacity="0.7">
        <rect x="195" y="225" width="14" height="22" rx="2" />
        <rect x="225" y="225" width="14" height="22" rx="2" />
        <rect x="255" y="225" width="14" height="22" rx="2" />
        <rect x="285" y="225" width="14" height="22" rx="2" />
        <rect x="195" y="260" width="14" height="22" rx="2" />
        <rect x="225" y="260" width="14" height="22" rx="2" />
        <rect x="255" y="260" width="14" height="22" rx="2" />
        <rect x="285" y="260" width="14" height="22" rx="2" />
      </g>

      {/* Right Wing */}
      <rect x="470" y="210" width="150" height="85" fill={fillColor} />
      <rect x="465" y="200" width="160" height="10" fill={roofColor} />
      {/* Right wing windows */}
      <g fill={roofColor} opacity="0.7">
        <rect x="485" y="225" width="14" height="22" rx="2" />
        <rect x="515" y="225" width="14" height="22" rx="2" />
        <rect x="545" y="225" width="14" height="22" rx="2" />
        <rect x="575" y="225" width="14" height="22" rx="2" />
        <rect x="485" y="260" width="14" height="22" rx="2" />
        <rect x="515" y="260" width="14" height="22" rx="2" />
        <rect x="545" y="260" width="14" height="22" rx="2" />
        <rect x="575" y="260" width="14" height="22" rx="2" />
      </g>

      {/* Trees and Foliage */}
      {!isSilhouette && (
        <g opacity={isSubtle ? 0.4 : 0.85}>
          {/* Left Large Tree */}
          <ellipse cx="120" cy="270" rx="42" ry="50" fill={treeColor} />
          <ellipse cx="145" cy="255" rx="35" ry="42" fill={treeDark} />
          <rect x="116" y="295" width="10" height="40" rx="3" fill="#50352A" />

          {/* Right Tree */}
          <ellipse cx="670" cy="275" rx="40" ry="48" fill={treeDark} />
          <ellipse cx="695" cy="265" rx="35" ry="40" fill={treeColor} />
          <rect x="675" y="300" width="9" height="35" rx="3" fill="#50352A" />
        </g>
      )}
    </svg>
  );
};

