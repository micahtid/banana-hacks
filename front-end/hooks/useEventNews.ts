/**
 * useEventNews Hook
 *
 * Manages event and generic news state with automatic rotation
 * Consolidates logic previously duplicated across MainDashboard, Shops, and Transactions
 */

import { useState, useEffect, useRef } from "react";
import type { Game } from "@/utils/database_functions";

interface UseEventNewsReturn {
  newsText: string;
  isEventActive: boolean;
}

export function useEventNews(game: Game): UseEventNewsReturn {
  const [newsText, setNewsText] = useState<string>("NO NEWS");
  const [isEventActive, setIsEventActive] = useState<boolean>(false);
  const [previousEventTriggered, setPreviousEventTriggered] = useState<boolean>(false);

  const eventTimerRef = useRef<NodeJS.Timeout | null>(null);
  const genericNewsTimerRef = useRef<NodeJS.Timeout | null>(null);
  const genericNewsIndexRef = useRef<number>(0);
  const allGenericNewsRef = useRef<string[]>([]);
  const isEventActiveRef = useRef<boolean>(false);
  const currentIntervalRef = useRef<number>(20000);

  // Effect: Handle event triggers (when backend sets eventTriggered = true)
  useEffect(() => {
    // If event just triggered (new event), start the timer
    if (game.eventTriggered && !previousEventTriggered) {
      // Clear any existing timers (both event timer and generic news rotation)
      if (eventTimerRef.current) {
        clearTimeout(eventTimerRef.current);
        eventTimerRef.current = null;
      }
      if (genericNewsTimerRef.current) {
        clearInterval(genericNewsTimerRef.current);
        genericNewsTimerRef.current = null;
      }

      // Event just triggered!
      setPreviousEventTriggered(true);
      const newText = game.eventTitle || "MARKET EVENT";
      setNewsText(newText);
      setIsEventActive(true);
      isEventActiveRef.current = true;

      // Set a fallback timer (10 seconds) in case backend doesn't reset in time
      eventTimerRef.current = setTimeout(() => {
        if (isEventActiveRef.current) {
          const allGenericNews = (game as any).allGenericNews;
          if (allGenericNews && Array.isArray(allGenericNews) && allGenericNews.length > 0) {
            genericNewsIndexRef.current = 0;
            setNewsText(allGenericNews[0]);
          } else {
            const genericNews = (game as any).genericNews || "NO NEWS";
            setNewsText(genericNews);
          }
          setIsEventActive(false);
          setPreviousEventTriggered(false);
          isEventActiveRef.current = false;
        }
      }, 10000);
    }

    // If backend cleared event_triggered, immediately reset to generic news
    if (!game.eventTriggered && previousEventTriggered) {
      if (eventTimerRef.current) {
        clearTimeout(eventTimerRef.current);
        eventTimerRef.current = null;
      }

      setPreviousEventTriggered(false);
      setIsEventActive(false);
      isEventActiveRef.current = false;

      const allGenericNews = (game as any).allGenericNews;
      if (allGenericNews && Array.isArray(allGenericNews) && allGenericNews.length > 0) {
        genericNewsIndexRef.current = 0;
        setNewsText(allGenericNews[0]);
      } else {
        const genericNews = (game as any).genericNews || "NO NEWS";
        setNewsText(genericNews);
      }
    }

    return () => {
      if (eventTimerRef.current) {
        clearTimeout(eventTimerRef.current);
        eventTimerRef.current = null;
      }
    };
  }, [game.eventTriggered, previousEventTriggered, game.eventTitle, (game as any).genericNews]);

  // Effect: Set generic news when available and rotate every 20s (or 3s during events)
  useEffect(() => {
    const allGenericNews = (game as any).allGenericNews;

    const newHeadlinesStr = allGenericNews && Array.isArray(allGenericNews)
      ? JSON.stringify(allGenericNews)
      : '';
    const oldHeadlinesStr = JSON.stringify(allGenericNewsRef.current);
    const headlinesChanged = newHeadlinesStr !== oldHeadlinesStr;

    if (!game.eventTriggered && !isEventActive) {
      if (allGenericNews && Array.isArray(allGenericNews) && allGenericNews.length > 0) {
        allGenericNewsRef.current = allGenericNews;

        if (headlinesChanged || !genericNewsTimerRef.current) {
          if (genericNewsTimerRef.current) {
            clearInterval(genericNewsTimerRef.current);
            genericNewsTimerRef.current = null;
          }

          if (headlinesChanged) {
            genericNewsIndexRef.current = 0;
            setNewsText(allGenericNews[0]);
          } else {
            const currentIndex = genericNewsIndexRef.current;
            if (currentIndex >= allGenericNews.length || currentIndex < 0) {
              genericNewsIndexRef.current = 0;
              setNewsText(allGenericNews[0]);
            } else if (!newsText || newsText === "NO NEWS" || !allGenericNews.includes(newsText)) {
              genericNewsIndexRef.current = 0;
              setNewsText(allGenericNews[0]);
            }
          }

          const getRotationInterval = () => {
            return isEventActiveRef.current ? 3000 : 20000;
          };

          const rotateNews = () => {
            if (allGenericNewsRef.current.length > 0) {
              if (genericNewsIndexRef.current >= allGenericNewsRef.current.length) {
                genericNewsIndexRef.current = 0;
              }
              genericNewsIndexRef.current = (genericNewsIndexRef.current + 1) % allGenericNewsRef.current.length;
              setNewsText(allGenericNewsRef.current[genericNewsIndexRef.current]);

              const newInterval = getRotationInterval();
              if (newInterval !== currentIntervalRef.current) {
                if (genericNewsTimerRef.current) {
                  clearInterval(genericNewsTimerRef.current);
                }
                currentIntervalRef.current = newInterval;
                genericNewsTimerRef.current = setInterval(rotateNews, currentIntervalRef.current);
              }
            }
          };

          currentIntervalRef.current = getRotationInterval();
          genericNewsTimerRef.current = setInterval(rotateNews, currentIntervalRef.current);
        }
      } else {
        if (genericNewsTimerRef.current) {
          clearInterval(genericNewsTimerRef.current);
          genericNewsTimerRef.current = null;
        }
        const genericNews = (game as any).genericNews;
        if (genericNews && genericNews.trim() !== '') {
          setNewsText(genericNews);
        }
      }
    }

    return () => {
      // Cleanup handled in component unmount
    };
  }, [(game as any).allGenericNews, (game as any).genericNews, game.eventTriggered, isEventActive]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventTimerRef.current) {
        clearTimeout(eventTimerRef.current);
      }
      if (genericNewsTimerRef.current) {
        clearInterval(genericNewsTimerRef.current);
      }
    };
  }, []);

  return { newsText, isEventActive };
}
