"use client";

import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { type Game, type User, buyCoins, sellCoins } from "@/utils/database_functions";
import { useState, useEffect } from "react";
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

// Register ChartJS components
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

export default function MainDashboard({ game, currentUser }: MainDashboardProps) {
  const { user } = useUser();
  const [amount, setAmount] = useState("");
  const [actionLoading, setActionLoading] = useState<"buy" | "sell" | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<string>("--:--");

  const currentPrice = game.coin[game.coin.length - 1] || 100;

  useEffect(() => {
    if (!game.startTime || !game.isStarted) {
      setTimeRemaining("--:--");
      return;
    }

    const updateTimer = () => {
      const now = new Date();

      // Handle Firestore Timestamp objects
      let startTime: Date;
      if (game.startTime && typeof game.startTime === 'object' && 'seconds' in game.startTime) {
        // Firestore Timestamp
        startTime = new Date((game.startTime as any).seconds * 1000);
      } else if (game.startTime instanceof Date) {
        startTime = game.startTime;
      } else {
        startTime = new Date(game.startTime);
      }

      const endTime = new Date(startTime.getTime() + game.gameDuration * 60000);
      const diff = endTime.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeRemaining("00:00");
        return;
      }

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeRemaining(`${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [game.startTime, game.gameDuration, game.isStarted]);

  const handleBuy = async () => {
    if (!user || !amount || parseFloat(amount) <= 0) return;

    setActionLoading("buy");
    try {
      // TO UPDATE: This will call backend buy(userId, numBC, gameId)
      await buyCoins(user.uid, parseFloat(amount), game.gameId);
      setAmount("");
    } catch (error) {
      console.error("Failed to buy coins:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSell = async () => {
    if (!user || !amount || parseFloat(amount) <= 0) return;

    setActionLoading("sell");
    try {
      // TO UPDATE: This will call backend sell(userId, numBC, gameId)
      await sellCoins(user.uid, parseFloat(amount), game.gameId);
      setAmount("");
    } catch (error) {
      console.error("Failed to sell coins:", error);
    } finally {
      setActionLoading(null);
    }
  };

  // Prepare chart data
  const chartData = {
    labels: game.coin.map((_, index) => `${index}m`),
    datasets: [
      {
        label: "Banana Coin Price",
        data: game.coin,
        borderColor: "rgb(212, 160, 23)",
        backgroundColor: "rgba(212, 160, 23, 0.1)",
        tension: 0.4,
        fill: true,
        pointRadius: 2,
        pointHoverRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: "rgba(42, 36, 16, 0.95)",
        titleColor: "#f5d76e",
        bodyColor: "#f5e6d3",
        borderColor: "#4a3c1f",
        borderWidth: 2,
        titleFont: {
          family: "var(--font-vt323), monospace",
          size: 16,
        },
        bodyFont: {
          family: "var(--font-geist-sans), sans-serif",
          size: 14,
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: "rgba(74, 60, 31, 0.3)",
        },
        ticks: {
          color: "#f5e6d3",
          font: {
            family: "var(--font-geist-mono), monospace",
          },
        },
      },
      y: {
        grid: {
          color: "rgba(74, 60, 31, 0.3)",
        },
        ticks: {
          color: "#f5e6d3",
          font: {
            family: "var(--font-geist-mono), monospace",
          },
          callback: function(value: any) {
            return '$' + value;
          },
        },
      },
    },
  };

  // Calculate portfolio value
  const portfolioValue = currentUser.usd + (currentUser.coins * currentPrice);
  const portfolioChange = ((portfolioValue - 10000) / 10000) * 100;

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <div className="grid grid-cols-[65fr,35fr] gap-6 h-full p-8">
        {/* Left Column - Market Graph */}
        <div className="flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-retro text-4xl text-[var(--primary-light)]">
              MAIN DASHBOARD
            </h2>
            <div className="px-6 py-3 border-2 border-[var(--border)] bg-[var(--card-bg)]">
              <div className="text-sm text-[var(--foreground)] mb-1">TIME REMAINING</div>
              <div className="font-retro text-3xl text-[var(--primary)] text-center">
                {timeRemaining}
              </div>
            </div>
          </div>
          <Card title="BANANA COIN MARKET" padding="lg" className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 min-h-0">
              <Line data={chartData} options={chartOptions} />
            </div>
            <div className="mt-4 p-4 border-t-2 border-[var(--border)]">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-[var(--foreground)]">Current Price</div>
                  <div className="font-retro text-3xl text-[var(--primary)]">
                    ${currentPrice.toFixed(2)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-[var(--foreground)]">Total Volume</div>
                  <div className="font-retro text-2xl text-[var(--accent)]">
                    {game.interactions.length} trades
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column - Wallet, Actions, Bots */}
        <div className="flex flex-col gap-4 min-h-0 overflow-y-auto pr-2">
          {/* Wallet */}
          <Card title="WALLET" padding="lg">
            <div className="space-y-3">
              <div className="p-3 bg-[var(--background)] border-2 border-[var(--border)]">
                <div className="text-sm text-[var(--foreground)]">US Dollars</div>
                <div className="font-retro text-2xl text-[var(--success)]">
                  ${currentUser.usd.toFixed(2)}
                </div>
              </div>
              <div className="p-3 bg-[var(--background)] border-2 border-[var(--border)]">
                <div className="text-sm text-[var(--foreground)]">Banana Coins</div>
                <div className="font-retro text-2xl text-[var(--primary)]">
                  {currentUser.coins.toFixed(2)} BC
                </div>
              </div>
            </div>
          </Card>

          {/* Actions */}
          <Card title="ACTIONS" padding="lg">
            <div className="space-y-4">
              <Input
                label="Amount (BC)"
                type="number"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                fullWidth
                min="0"
                step="0.01"
              />
              <div className="text-xs text-[var(--foreground)] -mt-2">
                Cost: ${(parseFloat(amount || "0") * currentPrice).toFixed(2)} USD
              </div>
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

          {/* Bots */}
          <Card title={`BOTS (${currentUser.bots.length})`} padding="lg">
            {currentUser.bots.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-[var(--foreground)] mb-3">
                  No bots yet
                </p>
                <p className="text-sm text-[var(--foreground)]">
                  Visit the Shops tab to buy trading bots
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {currentUser.bots.map((bot) => (
                  <div
                    key={bot.botId}
                    className="p-3 border-2 border-[var(--border)] bg-[var(--background)] hover:border-[var(--primary)] transition-colors"
                  >
                    <div className="font-retro text-lg text-[var(--primary-light)] mb-2">
                      {bot.botName}
                    </div>
                    <div className="text-sm text-[var(--foreground)]">
                      {/* Mock data for now */}
                      <div className="flex justify-between">
                        <span>Trades:</span>
                        <span className="text-[var(--accent)]">
                          {Math.floor(Math.random() * 50) + 10}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Performance:</span>
                        <span className="text-[var(--success)]">
                          +{(Math.random() * 20 + 5).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>BC Earned:</span>
                        <span className="text-[var(--primary)]">
                          {(Math.random() * 100 + 20).toFixed(2)} BC
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
