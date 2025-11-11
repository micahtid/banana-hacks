"use client";

import React from "react";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { type Game, type User } from "@/utils/database_functions";
import { useState, useEffect, useRef } from "react";
import { FaUser } from "react-icons/fa";
import { TbAlertTriangle } from "react-icons/tb";

interface TransactionsProps {
  game: Game;
  currentUser: User;
}

type TabType = "buy" | "sell";

// Helper function to get display name for a transaction actor
// Formats minion names as username_botname_number and keeps user names as-is
function getDisplayName(name: string, game: Game): string {
  const nameLower = name.toLowerCase();

  // Check if this is a minion transaction
  const isMinion = nameLower.includes('bot') || nameLower.includes('minion');

  if (!isMinion) {
    return name; // Regular user name
  }

  // Try to find which player owns this bot and format properly
  for (const player of (game.players || [])) {
    const playerName = (player as any).playerName || (player as any).userName;
    for (const bot of (player.bots || [])) {
      const botName = bot.botName;
      const botId = bot.botId;

      // Check by bot name
      if (botName && (nameLower.includes(botName.toLowerCase()) || name.includes(botName))) {
        // Bot name already includes number (e.g. "Momentum Bot 1")
        // Format as username_bottype_number
        const botNameParts = botName.match(/^(.+?)\s+(\d+)$/);
        if (botNameParts) {
          // Has format "Bot Type Number"
          const botType = botNameParts[1].replace(/\s+/g, '_');
          const botNumber = botNameParts[2];
          return `${playerName}_${botType}_${botNumber}`;
        } else {
          // No number, just use bot name
          return `${playerName}_${botName.replace(/\s+/g, '_')}`;
        }
      }

      // Check by bot ID
      if (botId && (nameLower.includes(botId.toLowerCase()) || name.includes(botId))) {
        const botNameParts = botName ? botName.match(/^(.+?)\s+(\d+)$/) : null;
        if (botNameParts) {
          const botType = botNameParts[1].replace(/\s+/g, '_');
          const botNumber = botNameParts[2];
          return `${playerName}_${botType}_${botNumber}`;
        } else {
          return `${playerName}_${botName ? botName.replace(/\s+/g, '_') : botId}`;
        }
      }
    }
  }

  // Fallback: if we can't match to a specific bot, clean up the name
  if (name.startsWith('Bot_') || name.startsWith('bot_')) {
    return name; // Keep bot ID format
  }

  // For backend types like "mean_reversion", convert to user-friendly format
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Helper function to calculate time ago from timestamp
function getTimeAgo(timestamp: string | number | Date | undefined): string {
  if (!timestamp) return "Unknown";

  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return `${diffSecs}s ago`;
  } catch {
    return "Unknown";
  }
}

