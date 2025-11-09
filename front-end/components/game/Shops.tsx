"use client";

import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { type Game, type User, buyMinion } from "@/utils/database_functions";
import { useState, useEffect } from "react";
import { useUser } from "@/providers/UserProvider";

interface ShopsProps {
  game: Game;
  currentUser: User;
}

interface PremadeMinion {
  id: string;
  name: string;
  description: string;
  price: number;
  strategy: string;
}

const PREMADE_MINIONS: PremadeMinion[] = [
  {
    id: "hodler",
    name: "Mean Reversion Bot",
    description: "A patient minion that buys and holds for long-term gains",
    price: 500,
    strategy: "Buy low, hold forever",
  },
  {
    id: "scalper",
    name: "Momentum Bot",
    description: "Makes rapid small trades to capture quick profits",
    price: 750,
    strategy: "Fast trades, small margins",
  },
  {
    id: "swing",
    name: "Momentum Bot",
    description: "Identifies trends and trades on momentum swings",
    price: 1000,
    strategy: "Trend following",
  },
  {
    id: "arbitrage",
    name: "Market Maker Bot",
    description: "Exploits price differences for guaranteed profits",
    price: 1500,
    strategy: "Risk-free arbitrage",
  },
  {
    id: "dip",
    name: "Mean Reversion Bot",
    description: "Automatically buys during market dips",
    price: 600,
    strategy: "Buy the dip",
  },
  {
    id: "momentum",
    name: "Momentum Bot",
    description: "Rides strong upward momentum for maximum gains",
    price: 800,
    strategy: "Follow the momentum",
  },
];

const CUSTOM_MINION_PRICE = 1750; // More expensive than all premade minions

