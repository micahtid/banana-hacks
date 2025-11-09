"use client";

import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import {
  type Game,
  type User,
  type LeaderboardEntry,
  buyCoins,
  sellCoins,
  toggleMinion,
  getLeaderboard,
} from "@/utils/database_functions";
import { useState, useEffect, useMemo, useRef } from "react";
import { useUser } from "@/providers/UserProvider";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { FaTrophy, FaMedal, FaAward } from "react-icons/fa";
import { TbAlertTriangle } from "react-icons/tb";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface MainDashboardProps {
  game: Game;
  currentUser: User;
}

// Helper function to get display name for a minion
// Handles both new minions (with proper display names) and old minions (with backend types)
function getMinionDisplayName(botName: string): string {
  // If it's already a display name (has spaces or starts with capital), return as-is
  if (botName.includes(' ') || /^[A-Z]/.test(botName)) {
    return botName;
  }
  
  // For old minions with backend types, convert to user-friendly format
  // e.g., "mean_reversion" → "Mean Reversion Bot"
  return botName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ') + ' Bot';
}

export default function MainDashboard({ game, currentUser }: MainDashboardProps) {
  const { user } = useUser();
  const [amount, setAmount] = useState<string>("");
  const [actionLoading, setActionLoading] = useState<"buy" | "sell" | null>(null);
  const [actionError, setActionError] = useState<string>("");
  const [timeRemaining, setTimeRemaining] = useState<string>("--:--");
  const [togglingMinion, setTogglingMinion] = useState<string | null>(null);
  const [showLeaderboard, setShowLeaderboard] = useState<boolean>(false);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [rotMultiplier, setRotMultiplier] = useState<number>(1.0);
  const [rotLevel, setRotLevel] = useState<number>(0);
  const [newsText, setNewsText] = useState<string>("NO NEWS");
  const [isEventActive, setIsEventActive] = useState<boolean>(false);
  const [previousEventTriggered, setPreviousEventTriggered] = useState<boolean>(false);
  const eventTimerRef = useRef<NodeJS.Timeout | null>(null);
  const genericNewsTimerRef = useRef<NodeJS.Timeout | null>(null);
  const genericNewsIndexRef = useRef<number>(0);
  const allGenericNewsRef = useRef<string[]>([]);
  const isEventActiveRef = useRef<boolean>(false);
  const currentIntervalRef = useRef<number>(20000); // Track current interval

  // Safe defaults for optional arrays or values
  const coinsArr = Array.isArray(game.coin) ? game.coin : [];
  const interactionsArr = Array.isArray(game.interactions)
    ? game.interactions
    : [];

  // --- Event News Banner Logic ---
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
      // But we'll also check backend state on each poll
      eventTimerRef.current = setTimeout(() => {
        // Only use timeout if backend still shows event as active
        // Otherwise, backend already cleared it and we should respect that
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
          setPreviousEventTriggered(false); // Reset for next event
          isEventActiveRef.current = false;
        }
      }, 10000);
    }

    // CRITICAL: If backend cleared event_triggered, immediately reset to generic news
    // This is the primary mechanism - backend controls the timeout
    if (!game.eventTriggered && previousEventTriggered) {
      // Clear the frontend timeout since backend already cleared the event
      if (eventTimerRef.current) {
        clearTimeout(eventTimerRef.current);
        eventTimerRef.current = null;
      }
      
      // Reset to generic news immediately
      setPreviousEventTriggered(false);
      setIsEventActive(false);
      isEventActiveRef.current = false;
      
      // Set initial generic news - rotation will be handled by the generic news effect
      const allGenericNews = (game as any).allGenericNews;
      if (allGenericNews && Array.isArray(allGenericNews) && allGenericNews.length > 0) {
        genericNewsIndexRef.current = 0;
        setNewsText(allGenericNews[0]);
      } else {
        const genericNews = (game as any).genericNews || "NO NEWS";
        setNewsText(genericNews);
      }
    }

    // Note: Generic news handling is now in a separate useEffect below
    // This keeps the event logic separate from generic news logic

    // Cleanup on unmount
    return () => {
      if (eventTimerRef.current) {
        clearTimeout(eventTimerRef.current);
        eventTimerRef.current = null;
      }
    };
  }, [game.eventTriggered, previousEventTriggered, game.eventTitle, (game as any).genericNews]);

  // Effect: Set generic news when it becomes available and rotate every 10 seconds
  // This should work BEFORE events (when no event has triggered) and AFTER events (when event clears)
  useEffect(() => {
    const allGenericNews = (game as any).allGenericNews;
    
    // Check if headlines have actually changed by comparing stringified arrays
    const newHeadlinesStr = allGenericNews && Array.isArray(allGenericNews) 
      ? JSON.stringify(allGenericNews) 
      : '';
    const oldHeadlinesStr = JSON.stringify(allGenericNewsRef.current);
    const headlinesChanged = newHeadlinesStr !== oldHeadlinesStr;
    
    // Set up generic news rotation when:
    // 1. No event is currently triggered (from backend)
    // 2. No event is active locally (not showing event news)
    // This allows rotation both before events and after events clear
    if (!game.eventTriggered && !isEventActive) {
      if (allGenericNews && Array.isArray(allGenericNews) && allGenericNews.length > 0) {
        // Update ref with new headlines
        allGenericNewsRef.current = allGenericNews;
        
        // Only clear and recreate interval if:
        // 1. Headlines actually changed (content changed)
        // 2. No interval exists yet (first time setup)
        // 3. Event state changed (event just cleared)
        if (headlinesChanged || !genericNewsTimerRef.current) {
          // Clear existing timer if it exists
          if (genericNewsTimerRef.current) {
            clearInterval(genericNewsTimerRef.current);
            genericNewsTimerRef.current = null;
          }
          
          // If headlines changed, reset index and update display
          if (headlinesChanged) {
            genericNewsIndexRef.current = 0;
            setNewsText(allGenericNews[0]);
          } else {
            // Validate current index and newsText
            const currentIndex = genericNewsIndexRef.current;
            if (currentIndex >= allGenericNews.length || currentIndex < 0) {
              genericNewsIndexRef.current = 0;
              setNewsText(allGenericNews[0]);
            } else if (!newsText || newsText === "NO NEWS" || !allGenericNews.includes(newsText)) {
              // If current text is invalid or not in the list, reset to first headline
              genericNewsIndexRef.current = 0;
              setNewsText(allGenericNews[0]);
            }
          }
          
          // Rotate through headlines - slower normally (20s), faster during events (3s)
          // Use refs to check current state in interval callback (avoids stale closures)
          const getRotationInterval = () => {
            // Speed up during events, slow down normally
            return isEventActiveRef.current ? 3000 : 20000; // 3s during events, 20s normally
          };
          
          // Set up rotation with dynamic interval
          const rotateNews = () => {
            if (allGenericNewsRef.current.length > 0) {
              // Ensure index is valid
              if (genericNewsIndexRef.current >= allGenericNewsRef.current.length) {
                genericNewsIndexRef.current = 0;
              }
              genericNewsIndexRef.current = (genericNewsIndexRef.current + 1) % allGenericNewsRef.current.length;
              setNewsText(allGenericNewsRef.current[genericNewsIndexRef.current]);
              
              // Check if interval needs to change based on event state
              const newInterval = getRotationInterval();
              if (newInterval !== currentIntervalRef.current) {
                // Clear and recreate with new interval
                if (genericNewsTimerRef.current) {
                  clearInterval(genericNewsTimerRef.current);
                }
                currentIntervalRef.current = newInterval;
                genericNewsTimerRef.current = setInterval(rotateNews, currentIntervalRef.current);
              }
            }
          };
          
          // Start with initial interval
          currentIntervalRef.current = getRotationInterval();
          genericNewsTimerRef.current = setInterval(rotateNews, currentIntervalRef.current);
        }
      } else {
        // Fallback to single generic news if array not available
        // Clear rotation timer since we don't have headlines to rotate
        if (genericNewsTimerRef.current) {
          clearInterval(genericNewsTimerRef.current);
          genericNewsTimerRef.current = null;
        }
        const genericNews = (game as any).genericNews;
        if (genericNews && genericNews.trim() !== '') {
          setNewsText(genericNews);
        }
      }
    } else if (game.eventTriggered || isEventActive) {
      // When event is active, continue rotation but at faster speed
      // The rotation interval will automatically adjust via the dynamic interval check
      // Don't stop rotation - let it speed up during events
    }
    
    // Cleanup on unmount
    return () => {
      // Only cleanup on unmount or when event state changes
      // Don't cleanup on every render to avoid interrupting rotation
    };
  }, [(game as any).allGenericNews, (game as any).genericNews, game.eventTriggered, isEventActive]);

  // Calculate current user's total trades (their own + their bots' trades)
  const currentUserName = currentUser.userName || currentUser.playerName;
  const currentUserBotNames = (currentUser.bots || []).map((bot: any) => bot.botName).filter(Boolean);

  const currentUserTotalTrades = interactionsArr.filter((interaction: any) => {
    if (!interaction.name) return false;
    const name = interaction.name;

    // Check if it's the user's own trade
    if (name === currentUserName) return true;

    // Check if it's one of the user's bots
    return currentUserBotNames.some((botName: string) =>
      name.includes(botName) || name.toLowerCase().includes(botName.toLowerCase())
    );
  }).length;

  const currentPrice = coinsArr.length > 0 ? Number(coinsArr.at(-1)) : 1.0;
  const previousPrice =
    coinsArr.length > 1 ? Number(coinsArr.at(-2)) : currentPrice;
  const priceChange = currentPrice - previousPrice;
  const priceChangePercent =
    previousPrice !== 0 ? (priceChange / previousPrice) * 100 : 0;

  // --- Timer Logic ---
  useEffect(() => {
    if (!game.startTime || !game.isStarted) {
      setTimeRemaining("--:--");
      return;
    }

    const updateTimer = () => {
      const now = new Date();
      let startTime: Date;

      if (!game.startTime) return setTimeRemaining("--:--");

      if (
        typeof game.startTime === "object" &&
        game.startTime !== null &&
        "seconds" in game.startTime &&
        typeof (game.startTime as any).seconds === "number"
      ) {
        startTime = new Date((game.startTime as { seconds: number }).seconds * 1000);
      } else if (game.startTime instanceof Date) {
        startTime = game.startTime;
      } else {
        startTime = new Date(game.startTime as any);
      }

      const durationMinutes = typeof game.gameDuration === "number" ? game.gameDuration : 0;
      const endTime = new Date(startTime.getTime() + durationMinutes * 60000);
      const diff = endTime.getTime() - now.getTime();

      if (diff <= 0) return setTimeRemaining("00:00");

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeRemaining(
        `${minutes.toString().padStart(2, "0")}:${seconds
          .toString()
          .padStart(2, "0")}`
      );
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [game.startTime, game.gameDuration, game.isStarted]);

  // --- Leaderboard Real-time Updates ---
  useEffect(() => {
    if (!showLeaderboard || !game.gameId) return;

    const fetchLeaderboard = async () => {
      try {
        const data = await getLeaderboard(game.gameId ?? "");
        setLeaderboard(data);
      } catch (error) {
        console.error("Failed to fetch leaderboard:", error);
      }
    };

    // Initial fetch
    fetchLeaderboard();

    // Poll every 1 second for real-time updates
    const interval = setInterval(fetchLeaderboard, 1000);
    return () => clearInterval(interval);
  }, [showLeaderboard, game.gameId]);

  // --- Banana Rot Logic ---
  useEffect(() => {
    const calculateRot = () => {
      // Get last interaction time and value for current user
      const lastInteractionTime = currentUser.lastInteractionTime || currentUser.lastInteractionT;
      const lastInteractionValue = currentUser.lastInteractionValue || currentUser.lastInteractionV || 0;
      
      // Get current coin balance (before rot is applied)
      const rawCoins = typeof currentUser.coins === "number" ? currentUser.coins : 0;
      
      // Reset rot if coins reach 0
      if (rawCoins <= 0) {
        setRotMultiplier(1.0);
        setRotLevel(0);
        return;
      }

      if (!lastInteractionTime) {
        // No trades yet, coins are fresh
        setRotMultiplier(1.0);
        setRotLevel(0);
        return;
      }

      // Calculate seconds since last trade
      let lastTradeDate: Date;
      if (typeof lastInteractionTime === 'object' && 'seconds' in lastInteractionTime) {
        lastTradeDate = new Date((lastInteractionTime as { seconds: number }).seconds * 1000);
      } else if (lastInteractionTime instanceof Date) {
        lastTradeDate = lastInteractionTime;
      } else {
        lastTradeDate = new Date(lastInteractionTime as string);
      }

      const now = new Date();
      const secondsSinceLastTrade = Math.floor((now.getTime() - lastTradeDate.getTime()) / 1000);

      // Use absolute value of lastInteractionValue (current tick when trade happened)
      const tradeSize = Math.abs(lastInteractionValue) || 50; // Default to 50 if undefined/0

      // Calculate dynamic cooldown based on trade size
      // Larger trades (higher tick values) = longer cooldown (more protection)
      // Formula: cooldown = minCooldown + (maxCooldown - minCooldown) * (tradeSize / (tradeSize + scaleFactor))
      const MIN_COOLDOWN = 20.0;   // Minimum 60 seconds (1 minute) cooldown before rot starts
      const MAX_COOLDOWN = 40.0;   // Maximum 90 seconds cooldown (larger trades get more protection)
      const COOLDOWN_SCALE = 100; // Adjust sensitivity (lower = faster growth)
      
      const cooldownSeconds = MIN_COOLDOWN + (MAX_COOLDOWN - MIN_COOLDOWN) * (tradeSize / (tradeSize + COOLDOWN_SCALE));

      // Apply cooldown period
      if (secondsSinceLastTrade < cooldownSeconds) {
        // Still in cooldown, coins are fresh
        setRotMultiplier(1.0);
        setRotLevel(0);
        return;
      }

      // Calculate time after cooldown (t in the formula)
      const t = secondsSinceLastTrade - cooldownSeconds;

      // Calculate decay coefficient based on trade size
      // Larger trades = slower decay (reward large trades)
      // Formula: coefficient = minCoeff + (maxCoeff - minCoeff) / (1 + tradeSize/scaleFactor)
      // Reduced coefficients to make rotting slower overall
      const MIN_COEFF = 0.005;  // Slowest decay for large trades (reduced from 0.02)
      const MAX_COEFF = 0.02;  // Fastest decay for tiny trades (reduced from 0.08)
      const DECAY_SCALE = 100; // Adjust this to tune sensitivity
      
      const coefficient = MIN_COEFF + (MAX_COEFF - MIN_COEFF) / (1 + tradeSize / DECAY_SCALE);

      // Apply exponential decay: e^(-coefficient * t)
      const multiplier = Math.exp(-coefficient * t);

      // Debug logging (only log occasionally to avoid spam)
      if (secondsSinceLastTrade % 5 === 0 && secondsSinceLastTrade > 0) {
        console.log('[Rot Debug]', {
          tradeSize,
          cooldownSeconds: cooldownSeconds.toFixed(2),
          secondsSinceLastTrade,
          timeAfterCooldown: t.toFixed(1),
          coefficient: coefficient.toFixed(4),
          multiplier: multiplier.toFixed(4),
          rotLevel: Math.min(4, Math.floor(t / 5))
        });
      }

      setRotMultiplier(multiplier);

      // Determine rot level for color changes (every 5 seconds after cooldown)
      // Level 0: 0-5s (fresh - ripe yellow)
      // Level 1: 5-10s (slightly brown)
      // Level 2: 10-15s (brown)
      // Level 3: 15-20s (dark brown)
      // Level 4: 20s+ (nearly black/rotten)
      const level = Math.min(4, Math.floor(t / 5));
      setRotLevel(level);
    };

    // Update rot calculation every second
    calculateRot();
    const interval = setInterval(calculateRot, 1000);
    return () => clearInterval(interval);
  }, [currentUser.lastInteractionTime, currentUser.lastInteractionT, currentUser.lastInteractionValue, currentUser.lastInteractionV]);

  // --- Actions ---
  const handleBuy = async () => {
    if (!user || !amount || parseFloat(amount) <= 0) return;
    setActionLoading("buy");
    setActionError("");
    try {
      await buyCoins(user.uid, parseFloat(amount), game.gameId ?? "");
      setAmount("");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to buy coins";
      setActionError(errorMessage);
      console.error("Failed to buy coins:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSell = async () => {
    if (!user || !amount || parseFloat(amount) <= 0) return;
    setActionLoading("sell");
    setActionError("");
    try {
      await sellCoins(user.uid, parseFloat(amount), game.gameId ?? "");
      setAmount("");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to sell coins";
      setActionError(errorMessage);
      console.error("Failed to sell coins:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleMinion = async (minionId: string) => {
    if (!user) return;
    
    console.log('[MainDashboard] Toggling minion:', {
      minionId,
      userId: currentUser.userId,
      gameId: game.gameId
    });
    
    setTogglingMinion(minionId);
    try {
      await toggleMinion(minionId, currentUser.userId, game.gameId ?? "");
      console.log('[MainDashboard] ✓ Minion toggled successfully');
      
      // Force refresh by waiting a moment for Redis to update
      setTimeout(() => {
        console.log('[MainDashboard] State should refresh from polling');
      }, 100);
    } catch (error) {
      console.error("[MainDashboard] ❌ Failed to toggle minion:", error);
    } finally {
      setTogglingMinion(null);
    }
  };

  // --- Wallet Data ---
  const usd = typeof currentUser.usd === "number" ? currentUser.usd : 0;
  const rawCoins = typeof currentUser.coins === "number" ? currentUser.coins : 0;
  const coins = Math.max(0, rawCoins * rotMultiplier); // Apply rot decay, prevent negative values
  const minions = Array.isArray(currentUser.bots) ? currentUser.bots : [];
  
  // Calculate total minion balances (USD + BC)
  const totalMinionUsd = minions.reduce((sum, minion: any) => {
    return sum + (typeof minion.usdBalance === 'number' ? minion.usdBalance : 0);
  }, 0);
  const totalMinionCoins = minions.reduce((sum, minion: any) => {
    return sum + (typeof minion.coinBalance === 'number' ? Math.max(0, minion.coinBalance) : 0);
  }, 0);
  
  // Combined balances (user + minions)
  const totalUsd = usd + totalMinionUsd;
  const totalCoins = coins + totalMinionCoins;

  // Banana rot color mapping
  const getRotColor = (level: number): { bg: string; border: string; text: string } => {
    switch (level) {
      case 0:
        // Fresh - Ripe yellow
        return {
          bg: "bg-yellow-100",
          border: "border-yellow-400",
          text: "text-yellow-900"
        };
      case 1:
        // Slightly brown
        return {
          bg: "bg-amber-100",
          border: "border-amber-500",
          text: "text-amber-900"
        };
      case 2:
        // Brown
        return {
          bg: "bg-orange-200",
          border: "border-orange-600",
          text: "text-orange-950"
        };
      case 3:
        // Dark brown
        return {
          bg: "bg-amber-800",
          border: "border-amber-900",
          text: "text-amber-100"
        };
      case 4:
      default:
        // Nearly black/rotten
        return {
          bg: "bg-stone-900",
          border: "border-stone-950",
          text: "text-stone-300"
        };
    }
  };

  // If coins value rounds to 0.00, always show as fresh (level 0)
  const coinsRounded = Number(coins.toFixed(2));
  const effectiveRotLevel = coinsRounded === 0 ? 0 : rotLevel;
  const rotColors = getRotColor(effectiveRotLevel);

  // Bot price mapping for performance calculation
  const BOT_PRICES: { [key: string]: number } = {
    "Random Bot": 300,
    "Momentum Bot": 800,
    "Mean Reversion Bot": 750,
    "Market Maker Bot": 1200,
    "Hedger Bot": 1000,
    "Custom Minion": 1750,
    // Backend type names (for backward compatibility)
    "random": 300,
    "momentum": 800,
    "mean_reversion": 750,
    "market_maker": 1200,
    "hedger": 1000,
  };

  // --- Chart Data ---
  const DISPLAY_WINDOW_SECONDS = 60;

  const formatTimeLabel = (totalSeconds: number): string => {
    const minutes = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
  };

  const getElapsedSeconds = (): number => {
    if (!game.startTime || !game.isStarted) return 0;
    const now = new Date();
    let startTime: Date;

    if (
      typeof game.startTime === "object" &&
      game.startTime !== null &&
      "seconds" in game.startTime &&
      typeof (game.startTime as any).seconds === "number"
    ) {
      startTime = new Date((game.startTime as { seconds: number }).seconds * 1000);
    } else if (game.startTime instanceof Date) {
      startTime = game.startTime;
    } else {
      startTime = new Date(game.startTime as any);
    }

    return Math.floor((now.getTime() - startTime.getTime()) / 1000);
  };

  const elapsedSeconds = getElapsedSeconds();
  const startIndex = Math.max(0, coinsArr.length - DISPLAY_WINDOW_SECONDS);
  // Ensure we always have at least one data point to prevent flashing
  const displayData = coinsArr.length > 0 ? coinsArr.slice(startIndex) : [1.0];
  const displayLabels = displayData.map((_, index) => {
    const dataPointSecond = elapsedSeconds - (displayData.length - 1 - index);
    return formatTimeLabel(Math.max(0, dataPointSecond));
  });

  const chartData = useMemo(() => ({
    labels: displayLabels,
    datasets: [
      {
        label: "Banana Coin Price",
        data: displayData,
        borderColor: "rgb(212, 160, 23)",
        backgroundColor: "rgba(212, 160, 23, 0.1)",
        tension: 0,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 0,
        borderWidth: 2,
      },
    ],
  }), [displayLabels.length, displayData.length, displayData[displayData.length - 1]]);

  // --- Chart Limits ---
  // Use only the displayed data for scale calculation to prevent flashing
  const validPrices = displayData.filter((p) => typeof p === "number" && p > 0);
  const minPrice = validPrices.length > 0 ? Math.min(...validPrices) : 0.5;
  const maxPrice = validPrices.length > 0 ? Math.max(...validPrices) : 1.5;
  const gridMin = Math.floor(minPrice * 0.8 * 10) / 10;
  const gridMax = Math.ceil(maxPrice * 1.2 * 10) / 10;
  const gridRange = gridMax - gridMin;
  const gridStep = Math.ceil((gridRange / 5) * 10) / 10;

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(42, 36, 16, 0.95)",
        titleColor: "#f5d76e",
        bodyColor: "#f5e6d3",
        borderColor: "#4a3c1f",
        borderWidth: 2,
        titleFont: { family: "VT323, monospace", size: 18 },
        bodyFont: { family: "VT323, monospace", size: 16 },
        callbacks: {
          title: (context: any) => `Time: ${context[0].label}`,
          label: (context: any) => `Price: $${context.parsed.y.toFixed(4)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(74, 60, 31, 0.3)" },
        ticks: {
          color: "#8b7355",
          font: { family: "VT323, monospace", size: 16 },
          maxTicksLimit: 10,
          autoSkip: true,
        },
      },
      y: {
        min: gridMin,
        max: gridMax,
        grid: { color: "rgba(74, 60, 31, 0.3)" },
        ticks: {
          color: "#8b7355",
          font: { family: "VT323, monospace", size: 16 },
          callback: (value: number | string) => "$" + Number(value).toFixed(2),
          stepSize: gridStep,
        },
      },
    },
    animation: { duration: 0 },
  }), [gridMin, gridMax, gridStep]);

  // --- Portfolio Stats ---
  // Include minion balances in portfolio value
  const portfolioValue = totalUsd + totalCoins * currentPrice;
  const portfolioChange = ((portfolioValue - 10000) / 10000) * 100;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-6 mb-6">
        <h2 className="font-retro text-4xl text-[var(--primary)] flex-shrink-0">
          MAIN DASHBOARD
        </h2>
        {/* News Carousel Banner - stretches between page name and clock */}
        <div className={`py-2 px-8 overflow-hidden relative flex items-center flex-1 min-w-0 ${isEventActive ? 'border-2 border-[var(--danger)] animate-flash-red rounded' : ''}`}>
          <div className="overflow-hidden relative w-full flex items-center">
            <div
              className="font-retro text-3xl whitespace-nowrap animate-scroll-fast inline-flex items-center gap-2 text-gray-700"
              style={{ willChange: 'transform' }}
            >
              {/* Duplicate content for seamless infinite scroll */}
              <span className="inline-block">
                {isEventActive && <TbAlertTriangle className="text-4xl inline-block mr-2" />}
                {`${newsText || "NO NEWS"} • `.repeat(6)}
              </span>
              <span className="inline-block">
                {isEventActive && <TbAlertTriangle className="text-4xl inline-block mr-2" />}
                {`${newsText || "NO NEWS"} • `.repeat(6)}
              </span>
            </div>
          </div>
        </div>
        <div className="px-6 py-3 border-2 border-[var(--border)] bg-[var(--card-bg)] flex-shrink-0">
          <div className="text-sm text-[var(--primary)] mb-1">TIME REMAINING</div>
          <div className="font-retro text-3xl text-[var(--primary-dark)] text-center">
            {timeRemaining}
          </div>
        </div>
        <button
          onClick={() => setShowLeaderboard(true)}
          className="px-6 py-3 border-2 border-[var(--border)] bg-[var(--card-bg)] hover:bg-[var(--primary)] hover:border-[var(--primary-dark)] transition-colors cursor-pointer flex items-center justify-center flex-shrink-0"
          style={{ aspectRatio: "1/1", height: "100%" }}
        >
          <FaTrophy className="text-4xl text-[var(--primary-dark)] hover:text-[var(--background)]" />
        </button>
      </div>
      <div
        style={{ display: "grid", gridTemplateColumns: "65% 35%", gap: "1.5rem" }}
        className="flex-1 min-h-0 pb-8"
      >
        <div className="flex flex-col min-h-0 overflow-hidden">
          <Card title="BANANA COIN MARKET" padding="lg" className="h-full flex flex-col">
            <div className="flex-1 min-h-0">
              <Line key="banana-coin-chart" data={chartData} options={chartOptions} />
            </div>
            <div className="mt-4 p-4 border-t-2 border-[var(--border)]">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-[var(--primary)]">Current Price</div>
                  <div className="font-retro text-3xl text-[var(--primary-dark)]">
                    ${currentPrice.toFixed(4)}
                  </div>
                  <div
                    className={`text-sm ${
                      priceChange >= 0 ? "text-green-500" : "text-red-500"
                    }`}
                  >
                    {priceChange >= 0 ? "▲" : "▼"} {Math.abs(priceChange).toFixed(4)} (
                    {priceChangePercent >= 0 ? "+" : ""}
                    {priceChangePercent.toFixed(2)}%)
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-[var(--primary)]">Your Total Trades</div>
                  <div className="font-retro text-2xl text-[var(--primary-dark)]">
                    {currentUserTotalTrades}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        <div className="flex flex-col gap-4 min-h-0 overflow-y-auto pr-2">
          <Card title="WALLET" padding="lg">
            <div className="space-y-3">
              <div className="p-3 bg-[var(--background)] border-2 border-[var(--border)]">
                <div className="text-sm text-[var(--primary)]">US Dollars</div>
                <div className="font-retro text-2xl text-[var(--success)]">
                  ${totalUsd.toFixed(2)}
                </div>
                {totalMinionUsd > 0 && (
                  <div className="text-xs text-[var(--primary)] mt-1">
                    (You: ${usd.toFixed(2)} + Minions: ${totalMinionUsd.toFixed(2)})
                  </div>
                )}
              </div>
              <div className={`p-3 border-2 transition-colors duration-500 ${rotColors.bg} ${rotColors.border}`}>
                <div className="text-sm text-[var(--primary)]">Banana Coins</div>
                <div className={`font-retro text-2xl transition-colors duration-500 ${rotColors.text}`}>
                  {coins.toFixed(2)} BC
                </div>
                {totalMinionCoins > 0 && (
                  <div className="text-xs text-[var(--primary)] mt-1">
                    Total: {totalCoins.toFixed(2)} BC (You + Minions)
                  </div>
                )}
              </div>
            </div>
          </Card>

          <Card title="ACTIONS" padding="lg">
            <div className="space-y-4">
              <Input
                label="Amount (BC)"
                type="number"
                placeholder="0.00"
                value={amount}
                onChange={(e) => {
                  setAmount(e.target.value);
                  setActionError(""); // Clear error when user types
                }}
                fullWidth
                min="0"
                step="0.01"
              />
              <div className="text-xs text-[var(--primary)] -mt-2">
                Cost: $
                {(parseFloat(amount || "0") * currentPrice).toFixed(4)} USD (@ $
                {currentPrice.toFixed(4)}/BC)
              </div>
              {actionError && (
                <div className="text-sm text-[var(--danger)] bg-red-50 border border-[var(--danger)] p-2 rounded">
                  {actionError}
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={handleBuy}
                  variant="success"
                  size="lg"
                  fullWidth
                  disabled={actionLoading !== null || !amount || parseFloat(amount) <= 0}
                >
                  {actionLoading === "buy" ? "Buying..." : "Buy"}
                </Button>
                <Button
                  onClick={handleSell}
                  variant="danger"
                  size="lg"
                  fullWidth
                  disabled={actionLoading !== null || !amount || parseFloat(amount) <= 0}
                >
                  {actionLoading === "sell" ? "Selling..." : "Sell"}
                </Button>
              </div>
            </div>
          </Card>

          <Card title={`MINIONS (${minions.length})`} padding="lg">
            {minions.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-[var(--primary)] mb-3">No minions yet</p>
                <p className="text-sm text-[var(--primary)]">
                  Visit the Shops tab to buy trading minions
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {minions.map((minion: any) => {
                  const isActive = minion.isActive ?? false;
                  const minionId = minion.botId ?? '';
                  const coinBalance = Math.max(0, typeof minion.coinBalance === 'number' ? minion.coinBalance : 0);
                  const usdBalance = typeof minion.usdBalance === 'number' ? minion.usdBalance : 0;

                  // Calculate performance based on total portfolio value (USD + BC value)
                  // Bots start with USD capital, not BC, so we need to track total portfolio value
                  const currentValue = (coinBalance * currentPrice) + usdBalance;

                  // Use actual starting USD balance if available (this is what the bot actually started with)
                  // Bots are allocated a percentage of their purchase price as starting capital
                  const startingUsdBalance = typeof minion.startingUsdBalance === 'number' ? minion.startingUsdBalance : 0;
                  
                  // Fallback: if startingUsdBalance is not available, estimate from bot cost
                  // (bots are allocated 70% of purchase price as starting capital)
                  const botName = minion.botName ?? "";
                  const baseBotName = botName.replace(/\s+\d+$/, ""); // Remove number suffix
                  const botCost = BOT_PRICES[baseBotName] || BOT_PRICES[botName] || 1000;
                  const estimatedStartingCapital = startingUsdBalance > 0 ? startingUsdBalance : (botCost * 0.7);
                  
                  // Initial value is the starting USD capital (bot starts with USD, not BC)
                  const initialValue = estimatedStartingCapital;

                  // Calculate performance
                  const valueChange = currentValue - initialValue;
                  const performancePercent = initialValue > 0 ? (valueChange / initialValue) * 100 : 0;

                  return (
                    <div
                      key={minionId || Math.random()}
                      className={`p-8 border-2 transition-colors ${
                        isActive
                          ? 'border-[var(--success)] bg-[var(--background)]'
                          : 'border-[var(--border)] bg-[var(--background)] opacity-70'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-retro text-lg text-[var(--primary-dark)]">
                          {getMinionDisplayName(minion.botName ?? "Minion")}
                        </div>
                        <Button
                          onClick={() => handleToggleMinion(minionId)}
                          variant={isActive ? "danger" : "success"}
                          size="sm"
                          disabled={togglingMinion !== null}
                        >
                          {togglingMinion === minionId
                            ? "..."
                            : isActive
                            ? "Stop"
                            : "Start"}
                        </Button>
                      </div>
                      <div className="text-xs text-[var(--primary)] space-y-1">
                        <div className="flex justify-between">
                          <span>Status:</span>
                          <span className={isActive ? "text-[var(--success)]" : "text-[var(--primary)]"}>
                            {isActive ? "Active" : "Stopped"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>BC Balance:</span>
                          <span className="text-[var(--primary-dark)]">
                            {coinBalance.toFixed(2)} BC
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Portfolio Value:</span>
                          <span className="text-[var(--success)]">
                            ${currentValue.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Performance:</span>
                          <span className={performancePercent >= 0 ? "text-[var(--success)]" : "text-[var(--danger)]"}>
                            {performancePercent >= 0 ? '+' : ''}{performancePercent.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Leaderboard Modal */}
      {showLeaderboard && (
        <div
          className="fixed inset-0 flex items-center justify-center z-50 p-8"
          style={{ backgroundColor: "rgba(0, 0, 0, 0.2)" }}
          onClick={() => setShowLeaderboard(false)}
        >
          <div
            className="w-full max-w-xl max-h-[80vh] overflow-y-auto border-2 border-[var(--border)] bg-[var(--card-bg)] p-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-8 pb-4 border-b-2 border-[var(--border)]">
              <h2 className="font-retro text-4xl text-[var(--primary)]">
                LEADERBOARD
              </h2>
              <button
                onClick={() => setShowLeaderboard(false)}
                className="text-3xl text-[var(--primary)] hover:text-[var(--danger)] transition-colors font-retro"
              >
                ✕
              </button>
            </div>

            {leaderboard.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-[var(--primary)] text-lg">Loading leaderboard...</p>
              </div>
            ) : (
              <div className="space-y-0">
                {leaderboard.map((entry, index) => {
                  const isCurrentUser = entry.userId === currentUser.userId;
                  // Recalculate wealth in real-time using current price
                  const liveWealth = entry.usdBalance + (Math.max(0, entry.coinBalance) * currentPrice);

                  return (
                    <div
                      key={entry.userId}
                      className={`py-5 px-4 border-b border-[var(--border)] flex items-center justify-between ${
                        isCurrentUser ? "bg-[var(--background)]" : ""
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="min-w-[3rem] flex items-center justify-center">
                          {index === 0 && <FaTrophy className="text-3xl text-yellow-400" />}
                          {index === 1 && <FaMedal className="text-3xl text-gray-400" />}
                          {index === 2 && <FaAward className="text-3xl text-amber-600" />}
                          {index > 2 && <span className="font-retro text-2xl text-[var(--primary-dark)]">#{index + 1}</span>}
                        </div>
                        <div className="font-retro text-xl text-[var(--primary-dark)]">
                          {entry.userName}
                        </div>
                      </div>
                      <div className="font-retro text-2xl text-[var(--success)]">
                        ${liveWealth.toFixed(2)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
