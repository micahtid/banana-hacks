"use client";

import { type Game, type User, type LeaderboardEntry, getLeaderboard } from "@/utils/database_functions";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import MainDashboard from "./MainDashboard";
import Shops from "./Shops";
import Transactions from "./Transactions";
import { TbChartLine, TbShoppingBag, TbList, TbDoorExit } from "react-icons/tb";
import { FaTrophy, FaMedal, FaAward } from "react-icons/fa";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";

interface GameDashboardProps {
  game: Game;
  currentUser: User;
}

type Tab = "dashboard" | "shops" | "transactions";

// End Game Screen Component
function EndGameScreen({ game, currentUser }: GameDashboardProps) {
  const router = useRouter();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const calculateFinalLeaderboard = async () => {
      try {
        const data = await getLeaderboard(game.gameId ?? "");
        setLeaderboard(data || []);
      } catch (error) {
        console.error('Failed to fetch final leaderboard:', error);
      } finally {
        setLoading(false);
      }
    };

    calculateFinalLeaderboard();
  }, [game.gameId]);

  const handleReturnHome = () => {
    router.push("/");
  };

  const currentUserRank = leaderboard.findIndex(entry => entry.userId === currentUser.userId) + 1;
  const currentUserEntry = leaderboard.find(entry => entry.userId === currentUser.userId);

  const playersList = game.players || game.users || [];
  const totalPlayers = playersList.length;
  const finalPrice = game.coinHistory && game.coinHistory.length > 0 
    ? game.coinHistory[game.coinHistory.length - 1] 
    : 1.0;
  const totalTrades = Array.isArray(game.interactions) ? game.interactions.length : 0;

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-[var(--background)]">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="font-retro text-6xl text-[var(--primary)] mb-4">
            GAME OVER!
          </h1>
          <p className="font-retro text-2xl text-[var(--primary-dark)]">
            Time's up! Here's how everyone did.
          </p>
        </div>

        {currentUserEntry && currentUserRank > 3 && (
          <Card className="mb-6 bg-[var(--card-bg)] border-2 border-[var(--border)]">
            <div className="text-center py-4">
              <div className="font-retro text-3xl text-[var(--primary-dark)] mb-2">
                YOUR FINAL RANK
              </div>
              <div className="flex items-center justify-center gap-4 mb-4">
                <div className="font-retro text-7xl text-[var(--primary-dark)]">
                  #{currentUserRank}
                </div>
              </div>
              <div className="font-retro text-4xl text-[var(--primary-dark)] mb-2">
                ${currentUserEntry.wealth.toFixed(2)}
              </div>
              <div className="text-lg text-[var(--primary-dark)]">
                ${currentUserEntry.usdBalance.toFixed(2)} USD + {currentUserEntry.coinBalance.toFixed(2)} BC
              </div>
            </div>
          </Card>
        )}

        <Card title="FINAL LEADERBOARD - TOP 3" padding="lg" className="mb-6">
          {loading ? (
            <div className="text-center py-12">
              <p className="text-[var(--primary)] text-lg">Loading final results...</p>
            </div>
          ) : leaderboard.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-[var(--primary)] text-lg">No players found</p>
            </div>
          ) : (
            <div className="space-y-0">
              {leaderboard.slice(0, 3).map((entry, index) => {
                const isCurrentUser = entry.userId === currentUser.userId;

                return (
                  <div
                    key={entry.userId}
                    className={`py-5 px-4 border-b border-[var(--border)] flex items-center justify-between ${
                      isCurrentUser ? "bg-[var(--card-bg)]" : ""
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="min-w-[3rem] flex items-center justify-center">
                        {index === 0 && <FaTrophy className="text-3xl text-yellow-300" />}
                        {index === 1 && <FaMedal className="text-3xl text-gray-300" />}
                        {index === 2 && <FaAward className="text-3xl text-amber-400" />}
                      </div>
                      <div>
                        <div className="font-retro text-xl text-[var(--primary-dark)]">
                          {entry.userName}
                          {isCurrentUser && " (You)"}
                        </div>
                        <div className="text-sm text-[var(--primary)]">
                          ${entry.usdBalance.toFixed(2)} + {entry.coinBalance.toFixed(2)} BC
                        </div>
                      </div>
                    </div>
                    <div className="font-retro text-2xl text-[var(--primary-dark)]">
                      ${entry.wealth.toFixed(2)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card padding="lg">
            <div className="text-center">
              <div className="text-sm text-[var(--primary)] mb-2">TOTAL PLAYERS</div>
              <div className="font-retro text-4xl text-[var(--primary-dark)]">
                {totalPlayers}
              </div>
            </div>
          </Card>
          <Card padding="lg">
            <div className="text-center">
              <div className="text-sm text-[var(--primary)] mb-2">FINAL PRICE</div>
              <div className="font-retro text-4xl text-[var(--primary-dark)]">
                ${finalPrice.toFixed(4)}
              </div>
            </div>
          </Card>
          <Card padding="lg">
            <div className="text-center">
              <div className="text-sm text-[var(--primary)] mb-2">TOTAL TRADES</div>
              <div className="font-retro text-4xl text-[var(--primary-dark)]">
                {totalTrades}
              </div>
            </div>
          </Card>
        </div>

        <div className="text-left">
          <Button
            onClick={handleReturnHome}
            variant="primary"
            size="lg"
            className="px-12 py-4 text-2xl"
          >
            RETURN TO LOBBY
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function GameDashboard({
  game,
  currentUser,
}: GameDashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const router = useRouter();
  const [isGameEnded, setIsGameEnded] = useState(false);

  // Check if game has ended
  useEffect(() => {
    if (!game.startTime || !game.isStarted) return;

    const checkGameEnd = () => {
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

      const durationMinutes = typeof game.gameDuration === "number" ? game.gameDuration : game.durationMinutes || 0;
      const endTime = new Date(startTime.getTime() + durationMinutes * 60000);
      const diff = endTime.getTime() - now.getTime();

      if (diff <= 0) {
        setIsGameEnded(true);
      }
    };

    checkGameEnd();
    const interval = setInterval(checkGameEnd, 1000);
    return () => clearInterval(interval);
  }, [game.startTime, game.gameDuration, game.durationMinutes, game.isStarted]);

  const tabs = [
    { id: "dashboard" as Tab, icon: TbChartLine },
    { id: "shops" as Tab, icon: TbShoppingBag },
    { id: "transactions" as Tab, icon: TbList },
  ];

  const handleLeaveGame = () => {
    router.push("/");
  };

  // Show end game screen if game has ended
  if (isGameEnded) {
    return <EndGameScreen game={game} currentUser={currentUser} />;
  }

  return (
    <div className="flex h-screen">
      {/* Vertical Navigation Bar */}
      <nav className="w-16 bg-[var(--card-bg)] border-r-2 border-[var(--border)] flex flex-col p-2 items-center">
        {/* Logo/Title */}
        <div className="mb-4 py-2">
          <h1 className="font-retro text-2xl text-[var(--primary-light)] text-center">
            BC
          </h1>
        </div>

        {/* Navigation Items */}
        <div className="flex flex-col gap-2 flex-1 items-center">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  w-10 h-10 border-2 transition-all flex items-center justify-center
                  ${
                    activeTab === tab.id
                      ? "bg-[var(--primary)] border-[var(--primary-light)] text-[var(--background)]"
                      : "bg-transparent border-[var(--border)] text-[var(--foreground)] hover:border-[var(--primary)]"
                  }
                `}
              >
                <Icon size={20} />
              </button>
            );
          })}
        </div>

        {/* Leave Game Button */}
        <button
          onClick={handleLeaveGame}
          className="w-10 h-10 border-2 border-[var(--danger)] bg-transparent text-[var(--danger)] hover:bg-[var(--danger)] hover:text-white transition-all flex items-center justify-center"
          title="Leave Game"
        >
          <TbDoorExit size={20} />
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">
        {activeTab === "dashboard" && (
          <div className="h-full overflow-hidden px-8 pt-6">
            <MainDashboard game={game} currentUser={currentUser} />
          </div>
        )}
        {activeTab === "shops" && (
          <div className="h-full overflow-y-auto px-8 pt-6">
            <Shops game={game} currentUser={currentUser} />
          </div>
        )}
        {activeTab === "transactions" && (
          <div className="h-full overflow-y-auto px-8 pt-6">
            <Transactions game={game} currentUser={currentUser} />
          </div>
        )}
      </main>
    </div>
  );
}