export default function Shops({ game, currentUser }: ShopsProps) {
  const { user } = useUser();
  const [customPrompt, setCustomPrompt] = useState("");
  const [buyingMinion, setBuyingMinion] = useState<string | null>(null);

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

  const handleBuyPremade = async (minion: PremadeMinion) => {
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

    if (currentUser.usd < minion.price) {
      console.warn(`[Shops] Insufficient USD: has $${currentUser.usd}, needs $${minion.price}`);
      return;
    }

    // Count existing bots of the same type to generate number
    const existingBots = currentUser.bots || [];
    const sameTypeBots = existingBots.filter((bot: any) =>
      bot.botName && bot.botName.startsWith(minion.name)
    );
    const botNumber = sameTypeBots.length + 1;
    const numberedBotName = `${minion.name} ${botNumber}`;

    setBuyingMinion(minion.id);
    try {
      console.log('[Shops] Purchasing minion:', {
        minionPrice: minion.price,
        userId: currentUser.userId,
        gameId: game.gameId,
        minionType: minion.id,
        botName: numberedBotName
      });

      await buyMinion(minion.price, currentUser.userId, game.gameId, minion.id, numberedBotName);
      console.log(`[Shops] ✅ Successfully purchased ${numberedBotName}!`);
    } catch (error) {
      console.error("[Shops] ❌ Failed to buy minion:", error);
    } finally {
      setBuyingMinion(null);
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

    if (currentUser.usd < CUSTOM_MINION_PRICE) {
      console.warn(`[Shops] Insufficient USD: has $${currentUser.usd}, needs $${CUSTOM_MINION_PRICE}`);
      return;
    }

    if (!customPrompt.trim()) {
      console.warn("[Shops] Custom minion prompt is empty");
      return;
    }

    // Count existing custom minions to generate number
    const existingBots = currentUser.bots || [];
    const customBots = existingBots.filter((bot: any) =>
      bot.botName && bot.botName.startsWith("Custom Minion")
    );
    const botNumber = customBots.length + 1;
    const numberedBotName = `Custom Minion ${botNumber}`;

    setBuyingMinion("custom");
    try {
      console.log('[Shops] Creating custom minion:', {
        minionPrice: CUSTOM_MINION_PRICE,
        userId: currentUser.userId,
        gameId: game.gameId,
        customPrompt,
        botName: numberedBotName
      });

      await buyMinion(CUSTOM_MINION_PRICE, currentUser.userId, game.gameId, "custom", numberedBotName, customPrompt);
      setCustomPrompt("");
      console.log(`[Shops] ✅ Successfully created ${numberedBotName}!`);
    } catch (error) {
      console.error("[Shops] ❌ Failed to buy custom minion:", error);
    } finally {
      setBuyingMinion(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="font-retro text-4xl text-[var(--primary-light)]">
          MINION SHOP
        </h2>
        <div className="text-right">
          <div className="text-sm text-[var(--foreground)]">Your Balance</div>
          <div className="font-retro text-3xl text-[var(--success)]">
            ${currentUser.usd.toFixed(2)} USD
          </div>
        </div>
      </div>

      {/* Custom Minion Section */}
      <Card title="CUSTOM MINION" padding="lg">
        <div className="max-w-md">
          {/* Custom Minion Card */}
          <div
            className={`
              p-5 border-2 transition-all
              ${currentUser.usd >= CUSTOM_MINION_PRICE ? "border-[var(--border)] hover:border-[var(--primary)]" : "border-[var(--border)] opacity-60"}
              bg-[var(--background)]
            `}
          >
            {/* Minion Header */}
            <div className="mb-3">
              <div className="font-retro text-xl text-[var(--primary-light)] mb-1">
                CUSTOM MINION
              </div>
              <div className="text-xs text-[var(--accent)] font-bold">
                AI-POWERED
              </div>
            </div>

            {/* Description */}
            <p className="text-sm text-[var(--foreground)] mb-3">
              Create a custom trading minion by describing its strategy
            </p>

            {/* Custom Prompt Input */}
            <div className="mb-4">
              <Input
                label="Minion Strategy"
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
                  ${CUSTOM_MINION_PRICE} USD
                </div>
              </div>
              <Button
                onClick={handleBuyCustom}
                variant={currentUser.usd >= CUSTOM_MINION_PRICE ? "primary" : "secondary"}
                size="sm"
                disabled={buyingMinion !== null || currentUser.usd < CUSTOM_MINION_PRICE || !customPrompt.trim()}
              >
                {buyingMinion === "custom"
                  ? "Creating..."
                  : currentUser.usd < CUSTOM_MINION_PRICE
                  ? "Can't Afford"
                  : "Create"}
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Prebuilt Minions Section */}
      <Card title="PREBUILT MINIONS" padding="lg">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {PREMADE_MINIONS.map((minion) => {
            const canAfford = currentUser.usd >= minion.price;
            const isOwned = currentUser.bots.some((b) => b.botName === minion.name);

            return (
              <div
                key={minion.id}
                className={`
                  p-5 border-2 transition-all
                  ${canAfford ? "border-[var(--border)] hover:border-[var(--primary)]" : "border-[var(--border)] opacity-60"}
                  ${isOwned ? "bg-[var(--border)]" : "bg-[var(--background)]"}
                `}
              >
                {/* Minion Header */}
                <div className="mb-3">
                  <div className="font-retro text-xl text-[var(--primary-light)] mb-1">
                    {minion.name}
                  </div>
                  {isOwned && (
                    <div className="text-xs text-[var(--success)] font-bold">
                      OWNED
                    </div>
                  )}
                </div>

                {/* Description */}
                <p className="text-sm text-[var(--foreground)] mb-3">
                  {minion.description}
                </p>

                {/* Strategy */}
                <div className="mb-4 p-3 bg-[var(--card-bg)] border border-[var(--border)]">
                  <div className="text-xs text-[var(--primary)] mb-1">
                    STRATEGY:
                  </div>
                  <div className="text-sm text-[var(--foreground)] font-mono">
                    {minion.strategy}
                  </div>
                </div>

                {/* Price and Buy Button */}
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs text-[var(--foreground)]">Price</div>
                    <div className="font-retro text-xl text-[var(--success)]">
                      ${minion.price} USD
                    </div>
                  </div>
                  <Button
                    onClick={() => handleBuyPremade(minion)}
                    variant={canAfford ? "success" : "secondary"}
                    size="sm"
                    disabled={buyingMinion !== null || !canAfford || isOwned}
                  >
                    {buyingMinion === minion.id
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
