import React from 'react';
import { ComplaintStatus, UrgencyLevel } from '../../types';
import { useLanguage } from '../../context/LanguageContext';

interface StatusBadgeProps {
  status: ComplaintStatus | UrgencyLevel | string;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showDot = true,
}) => {
  const { t } = useLanguage();

  const getStyle = () => {
    switch (status) {
      case 'Submitted':
        return {
          bg: 'bg-maroon-800 text-white',
          dot: 'bg-cream-200',
          border: 'border-transparent',
          label: t('statusSubmitted'),
        };
      case 'Assigned':
        return {
          bg: 'bg-blue-600 text-white',
          dot: 'bg-blue-200',
          border: 'border-transparent',
          label: t('statusAssigned'),
        };
      case 'In Progress':
        return {
          bg: 'bg-amber-500 text-white',
          dot: 'bg-amber-100 animate-ping',
          border: 'border-transparent',
          label: t('statusInProgress'),
        };
      case 'Resolved':
        return {
          bg: 'bg-emerald-600 text-white',
          dot: 'bg-emerald-200',
          border: 'border-transparent',
          label: t('statusResolved'),
        };
      case 'Critical':
        return {
          bg: 'bg-red-600 text-white',
          dot: 'bg-red-200 animate-pulse',
          border: 'border-transparent',
          label: t('statusCritical'),
        };
      case 'High':
        return {
          bg: 'bg-orange-500 text-white',
          dot: 'bg-orange-200',
          border: 'border-transparent',
          label: 'High',
        };
      case 'Medium':
        return {
          bg: 'bg-amber-100 text-amber-900 border-amber-300',
          dot: 'bg-amber-500',
          border: 'border',
          label: 'Medium',
        };
      case 'Low':
        return {
          bg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
          dot: 'bg-emerald-500',
          border: 'border',
          label: 'Low',
        };
      default:
        return {
          bg: 'bg-gray-100 text-gray-800',
          dot: 'bg-gray-400',
          border: 'border-transparent',
          label: status,
        };
    }
  };

  const style = getStyle();

  const sizeClasses = {
    sm: 'text-xs px-2.5 py-0.5 font-medium gap-1.5',
    md: 'text-xs px-3 py-1 font-semibold gap-2',
    lg: 'text-sm px-4 py-1.5 font-semibold gap-2.5',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full shadow-sm transition-all duration-200 ${style.bg} ${style.border} ${sizeClasses}`}
    >
      {showDot && (
        <span className="relative flex h-2 w-2">
          {status === 'In Progress' && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${style.dot}`} />
        </span>
      )}
      <span>{style.label}</span>
    </span>
  );
};

