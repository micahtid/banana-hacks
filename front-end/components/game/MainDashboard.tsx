"use client";

import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import {
  type Game,
  type User,
  buyCoins,
  sellCoins,
  toggleBot,
} from "@/utils/database_functions";
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
  const [amount, setAmount] = useState<string>("");
  const [actionLoading, setActionLoading] = useState<"buy" | "sell" | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<string>("--:--");
  const [togglingBot, setTogglingBot] = useState<string | null>(null);

  // Safe defaults for optional arrays or values
  const coinsArr = Array.isArray(game.coin) ? game.coin : [];
  const interactionsArr = Array.isArray(game.interactions)
    ? game.interactions
    : [];

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
        "seconds" in game.startTime &&
        typeof (game.startTime as any).seconds === "number"
      ) {
        startTime = new Date((game.startTime as { seconds: number }).seconds * 1000);
      } else if (game.startTime instanceof Date) {
        startTime = game.startTime;
      } else {
        startTime = new Date(game.startTime as string);
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

  // --- Actions ---
  const handleBuy = async () => {
    if (!user || !amount || parseFloat(amount) <= 0) return;
    setActionLoading("buy");
    try {
      await buyCoins(user.uid, parseFloat(amount), game.gameId ?? "");
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
      await sellCoins(user.uid, parseFloat(amount), game.gameId ?? "");
      setAmount("");
    } catch (error) {
      console.error("Failed to sell coins:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleBot = async (botId: string) => {
    if (!user) return;
    
    console.log('[MainDashboard] Toggling bot:', {
      botId,
      userId: currentUser.userId,
      gameId: game.gameId
    });
    
    setTogglingBot(botId);
    try {
      await toggleBot(botId, currentUser.userId, game.gameId ?? "");
      console.log('[MainDashboard] ✓ Bot toggled successfully');
      
      // Force refresh by waiting a moment for Redis to update
      setTimeout(() => {
        console.log('[MainDashboard] State should refresh from polling');
      }, 100);
    } catch (error) {
      console.error("[MainDashboard] ❌ Failed to toggle bot:", error);
    } finally {
      setTogglingBot(null);
    }
  };

  // --- Wallet Data ---
  const usd = typeof currentUser.usd === "number" ? currentUser.usd : 0;
  const coins = typeof currentUser.coins === "number" ? currentUser.coins : 0;
  const bots = Array.isArray(currentUser.bots) ? currentUser.bots : [];

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
      "seconds" in game.startTime &&
      typeof (game.startTime as any).seconds === "number"
    ) {
      startTime = new Date((game.startTime as { seconds: number }).seconds * 1000);
    } else if (game.startTime instanceof Date) {
      startTime = game.startTime;
    } else {
      startTime = new Date(game.startTime as string);
    }

    return Math.floor((now.getTime() - startTime.getTime()) / 1000);
  };

  const elapsedSeconds = getElapsedSeconds();
  const startIndex = Math.max(0, coinsArr.length - DISPLAY_WINDOW_SECONDS);
  const displayData = coinsArr.slice(startIndex);
  const displayLabels = displayData.map((_, index) => {
    const dataPointSecond = elapsedSeconds - (displayData.length - 1 - index);
    return formatTimeLabel(Math.max(0, dataPointSecond));
  });

  const chartData = {
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
  };

  // --- Chart Limits ---
  const validPrices = coinsArr.filter((p) => typeof p === "number" && p > 0);
  const minPrice = validPrices.length > 0 ? Math.min(...validPrices) : 0.5;
  const maxPrice = validPrices.length > 0 ? Math.max(...validPrices) : 1.5;
  const gridMin = Math.floor(minPrice * 0.8 * 10) / 10;
  const gridMax = Math.ceil(maxPrice * 1.2 * 10) / 10;
  const gridRange = gridMax - gridMin;
  const gridStep = Math.ceil((gridRange / 5) * 10) / 10;

  const chartOptions = {
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
  };

  // --- Portfolio Stats ---
  const portfolioValue = usd + coins * currentPrice;
  const portfolioChange = ((portfolioValue - 10000) / 10000) * 100;

  return (
    <div className="h-screen flex flex-col overflow-hidden p-8">
      <div className="flex items-center justify-between mb-6">
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

      <div
        style={{ display: "grid", gridTemplateColumns: "65% 35%", gap: "1.5rem" }}
        className="flex-1 min-h-0"
      >
        <div className="flex flex-col min-h-0 overflow-hidden">
          <Card title="BANANA COIN MARKET" padding="lg" className="h-full flex flex-col">
            <div className="flex-1 min-h-0">
              <Line data={chartData} options={chartOptions} />
            </div>
            <div className="mt-4 p-4 border-t-2 border-[var(--border)]">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-[var(--foreground)]">Current Price</div>
                  <div className="font-retro text-3xl text-[var(--primary)]">
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
                  <div className="text-sm text-[var(--foreground)]">Total Volume</div>
                  <div className="font-retro text-2xl text-[var(--accent)]">
                    {interactionsArr.length} trades
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
                <div className="text-sm text-[var(--foreground)]">US Dollars</div>
                <div className="font-retro text-2xl text-[var(--success)]">
                  ${usd.toFixed(2)}
                </div>
              </div>
              <div className="p-3 bg-[var(--background)] border-2 border-[var(--border)]">
                <div className="text-sm text-[var(--foreground)]">Banana Coins</div>
                <div className="font-retro text-2xl text-[var(--primary)]">
                  {coins.toFixed(2)} BC
                </div>
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
                onChange={(e) => setAmount(e.target.value)}
                fullWidth
                min="0"
                step="0.01"
              />
              <div className="text-xs text-[var(--foreground)] -mt-2">
                Cost: $
                {(parseFloat(amount || "0") * currentPrice).toFixed(4)} USD (@ $
                {currentPrice.toFixed(4)}/BC)
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

          <Card title={`BOTS (${bots.length})`} padding="lg">
            {bots.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-[var(--foreground)] mb-3">No bots yet</p>
                <p className="text-sm text-[var(--foreground)]">
                  Visit the Shops tab to buy trading bots
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {bots.map((bot: any) => {
                  const isActive = bot.isActive ?? false;
                  const botId = bot.botId ?? '';
                  const usdBalance = typeof bot.usdBalance === 'number' ? bot.usdBalance : 0;
                  const coinBalance = typeof bot.coinBalance === 'number' ? bot.coinBalance : 0;
                  const startingBalance = typeof bot.startingUsdBalance === 'number' ? bot.startingUsdBalance : 0;
                  const performance = startingBalance > 0 ? ((usdBalance + coinBalance * currentPrice - startingBalance) / startingBalance * 100) : 0;
                  
                  return (
                    <div
                      key={botId || Math.random()}
                      className={`p-3 border-2 transition-colors ${
                        isActive 
                          ? 'border-[var(--success)] bg-[var(--background)]' 
                          : 'border-[var(--border)] bg-[var(--background)] opacity-70'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-retro text-lg text-[var(--primary-light)]">
                          {bot.botName ?? "Bot"}
                        </div>
                        <Button
                          onClick={() => handleToggleBot(botId)}
                          variant={isActive ? "danger" : "success"}
                          size="sm"
                          disabled={togglingBot !== null}
                        >
                          {togglingBot === botId 
                            ? "..." 
                            : isActive 
                            ? "Stop" 
                            : "Start"}
                        </Button>
                      </div>
                      <div className="text-xs text-[var(--foreground)] space-y-1">
                        <div className="flex justify-between">
                          <span>Status:</span>
                          <span className={isActive ? "text-[var(--success)]" : "text-[var(--foreground)]"}>
                            {isActive ? "Active" : "Stopped"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>USD Balance:</span>
                          <span className="text-[var(--success)]">
                            ${usdBalance.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>BC Balance:</span>
                          <span className="text-[var(--primary)]">
                            {coinBalance.toFixed(2)} BC
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Performance:</span>
                          <span className={performance >= 0 ? "text-[var(--success)]" : "text-[var(--danger)]"}>
                            {performance >= 0 ? '+' : ''}{performance.toFixed(1)}%
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
    </div>
  );
}
