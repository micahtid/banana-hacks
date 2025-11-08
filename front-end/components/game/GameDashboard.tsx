"use client";

import { type Game, type User } from "@/utils/database_functions";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import MainDashboard from "./MainDashboard";
import Shops from "./Shops";
import Transactions from "./Transactions";
import { TbChartLine, TbShoppingBag, TbList, TbDoorExit } from "react-icons/tb";

interface GameDashboardProps {
  game: Game;
  currentUser: User;
}

type Tab = "dashboard" | "shops" | "transactions";

export default function GameDashboard({
  game,
  currentUser,
}: GameDashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const router = useRouter();

  const tabs = [
    { id: "dashboard" as Tab, icon: TbChartLine },
    { id: "shops" as Tab, icon: TbShoppingBag },
    { id: "transactions" as Tab, icon: TbList },
  ];

  const handleLeaveGame = () => {
    router.push("/");
  };

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
          <MainDashboard game={game} currentUser={currentUser} />
        )}
        {activeTab === "shops" && (
          <div className="h-full overflow-y-auto p-8">
            <Shops game={game} currentUser={currentUser} />
          </div>
        )}
        {activeTab === "transactions" && (
          <div className="h-full overflow-y-auto p-8">
            <Transactions game={game} currentUser={currentUser} />
          </div>
        )}
      </main>
    </div>
  );
}
