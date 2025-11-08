import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  fullWidth = false,
  className = '',
  ...props
}) => {
  const widthClass = fullWidth ? 'w-full' : '';

  return (
    <div className={`flex flex-col gap-2 ${widthClass}`}>
      {label && (
        <label className="font-retro text-lg text-[var(--primary-light)]">
          {label}
        </label>
      )}
      <input
        className={`
          bg-[var(--card-bg)]
          text-[var(--foreground)]
          border-2
          border-[var(--border)]
          px-4
          py-3
          font-retro
          text-lg
          focus:outline-none
          focus:border-[var(--primary)]
          transition-colors
          ${error ? 'border-[var(--danger)]' : ''}
          ${widthClass}
          ${className}
        `}
        {...props}
      />
      {error && (
        <span className="font-sans text-sm text-[var(--danger)]">
          {error}
        </span>
      )}
    </div>
  );
};
