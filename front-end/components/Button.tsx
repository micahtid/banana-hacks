/**
 * Button Component
 * 
 * Reusable button component with variant styling and size options
 * Supports all standard HTML button attributes
 */

import React from 'react';

/* ============================================
   TYPES
   ============================================ */

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

/* ============================================
   COMPONENT
   ============================================ */

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  className = '',
  disabled,
  ...props
}) => {
  // Base styles applied to all buttons
  const baseStyles = 'font-retro text-xl transition-all duration-200 border-2 disabled:opacity-50 disabled:cursor-not-allowed';

  // Variant-specific color schemes
  const variants = {
    primary: 'bg-[var(--primary)] hover:bg-[var(--primary-dark)] text-[var(--background)] border-[var(--primary-light)]',
    secondary: 'bg-[var(--card-bg)] hover:bg-[var(--border)] text-[var(--foreground)] border-[var(--border)]',
    danger: 'bg-[var(--danger)] hover:bg-red-600 text-white border-red-300',
    success: 'bg-[var(--success)] hover:bg-green-600 text-white border-green-300',
  };

  // Size-specific padding and text sizing
  const sizes = {
    sm: 'px-4 py-1 text-lg',
    md: 'px-6 py-2 text-xl',
    lg: 'px-8 py-3 text-2xl',
  };

  const widthClass = fullWidth ? 'w-full' : '';

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${widthClass} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
