"use client";

import { Card } from "@/components/Card";
import { type Game, type User } from "@/utils/database_functions";
import { useState } from "react";

interface TransactionsProps {
  game: Game;
  currentUser: User;
}

type FilterType = "all" | "buy" | "sell" | "bot";

export default function Transactions({ game, currentUser }: TransactionsProps) {
  const [filter, setFilter] = useState<FilterType>("all");

  // Get all interactions/transactions
  const interactions = game.interactions || [];

  // Filter interactions
  const filteredInteractions = interactions.filter((interaction) => {
    if (filter === "all") return true;
    if (filter === "bot") return interaction.name.includes("Bot");
    return interaction.type.toLowerCase() === filter;
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
            onClick={() => setFilter("bot")}
            className={`
              font-retro text-lg px-6 py-2 border-2 transition-all
              ${
                filter === "bot"
                  ? "bg-[var(--accent)] border-orange-300 text-white"
                  : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--accent)]"
              }
            `}
          >
            BOT TRADES
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
              const isCurrentUser = interaction.name === currentUser.userName;
              const isBot = interaction.name.includes("Bot");

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
                          {interaction.name}
                        </span>
                        {isCurrentUser && (
                          <span className="text-xs bg-[var(--primary)] text-[var(--background)] px-2 py-1 font-bold">
                            YOU
                          </span>
                        )}
                        {isBot && (
                          <span className="text-xs bg-[var(--accent)] text-white px-2 py-1 font-bold">
                            BOT
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
                        {Math.abs(interaction.value).toFixed(2)} BC
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
              {interactions.filter((i) => i.type.toLowerCase() === "buy").length}
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="text-center">
            <div className="text-sm text-[var(--foreground)] mb-1">Total Sells</div>
            <div className="font-retro text-2xl text-[var(--danger)]">
              {interactions.filter((i) => i.type.toLowerCase() === "sell").length}
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="text-center">
            <div className="text-sm text-[var(--foreground)] mb-1">Bot Trades</div>
            <div className="font-retro text-2xl text-[var(--accent)]">
              {interactions.filter((i) => i.name.includes("Bot")).length}
            </div>
          </div>
        </Card>
      </div>

    </div>
  );
}