export default function Transactions({ game, currentUser }: TransactionsProps) {
  const [activeTab, setActiveTab] = useState<TabType>("buy");
  const [showAll, setShowAll] = useState(false);
  const [newsText, setNewsText] = useState<string>("NO NEWS");
  const [isEventActive, setIsEventActive] = useState<boolean>(false);
  const [previousEventTriggered, setPreviousEventTriggered] = useState<boolean>(false);
  const eventTimerRef = useRef<NodeJS.Timeout | null>(null);
  const genericNewsTimerRef = useRef<NodeJS.Timeout | null>(null);
  const currentIntervalRef = useRef<number>(20000); // Track current interval
  const genericNewsIndexRef = useRef<number>(0);
  const allGenericNewsRef = useRef<string[]>([]);
  const isEventActiveRef = useRef<boolean>(false);

  // Event News Banner Logic
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
        // Update ref with new headlines (always update ref to latest)
        allGenericNewsRef.current = allGenericNews;
        
        // Only clear and recreate interval if:
        // 1. Headlines actually changed (content changed)
        // 2. No interval exists yet (first time setup)
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
      // When event is active, ensure rotation is stopped
      if (genericNewsTimerRef.current) {
        clearInterval(genericNewsTimerRef.current);
        genericNewsTimerRef.current = null;
      }
    }
    
    // Cleanup on unmount
    return () => {
      // Only cleanup on unmount or when event state changes
      // Don't cleanup on every render to avoid interrupting rotation
    };
  }, [(game as any).allGenericNews, (game as any).genericNews, game.eventTriggered, isEventActive]);

  // Get all interactions/transactions - filter to only user transactions (no bots)
  const allInteractions = game.interactions || [];

  // Collect all bot identifiers from all players for identification
  const allBotIdentifiers = new Set<string>();
  const allPlayerNames = new Set<string>();

  (game.players || []).forEach((player: any) => {
    const playerName = player.playerName || player.userName;
    if (playerName) {
      allPlayerNames.add(playerName.toLowerCase());
    }

    (player.bots || []).forEach((bot: any) => {
      // Add bot name
      if (bot.botName) {
        allBotIdentifiers.add(bot.botName.toLowerCase());
      }
      // Add bot ID
      if (bot.botId) {
        allBotIdentifiers.add(bot.botId.toLowerCase());
      }
      // Add bot type if available
      if ((bot as any).botType) {
        allBotIdentifiers.add((bot as any).botType.toLowerCase());
      }
    });
  });

  // Helper function to check if a transaction is from a minion
  const isTransactionFromMinion = (interaction: any): boolean => {
    // First check: if backend explicitly marks it as a bot transaction
    if ((interaction as any).is_bot === true || (interaction as any).isBot === true) {
      return true;
    }

    // Second check: if the name field contains bot/minion keywords
    const name = (interaction.name || "").toLowerCase();
    if (name.includes("bot_") || name.startsWith("bot_")) {
      return true;
    }

    // Third check: match against known bot names from players
    if (Array.from(allBotIdentifiers).some(identifier =>
      name.includes(identifier.toLowerCase())
    )) {
      return true;
    }

    // Otherwise, assume it's a user transaction
    return false;
  };

  // Filter to only user transactions (no bots/minions)
  const userTransactions = allInteractions.filter((interaction) => {
    const isBot = isTransactionFromMinion(interaction);
    return !isBot;
  });

  // Separate user transactions by type (buy/sell)
  const buyTransactions = userTransactions.filter((interaction) =>
    interaction.type && interaction.type.toLowerCase() === "buy"
  );
  const sellTransactions = userTransactions.filter((interaction) =>
    interaction.type && interaction.type.toLowerCase() === "sell"
  );

  // Get the appropriate list based on active tab
  const displayTransactions = activeTab === "buy" ? buyTransactions : sellTransactions;

  // Sort by most recent and limit to 10 if not showing all
  const sortedTransactions = [...displayTransactions].reverse();
  const visibleTransactions = showAll ? sortedTransactions : sortedTransactions.slice(0, 10);

  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "buy":
        return "text-[var(--success)]";
      case "sell":
        return "text-[var(--danger)]";
      case "bot":
        return "text-[var(--accent)]";
      default:
        return "text-[var(--foreground)]";
    }
  };


  return (
    <div>
      {/* Header with News Flash */}
      <div className="flex items-center gap-6 mt-4 mb-10">
        <h2 className="font-retro text-4xl text-[var(--primary)] flex-shrink-0">
          TRANSACTIONS
        </h2>
        {/* News Carousel Banner - stretches between page name and trade count */}
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
        <div className="text-right flex-shrink-0">
          <div className="text-sm text-[var(--foreground)]">Total User Trades</div>
          <div className="font-retro text-3xl text-[var(--primary)]">
            {userTransactions.length}
          </div>
        </div>
      </div>

      <div className="space-y-6">

      {/* Tabs */}
      <Card padding="lg">
        <div className="flex gap-3">
          <button
            onClick={() => {
              setActiveTab("buy");
              setShowAll(false);
            }}
            className={`
              font-retro text-lg px-8 py-3 border-2 transition-all flex items-center gap-2
              ${
                activeTab === "buy"
                  ? "bg-[var(--success)] border-green-300 text-white"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--success)]"
              }
            `}
          >
            BUY
          </button>
          <button
            onClick={() => {
              setActiveTab("sell");
              setShowAll(false);
            }}
            className={`
              font-retro text-lg px-8 py-3 border-2 transition-all flex items-center gap-2
              ${
                activeTab === "sell"
                  ? "bg-[var(--danger)] border-red-300 text-white"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--danger)]"
              }
            `}
          >
            SELL
          </button>
        </div>
      </Card>

      {/* Transactions List */}
      <Card title={`${activeTab.toUpperCase()} TRANSACTIONS (${sortedTransactions.length})`} padding="lg">
        {sortedTransactions.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-xl text-[var(--foreground)] mb-2">
              No {activeTab} transactions yet
            </p>
            <p className="text-sm text-[var(--foreground)]">
              {activeTab === "buy"
                ? "User buy transactions will appear here"
                : "User sell transactions will appear here"}
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {visibleTransactions.map((interaction, index) => {
                // Defensive checks - skip malformed interactions
                if (!interaction.name || !interaction.type) return null;

                const isCurrentUser = interaction.name === currentUser.userName;

                return (
                  <div
                    key={index}
                    className="p-8 border-2 border-[var(--border)] bg-[var(--background)] hover:border-[var(--primary)] transition-all"
                  >
                    <div className="flex items-center justify-between">
                      {/* Left: Trader Info */}
                      <div className="flex items-center gap-3">
                        <FaUser className="text-2xl text-[var(--primary)]" />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-retro text-lg text-[var(--primary-light)]">
                              {interaction.name}
                            </span>
                            {isCurrentUser && (
                              <span className="text-xs bg-[var(--primary)] text-[var(--background)] px-2 py-1 font-bold">
                                YOU
                              </span>
                            )}
                          </div>
                          <div className={`text-sm font-bold uppercase ${getTypeColor(interaction.type)}`}>
                            {interaction.type}
                          </div>
                        </div>
                      </div>

                      {/* Right: Transaction Details */}
                      <div className="text-right">
                        <div className="font-retro text-2xl text-[var(--primary)]">
                          {interaction.value ? (Math.abs(interaction.value) / 100).toFixed(2) : "0.00"} BC
                        </div>
                        <div className="text-xs text-[var(--foreground)]">
                          {getTimeAgo((interaction as any).timestamp)}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* See All Button */}
            {sortedTransactions.length > 10 && !showAll && (
              <div className="mt-6 text-center">
                <Button
                  onClick={() => setShowAll(true)}
                  variant="primary"
                  size="lg"
                >
                  See All ({sortedTransactions.length} total)
                </Button>
              </div>
            )}

            {showAll && sortedTransactions.length > 10 && (
              <div className="mt-6 text-center">
                <Button
                  onClick={() => setShowAll(false)}
                  variant="secondary"
                  size="lg"
                >
                  Show Less
                </Button>
              </div>
            )}
          </>
        )}
      </Card>

      {/* Transaction Stats */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card padding="lg">
          <div className="text-center">
            <div className="text-sm text-[var(--foreground)] mb-1">
              Total User Buys
            </div>
            <div className="font-retro text-2xl text-[var(--success)]">
              {buyTransactions.length}
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="text-center">
            <div className="text-sm text-[var(--foreground)] mb-1">
              Total User Sells
            </div>
            <div className="font-retro text-2xl text-[var(--danger)]">
              {sellTransactions.length}
            </div>
          </div>
        </Card>
      </div>
      </div>
    </div>
  );
}
