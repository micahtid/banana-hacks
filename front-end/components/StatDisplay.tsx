/**
 * StatDisplay Component
 * 
 * Reusable component for displaying a label-value statistic
 * Provides consistent formatting across the application
 */

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

export default function StatDisplay({
  label,
  value,
  className = "",
  valueClassName = "",
}: StatDisplayProps) {
  return (
    <div className={`stat-container ${className}`}>
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${valueClassName}`}>{value}</div>
    </div>
  );
}

