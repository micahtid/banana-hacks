"use client";

import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { type Game, type User } from "@/utils/database_functions";
import { useState } from "react";
import { FaUser, FaRobot } from "react-icons/fa";

interface TransactionsProps {
  game: Game;
  currentUser: User;
}

type TabType = "users" | "minions";

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
    const playerName = player.playerName || player.userName;
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
  const [activeTab, setActiveTab] = useState<TabType>("users");
  const [showAll, setShowAll] = useState(false);

  // Get all interactions/transactions
  const interactions = game.interactions || [];

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
    if (!interaction.name && !interaction.interactionName) return false;

    const name = (interaction.name || "").toLowerCase();
    const interactionName = (interaction.interactionName || "").toLowerCase();
    const description = (interaction.interactionDescription || "").toLowerCase();

    // Direct keyword checks
    if (name.includes("bot") || name.includes("minion") ||
        interactionName.includes("bot") || interactionName.includes("minion") ||
        description.includes("bot") || description.includes("minion")) {
      return true;
    }

    // Check against all known bot identifiers
    if (Array.from(allBotIdentifiers).some(identifier =>
      name.includes(identifier) ||
      interactionName.includes(identifier) ||
      description.includes(identifier)
    )) {
      return true;
    }

    // Check if it's NOT a known player name (if it's not a player, might be a bot)
    const isKnownPlayer = Array.from(allPlayerNames).some(playerName =>
      name.includes(playerName) || interactionName.includes(playerName)
    );

    // If name contains "Bot_" prefix, it's definitely a bot
    if (name.startsWith("bot_") || interactionName.startsWith("bot_")) {
      return true;
    }

    return false;
  };

  // Separate user and minion transactions
  const userTransactions = interactions.filter((interaction) => !isTransactionFromMinion(interaction));
  const minionTransactions = interactions.filter((interaction) => isTransactionFromMinion(interaction));

  // Get the appropriate list based on active tab
  const displayTransactions = activeTab === "users" ? userTransactions : minionTransactions;

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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="font-retro text-4xl text-[var(--primary-light)]">
          TRANSACTIONS
        </h2>
        <div className="text-right">
          <div className="text-sm text-[var(--foreground)]">Total Trades</div>
          <div className="font-retro text-3xl text-[var(--primary)]">
            {interactions.length}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Card padding="lg">
        <div className="flex gap-3">
          <button
            onClick={() => {
              setActiveTab("users");
              setShowAll(false);
            }}
            className={`
              font-retro text-lg px-8 py-3 border-2 transition-all flex items-center gap-2
              ${
                activeTab === "users"
                  ? "bg-[var(--primary)] border-[var(--primary-light)] text-[var(--background)]"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--primary)]"
              }
            `}
          >
            <FaUser />
            USERS
          </button>
          <button
            onClick={() => {
              setActiveTab("minions");
              setShowAll(false);
            }}
            className={`
              font-retro text-lg px-8 py-3 border-2 transition-all flex items-center gap-2
              ${
                activeTab === "minions"
                  ? "bg-[var(--accent)] border-orange-300 text-white"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--accent)]"
              }
            `}
          >
            <FaRobot />
            MINIONS
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
              {activeTab === "users"
                ? "User buy/sell transactions will appear here"
                : "Minion trading activity will appear here"}
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {visibleTransactions.map((interaction, index) => {
                // Defensive checks - skip malformed interactions
                if (!interaction.name || !interaction.type) return null;

                const isCurrentUser = interaction.name === currentUser.userName;
                const isMinion = activeTab === "minions";

                return (
                  <div
                    key={index}
                    className="p-4 border-2 border-[var(--border)] bg-[var(--background)] hover:border-[var(--primary)] transition-all"
                  >
                    <div className="flex items-center justify-between">
                      {/* Left: Trader Info */}
                      <div className="flex items-center gap-3">
                        {isMinion ? (
                          <FaRobot className="text-2xl text-[var(--accent)]" />
                        ) : (
                          <FaUser className="text-2xl text-[var(--primary)]" />
                        )}
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-retro text-lg text-[var(--primary-light)]">
                              {getDisplayName(interaction.name, game)}
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
                          {interaction.value ? Math.abs(interaction.value).toFixed(2) : "0.00"} BC
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
              {activeTab === "users" ? "User" : "Minion"} Buys
            </div>
            <div className="font-retro text-2xl text-[var(--success)]">
              {displayTransactions.filter((i) => i.type && i.type.toLowerCase() === "buy").length}
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="text-center">
            <div className="text-sm text-[var(--foreground)] mb-1">
              {activeTab === "users" ? "User" : "Minion"} Sells
            </div>
            <div className="font-retro text-2xl text-[var(--danger)]">
              {displayTransactions.filter((i) => i.type && i.type.toLowerCase() === "sell").length}
            </div>
          </div>
        </Card>
      </div>

    </div>
  );
}
