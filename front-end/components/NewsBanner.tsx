/**
 * NewsBanner Component
 * 
 * Displays a scrolling news banner that shows market events
 * Used across multiple game views for consistent event notifications
 */

import { TbAlertTriangle } from "react-icons/tb";

/* ============================================
   TYPES
   ============================================ */

interface NewsBannerProps {
  newsText: string;
  isEventActive: boolean;
}

/* ============================================
   COMPONENT
   ============================================ */

export default function NewsBanner({ newsText, isEventActive }: NewsBannerProps) {
  return (
    <div className="news-banner">
      <div className="news-banner-content">
        <div
          className={`news-banner-text animate-scroll-fast ${
            isEventActive ? "active" : "inactive"
          }`}
        >
          {isEventActive && <TbAlertTriangle className="text-4xl" />}
          <span>
            {newsText} • {newsText} • {newsText} • {newsText} • {newsText} •
          </span>
        </div>
      </div>
    </div>
  );
}

