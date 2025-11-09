"use client";

import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { type Game, type User, buyBot } from "@/utils/database_functions";
import { useState, useEffect } from "react";
import { useUser } from "@/providers/UserProvider";

interface ShopsProps {
  game: Game;
  currentUser: User;
}

interface PremadeBot {
  id: string;
  name: string;
  description: string;
  price: number;
  strategy: string;
}

const PREMADE_BOTS: PremadeBot[] = [
  {
    id: "hodler",
    name: "HODL Master",
    description: "A patient bot that buys and holds for long-term gains",
    price: 500,
    strategy: "Buy low, hold forever",
  },
  {
    id: "scalper",
    name: "Quick Scalper",
    description: "Makes rapid small trades to capture quick profits",
    price: 750,
    strategy: "Fast trades, small margins",
  },
  {
    id: "swing",
    name: "Swing Trader",
    description: "Identifies trends and trades on momentum swings",
    price: 1000,
    strategy: "Trend following",
  },
  {
    id: "arbitrage",
    name: "Arbitrage Pro",
    description: "Exploits price differences for guaranteed profits",
    price: 1500,
    strategy: "Risk-free arbitrage",
  },
  {
    id: "dip",
    name: "Dip Buyer",
    description: "Automatically buys during market dips",
    price: 600,
    strategy: "Buy the dip",
  },
  {
    id: "momentum",
    name: "Momentum Chaser",
    description: "Rides strong upward momentum for maximum gains",
    price: 800,
    strategy: "Follow the momentum",
  },
];

const CUSTOM_BOT_PRICE = 1750; // More expensive than all premade bots

