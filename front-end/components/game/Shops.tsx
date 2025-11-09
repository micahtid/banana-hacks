"use client";

import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { type Game, type User, buyMinion } from "@/utils/database_functions";
import { useState, useEffect, useRef } from "react";
import { useUser } from "@/providers/UserProvider";
import { TbAlertTriangle } from "react-icons/tb";

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
    id: "random",
    name: "Random Bot",
    description: "Makes random trades with varied probability and amounts",
    price: 300,
    strategy: "Random buy/sell decisions",
  },
  {
    id: "momentum",
    name: "Momentum Bot",
    description: "Follows market trends using moving averages to ride momentum",
    price: 800,
    strategy: "Buy on uptrends, sell on downtrends",
  },
  {
    id: "mean_reversion",
    name: "Mean Reversion Bot",
    description: "Buys when price is below average, sells when above average",
    price: 750,
    strategy: "Trade against extreme price movements",
  },
  {
    id: "market_maker",
    name: "Market Maker Bot",
    description: "Maintains balanced portfolio by rebalancing USD/BC ratio",
    price: 1200,
    strategy: "Keep 50/50 USD/BC balance",
  },
  {
    id: "hedger",
    name: "Hedger Bot",
    description: "Protects against volatility by hedging during market swings",
    price: 1000,
    strategy: "Reduce risk in volatile markets",
  },
];

const CUSTOM_MINION_PRICE = 1750; // More expensive than all premade minions

export default function Shops({ game, currentUser }: ShopsProps) {
  const { user } = useUser();
  const [customPrompt, setCustomPrompt] = useState("");
  const [buyingMinion, setBuyingMinion] = useState<string | null>(null);
  const [newsText, setNewsText] = useState<string>("NO NEWS");
  const [isEventActive, setIsEventActive] = useState<boolean>(false);
  const [previousEventTriggered, setPreviousEventTriggered] = useState<boolean>(false);
  const eventTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Event News Banner Logic
  useEffect(() => {
    // Clear any existing timer
    if (eventTimerRef.current) {
      clearTimeout(eventTimerRef.current);
      eventTimerRef.current = null;
    }

    // Reset previousEventTriggered when eventTriggered becomes false
    if (!game.eventTriggered && previousEventTriggered) {
      setPreviousEventTriggered(false);
      setNewsText("NO NEWS");
      setIsEventActive(false);
    }
    
    if (game.eventTriggered && !previousEventTriggered) {
      setPreviousEventTriggered(true);
      const newText = game.eventTitle || "MARKET EVENT";
      setNewsText(newText);
      setIsEventActive(true);

      // Return to "NO NEWS" after 30 seconds
      eventTimerRef.current = setTimeout(() => {
        setNewsText("NO NEWS");
        setIsEventActive(false);
        eventTimerRef.current = null;
      }, 30000);
    }

    // Cleanup on unmount
    return () => {
      if (eventTimerRef.current) {
        clearTimeout(eventTimerRef.current);
        eventTimerRef.current = null;
      }
    };
  }, [game.eventTriggered, previousEventTriggered, game.eventTitle]);

  // Ensure newsText always has a value (defensive check)
  useEffect(() => {
    if (!newsText || newsText.trim() === '') {
      setNewsText("NO NEWS");
    }
  }, [newsText]);

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
    <div>
      {/* Header with News Flash */}
      <div className="flex items-center gap-6 mb-6">
        <h2 className="font-retro text-4xl text-[var(--primary)] flex-shrink-0">
          MINION SHOP
        </h2>
        {/* News Carousel Banner - stretches between page name and balance */}
        <div className={`py-2 px-4 overflow-hidden relative flex items-center flex-1 min-w-0 ${isEventActive ? 'border-2 border-[var(--danger)] animate-flash-red rounded' : ''}`}>
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
          <div className="text-sm text-[var(--foreground)]">Your Balance</div>
          <div className="font-retro text-3xl text-[var(--success)]">
            ${currentUser.usd.toFixed(2)} USD
          </div>
        </div>
      </div>

      <div className="space-y-6">

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
    </div>
  );
}
