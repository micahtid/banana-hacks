"use client";

import { Card } from "@/components/Card";
import { type Game, type User } from "@/utils/database_functions";
import { useState } from "react";

interface TransactionsProps {
  game: Game;
  currentUser: User;
}

type FilterType = "all" | "buy" | "sell" | "minion";

// Helper function to get display name for a transaction actor
// Handles both new format (proper names) and old format (backend types)
function getDisplayName(name: string): string {
  // If it's a user name or already a display name (has spaces or starts with capital), return as-is
  if (!name.toLowerCase().includes('bot') || name.includes(' ') || /^[A-Z]/.test(name.replace('Bot_', ''))) {
    return name;
  }
  
  // For old bot names with format "Bot_12345678" or backend types
  if (name.startsWith('Bot_')) {
    // Check if it's just Bot_ID format
    const afterBot = name.substring(4);
    if (/^[a-f0-9]{8}$/.test(afterBot)) {
      // It's an old Bot_ID format, keep as-is for now
      return name;
    }
  }
  
  // For backend types like "mean_reversion", convert to user-friendly format
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default function Transactions({ game, currentUser }: TransactionsProps) {
  const [filter, setFilter] = useState<FilterType>("all");

  // Get all interactions/transactions
  const interactions = game.interactions || [];

  // Filter interactions (with defensive checks)
  const filteredInteractions = interactions.filter((interaction) => {
    // Defensive: skip interactions without name field
    if (!interaction.name) return false;
    
    if (filter === "all") return true;
    
    // Minion filter: check both name field and interactionName for backward compatibility
    if (filter === "minion") {
      const nameHasBot = interaction.name.toLowerCase().includes("bot");
      const interactionNameHasBot = interaction.interactionName && 
                                    interaction.interactionName.toLowerCase().includes("bot");
      return nameHasBot || interactionNameHasBot;
    }
    
    return interaction.type && interaction.type.toLowerCase() === filter;
  });

  // Sort by most recent (if we had timestamps, we'd sort by those)
  const sortedInteractions = [...filteredInteractions].reverse();

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

      {/* Filters */}
      <Card padding="lg">
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setFilter("all")}
            className={`
              font-retro text-lg px-6 py-2 border-2 transition-all
              ${
                filter === "all"
                  ? "bg-[var(--primary)] border-[var(--primary-light)] text-[var(--background)]"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--primary)]"
              }
            `}
          >
            ALL
          </button>
          <button
            onClick={() => setFilter("buy")}
            className={`
              font-retro text-lg px-6 py-2 border-2 transition-all
              ${
                filter === "buy"
                  ? "bg-[var(--success)] border-green-300 text-white"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--success)]"
              }
            `}
          >
            BUYS
          </button>
          <button
            onClick={() => setFilter("sell")}
            className={`
              font-retro text-lg px-6 py-2 border-2 transition-all
              ${
                filter === "sell"
                  ? "bg-[var(--danger)] border-red-300 text-white"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--danger)]"
              }
            `}
          >
            SELLS
          </button>
          <button
            onClick={() => setFilter("minion")}
            className={`
              font-retro text-lg px-6 py-2 border-2 transition-all
              ${
                filter === "minion"
                  ? "bg-[var(--accent)] border-orange-300 text-white"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--accent)]"
              }
            `}
          >
            MINION TRADES
          </button>
        </div>
      </Card>

      {/* Transactions List */}
      <Card title={`${filter.toUpperCase()} TRANSACTIONS (${sortedInteractions.length})`} padding="lg">
        {sortedInteractions.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-xl text-[var(--foreground)] mb-2">
              No transactions yet
            </p>
            <p className="text-sm text-[var(--foreground)]">
              {filter === "all"
                ? "Start trading to see your transaction history"
                : `No ${filter} transactions found`}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {sortedInteractions.map((interaction, index) => {
              // Defensive checks - skip malformed interactions
              if (!interaction.name || !interaction.type) return null;
              
              const isCurrentUser = interaction.name === currentUser.userName;
              // Check for minion: case-insensitive check on both name and interactionName
              const isMinion = interaction.name.toLowerCase().includes("bot") ||
                           (interaction.interactionName && interaction.interactionName.toLowerCase().includes("bot"));

              return (
                <div
                  key={index}
                  className={`
                    p-4 border-2 transition-all
                    ${
                      isCurrentUser
                        ? "border-[var(--primary)] bg-[var(--border)]"
                        : "border-[var(--border)] bg-[var(--background)] hover:border-[var(--border)]"
                    }
                  `}
                >
                  <div className="flex items-center justify-between">
                    {/* Left: Trader Info */}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-retro text-lg text-[var(--primary-light)]">
                          {getDisplayName(interaction.name)}
                        </span>
                        {isCurrentUser && (
                          <span className="text-xs bg-[var(--primary)] text-[var(--background)] px-2 py-1 font-bold">
                            YOU
                          </span>
                        )}
                        {isMinion && (
                          <span className="text-xs bg-[var(--accent)] text-white px-2 py-1 font-bold">
                            MINION
                          </span>
                        )}
                      </div>
                      <div className={`text-sm font-bold uppercase ${getTypeColor(interaction.type)}`}>
                        {interaction.type}
                      </div>
                    </div>

                    {/* Right: Transaction Details */}
                    <div className="text-right">
                      <div className="font-retro text-2xl text-[var(--primary)]">
                        {interaction.value ? Math.abs(interaction.value).toFixed(2) : "0.00"} BC
                      </div>
                      <div className="text-xs text-[var(--foreground)]">
                        {/* Mock timestamp - in real implementation, use actual timestamp */}
                        {Math.floor((interactions.length - index) / 60)}h {((interactions.length - index) % 60)} m ago
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Transaction Stats */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card padding="lg">
          <div className="text-center">
            <div className="text-sm text-[var(--foreground)] mb-1">Total Buys</div>
            <div className="font-retro text-2xl text-[var(--success)]">
              {interactions.filter((i) => i.type && i.type.toLowerCase() === "buy").length}
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="text-center">
            <div className="text-sm text-[var(--foreground)] mb-1">Total Sells</div>
            <div className="font-retro text-2xl text-[var(--danger)]">
              {interactions.filter((i) => i.type && i.type.toLowerCase() === "sell").length}
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="text-center">
            <div className="text-sm text-[var(--foreground)] mb-1">Minion Trades</div>
            <div className="font-retro text-2xl text-[var(--accent)]">
              {interactions.filter((i) => 
                (i.name && i.name.toLowerCase().includes("bot")) ||
                (i.interactionName && i.interactionName.toLowerCase().includes("bot"))
              ).length}
            </div>
          </div>
        </Card>
      </div>

    </div>
  );
}