export default function Shops({ game, currentUser }: ShopsProps) {
  const { user } = useUser();
  const [customPrompt, setCustomPrompt] = useState("");
  const [buyingBot, setBuyingBot] = useState<string | null>(null);

  // Debug: Log currentUser when component mounts
  useEffect(() => {
    console.log('[Shops] Component mounted with currentUser:', {
      currentUser,
      hasUserId: 'userId' in currentUser,
      userId: currentUser.userId,
      userIdType: typeof currentUser.userId,
      userName: currentUser.userName,
      usd: currentUser.usd,
      allKeys: Object.keys(currentUser)
    });
    console.log('[Shops] Game:', {
      gameId: game.gameId,
      hasGameId: 'gameId' in game,
      gameIdType: typeof game.gameId
    });
  }, [currentUser, game]);

  const handleBuyPremade = async (bot: PremadeBot) => {
    if (!user) {
      console.error('[Shops] User not logged in');
      return;
    }

    if (!currentUser.userId) {
      console.error('[Shops] User ID not available');
      return;
    }

    if (!game.gameId) {
      console.error('[Shops] Game ID not available');
      return;
    }

    if (currentUser.usd < bot.price) {
      console.warn(`[Shops] Insufficient USD: has $${currentUser.usd}, needs $${bot.price}`);
      return;
    }

    setBuyingBot(bot.id);
    try {
      console.log('[Shops] Purchasing bot:', { 
        botPrice: bot.price, 
        userId: currentUser.userId, 
        gameId: game.gameId, 
        botType: bot.id 
      });
      
      await buyBot(bot.price, currentUser.userId, game.gameId, bot.id, bot.name);
      console.log(`[Shops] ✅ Successfully purchased ${bot.name}!`);
    } catch (error) {
      console.error("[Shops] ❌ Failed to buy bot:", error);
    } finally {
      setBuyingBot(null);
    }
  };

  const handleBuyCustom = async () => {
    if (!user) {
      console.error('[Shops] User not logged in');
      return;
    }

    if (!currentUser.userId) {
      console.error('[Shops] User ID not available');
      return;
    }

    if (!game.gameId) {
      console.error('[Shops] Game ID not available');
      return;
    }

    if (currentUser.usd < CUSTOM_BOT_PRICE) {
      console.warn(`[Shops] Insufficient USD: has $${currentUser.usd}, needs $${CUSTOM_BOT_PRICE}`);
      return;
    }

    if (!customPrompt.trim()) {
      console.warn("[Shops] Custom bot prompt is empty");
      return;
    }

    setBuyingBot("custom");
    try {
      console.log('[Shops] Creating custom bot:', { 
        botPrice: CUSTOM_BOT_PRICE, 
        userId: currentUser.userId, 
        gameId: game.gameId, 
        customPrompt 
      });
      
      await buyBot(CUSTOM_BOT_PRICE, currentUser.userId, game.gameId, "custom", customPrompt);
      setCustomPrompt("");
      console.log("[Shops] ✅ Successfully created custom bot!");
    } catch (error) {
      console.error("[Shops] ❌ Failed to buy custom bot:", error);
    } finally {
      setBuyingBot(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="font-retro text-4xl text-[var(--primary-light)]">
          BOT SHOP
        </h2>
        <div className="text-right">
          <div className="text-sm text-[var(--foreground)]">Your Balance</div>
          <div className="font-retro text-3xl text-[var(--success)]">
            ${currentUser.usd.toFixed(2)} USD
          </div>
        </div>
      </div>

      {/* Custom Bot Section */}
      <Card title="CUSTOM BOT" padding="lg">
        <div className="max-w-md">
          {/* Custom Bot Card */}
          <div
            className={`
              p-5 border-2 transition-all
              ${currentUser.usd >= CUSTOM_BOT_PRICE ? "border-[var(--border)] hover:border-[var(--primary)]" : "border-[var(--border)] opacity-60"}
              bg-[var(--background)]
            `}
          >
            {/* Bot Header */}
            <div className="mb-3">
              <div className="font-retro text-xl text-[var(--primary-light)] mb-1">
                CUSTOM BOT
              </div>
              <div className="text-xs text-[var(--accent)] font-bold">
                AI-POWERED
              </div>
            </div>

            {/* Description */}
            <p className="text-sm text-[var(--foreground)] mb-3">
              Create a custom trading bot by describing its strategy
            </p>

            {/* Custom Prompt Input */}
            <div className="mb-4">
              <Input
                label="Bot Strategy"
                placeholder="e.g., 'Buy when price drops 5%'"
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                fullWidth
              />
            </div>

            {/* Price and Buy Button */}
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-xs text-[var(--foreground)]">Price</div>
                <div className="font-retro text-xl text-[var(--success)]">
                  ${CUSTOM_BOT_PRICE} USD
                </div>
              </div>
              <Button
                onClick={handleBuyCustom}
                variant={currentUser.usd >= CUSTOM_BOT_PRICE ? "primary" : "secondary"}
                size="sm"
                disabled={buyingBot !== null || currentUser.usd < CUSTOM_BOT_PRICE || !customPrompt.trim()}
              >
                {buyingBot === "custom"
                  ? "Creating..."
                  : currentUser.usd < CUSTOM_BOT_PRICE
                  ? "Can't Afford"
                  : "Create"}
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Prebuilt Bots Section */}
      <Card title="PREBUILT BOTS" padding="lg">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {PREMADE_BOTS.map((bot) => {
            const canAfford = currentUser.usd >= bot.price;
            const isOwned = currentUser.bots.some((b) => b.botName === bot.name);

            return (
              <div
                key={bot.id}
                className={`
                  p-5 border-2 transition-all
                  ${canAfford ? "border-[var(--border)] hover:border-[var(--primary)]" : "border-[var(--border)] opacity-60"}
                  ${isOwned ? "bg-[var(--border)]" : "bg-[var(--background)]"}
                `}
              >
                {/* Bot Header */}
                <div className="mb-3">
                  <div className="font-retro text-xl text-[var(--primary-light)] mb-1">
                    {bot.name}
                  </div>
                  {isOwned && (
                    <div className="text-xs text-[var(--success)] font-bold">
                      OWNED
                    </div>
                  )}
                </div>

                {/* Description */}
                <p className="text-sm text-[var(--foreground)] mb-3">
                  {bot.description}
                </p>

                {/* Strategy */}
                <div className="mb-4 p-3 bg-[var(--card-bg)] border border-[var(--border)]">
                  <div className="text-xs text-[var(--primary)] mb-1">
                    STRATEGY:
                  </div>
                  <div className="text-sm text-[var(--foreground)] font-mono">
                    {bot.strategy}
                  </div>
                </div>

                {/* Price and Buy Button */}
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs text-[var(--foreground)]">Price</div>
                    <div className="font-retro text-xl text-[var(--success)]">
                      ${bot.price} USD
                    </div>
                  </div>
                  <Button
                    onClick={() => handleBuyPremade(bot)}
                    variant={canAfford ? "success" : "secondary"}
                    size="sm"
                    disabled={buyingBot !== null || !canAfford || isOwned}
                  >
                    {buyingBot === bot.id
                      ? "Buying..."
                      : isOwned
                      ? "Owned"
                      : !canAfford
                      ? "Can't Afford"
                      : "Buy"}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

    </div>
  );
}
