import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  padding = 'md',
}) => {
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
      {title && (
        <h3 className="font-retro text-2xl text-[var(--primary-light)] mb-4 pb-2 border-b-2 border-[var(--border)]">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
};
