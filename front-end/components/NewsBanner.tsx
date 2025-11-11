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

export const NewsBanner: React.FC<NewsBannerProps> = ({ newsText, isEventActive }) => {
  // Create a repeated text segment for seamless scrolling
  // Duplicate content 3 times to ensure seamless loop (animation moves by 50% = 1 of 2 copies)
  const textSegment = `${newsText} • `;
  const repeatedText = textSegment.repeat(6); // Enough repetitions for smooth scrolling

  return (
    <div className="news-banner">
      <div className="news-banner-content">
        <div
          className={`news-banner-text animate-scroll-fast ${
            isEventActive ? "active" : "inactive"
          }`}
        >
          {/* Duplicate content for seamless infinite scroll */}
          <span className="inline-block">
            {isEventActive && <TbAlertTriangle className="text-4xl inline-block mr-2" />}
            {repeatedText}
          </span>
          <span className="inline-block">
            {isEventActive && <TbAlertTriangle className="text-4xl inline-block mr-2" />}
            {repeatedText}
          </span>
        </div>
      </div>
    </div>
  );
};

