/**
 * Minion/Bot Constants
 *
 * Centralized configuration for all trading minions
 */

export interface PremadeMinion {
  id: string;
  name: string;
  description: string;
  price: number;
  strategy: string;
}

export const PREMADE_MINIONS: PremadeMinion[] = [
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

export const CUSTOM_MINION_PRICE = 1750;

/**
 * Bot price mapping for performance calculation and display
 * Includes both display names and backend type names for backward compatibility
 */
export const BOT_PRICES: { [key: string]: number } = {
  // Display names
  "Random Bot": 300,
  "Momentum Bot": 800,
  "Mean Reversion Bot": 750,
  "Market Maker Bot": 1200,
  "Hedger Bot": 1000,
  "Custom Minion": 1750,
  // Backend type names (for backward compatibility)
  "random": 300,
  "momentum": 800,
  "mean_reversion": 750,
  "market_maker": 1200,
  "hedger": 1000,
};

/**
 * Get display name for a minion
 * Handles both new minions (with proper display names) and old minions (with backend types)
 */
export function getMinionDisplayName(botName: string): string {
  // If it's already a display name (has spaces or starts with capital), return as-is
  if (botName.includes(' ') || /^[A-Z]/.test(botName)) {
    return botName;
  }

  // For old minions with backend types, convert to user-friendly format
  // e.g., "mean_reversion" → "Mean Reversion Bot"
  return botName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ') + ' Bot';
}
