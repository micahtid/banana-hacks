/**
 * StatDisplay Component
 *
 * Reusable component for displaying a label-value statistic
 * Provides consistent formatting across the application
 */

import React from "react";

/* ============================================
   TYPES
   ============================================ */

interface StatDisplayProps {
  label: string;
  value: string | number;
  className?: string;
  valueClassName?: string;
}

/* ============================================
   COMPONENT
   ============================================ */

export const StatDisplay: React.FC<StatDisplayProps> = ({
  label,
  value,
  className = "",
  valueClassName = "",
}) => {
  return (
    <div className={`stat-container ${className}`}>
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${valueClassName}`}>{value}</div>
    </div>
  );
};

