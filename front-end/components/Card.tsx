/**
 * Card Component
 * 
 * Reusable card container with optional title and configurable padding
 * Provides consistent styling for content sections
 */

import React from 'react';

/* ============================================
   TYPES
   ============================================ */

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

/* ============================================
   COMPONENT
   ============================================ */

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  padding = 'md',
}) => {
  // Padding size variants
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={`
        bg-[var(--card-bg)]
        border-2
        border-[var(--border)]
        ${paddingClasses[padding]}
        ${className}
      `}
    >
      {/* Optional title with bottom border */}
      {title && (
        <h3 className="font-retro text-2xl text-[var(--primary-light)] mb-4 pb-2 border-b-2 border-[var(--border)]">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
};
