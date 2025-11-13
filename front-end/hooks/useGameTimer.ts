/**
 * useGameTimer Hook
 *
 * Calculates time remaining in a game based on start time and duration
 * Returns formatted time string and game end status
 */

import { useState, useEffect } from "react";

interface UseGameTimerReturn {
  timeRemaining: string;
  isGameEnded: boolean;
  secondsRemaining: number;
}

export function useGameTimer(
  startTime: Date | { seconds: number } | number | null | undefined,
  durationSeconds: number
): UseGameTimerReturn {
  const [timeRemaining, setTimeRemaining] = useState<string>("--:--");
  const [isGameEnded, setIsGameEnded] = useState<boolean>(false);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(0);

  useEffect(() => {
    if (!startTime) {
      setTimeRemaining("--:--");
      setIsGameEnded(false);
      setSecondsRemaining(0);
      return;
    }

    // Convert startTime to Date object
    let startDate: Date;
    if (startTime instanceof Date) {
      startDate = startTime;
    } else if (typeof startTime === "object" && "seconds" in startTime) {
      startDate = new Date(startTime.seconds * 1000);
    } else if (typeof startTime === "number") {
      startDate = new Date(startTime * 1000);
    } else {
      setTimeRemaining("--:--");
      setIsGameEnded(false);
      setSecondsRemaining(0);
      return;
    }

    const updateTimer = () => {
      const now = new Date();
      const elapsed = Math.floor((now.getTime() - startDate.getTime()) / 1000);
      const remaining = Math.max(0, durationSeconds - elapsed);

      setSecondsRemaining(remaining);

      if (remaining <= 0) {
        setTimeRemaining("00:00");
        setIsGameEnded(true);
        return;
      }

      const minutes = Math.floor(remaining / 60);
      const seconds = remaining % 60;
      setTimeRemaining(
        `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`
      );
      setIsGameEnded(false);
    };

    // Update immediately
    updateTimer();

    // Update every second
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [startTime, durationSeconds]);

  return { timeRemaining, isGameEnded, secondsRemaining };
}
