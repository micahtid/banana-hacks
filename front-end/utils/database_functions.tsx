/**
 * Database Functions
 *
 * This file contains all Firebase authentication and game-related API functions.
 * Note: Firebase config is embedded for simplicity. For production apps,
 * consider moving sensitive config to environment variables.
 */

import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

/* ============================================
   FIREBASE INITIALIZATION
   ============================================ */

export const initializeFirebase = () => {
  const firebaseConfig = {
    apiKey: "AIzaSyBcUuGzuZtK4IMpA34Mn7rO4yREJOoyA3A",
    authDomain: "corn-hacks.firebaseapp.com",
    projectId: "corn-hacks",
    storageBucket: "corn-hacks.firebasestorage.app",
    messagingSenderId: "837856312087",
    appId: "1:837856312087:web:b8758c25758e0f9a671552",
    measurementId: "G-B7QWF5JHVL"
  };

  const app = initializeApp(firebaseConfig);
  return app;
}

export const getUserAuth = (alreadyInit: boolean) => {
  if (!alreadyInit) {
    const app = initializeFirebase();
  }
  const auth = getAuth();
  return auth;
};

export const signIn = () => {
  const auth = getUserAuth(false);
  const provider = new GoogleAuthProvider();
  signInWithPopup(auth, provider);
};

export const signOut = () => {
  const auth = getUserAuth(false);
  auth.signOut();
};

/* ============================================
   TYPE DEFINITIONS
   ============================================ */

export interface Bot {
  botId: string;
  botName: string;
  coinBalance: number;
  isActive: boolean;
}

export interface LeaderboardEntry {
  userId: string;
  userName: string;
  usdBalance: number;
  coinBalance: number;
  wealth: number;
}

export interface Player {
  playerId: string;
  playerName: string;
  coinBalance: number;
  usdBalance: number;
  lastInteractionValue: number;
  lastInteractionTime: Date;
  bots: Bot[];
}

// Alias for backward compatibility
export interface User extends Player {
  userId: string;
  userName: string;
  coins: number;
  usd: number;
  lastInteractionV: number;
  lastInteractionT: Date;
}

export interface Interaction {
  // New fields (added for transaction history)
  name?: string;              // Actor name (user or bot)
  type?: string;              // 'buy' or 'sell'
  value?: number;             // Amount in cents
  
  // Legacy fields
  interactionName: string;
  interactionDescription: string;
}

export interface Game {
  gameId: string;
  isStarted: boolean;
  durationMinutes: number;
  maxPlayers: number;
  eventTime: Date;
  eventTitle?: string;
  eventTriggered?: boolean;

  players: Player[];

  coinHistory: number[];
  totalCoin: number;
  totalUsd: number;

  interactions: Interaction[];

  // Additional fields for backward compatibility
  isEnded?: boolean;
  startTime?: Date | null;
  endTime?: Date | null;
  creatorId?: string;

  // Alias for backward compatibility
  users?: Player[];
  coin?: number[];
  gameDuration?: number;
  eventTimer?: Date;
}

/**
 * Create a new game room
 * @param creatorId - User ID of the creator
 * @param creatorName - Display name of the creator
 * @param gameDuration - Duration of the game in minutes
 * @param maxPlayers - Maximum number of players
 * @returns Game ID
 */
export const createRoom = async (
  creatorId: string,
  creatorName: string,
  gameDuration: number,
  maxPlayers: number
): Promise<string> => {
  const response = await fetch('/api/game/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      userId: creatorId,
      userName: creatorName,
      duration: gameDuration,
      maxPlayers,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to create room');
  }

  const data = await response.json();
  return data.gameId;
};

/**
 * Join an existing game room
 * @param gameId - Game ID to join
 * @param userId - User ID
 * @param userName - Display name
 */
export const joinRoom = async (
  gameId: string,
  userId: string,
  userName: string
): Promise<void> => {
  const response = await fetch('/api/game/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gameId, userId, userName }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to join room');
  }
};

/**
 * Get real-time updates for a game room
 * @param gameId - Game ID
 * @param onUpdate - Callback when game data updates
 * @returns Unsubscribe function
 */
export const getRoom = (
  gameId: string,
  onUpdate: (game: Game | null) => void
) => {
  let intervalId: NodeJS.Timeout;

  const fetchGame = async () => {
    try {
      const response = await fetch(`/api/game/${gameId}`);
      if (response.ok) {
        const data = await response.json();
        onUpdate(data.game);
      } else {
        onUpdate(null);
      }
    } catch (error) {
      onUpdate(null);
    }
  };

  // Initial fetch
  fetchGame();

  // Poll every 1 second to match backend market update rate
  intervalId = setInterval(fetchGame, 1000);

  // Return unsubscribe function
  return () => clearInterval(intervalId);
};

/**
 * Start the game (only creator can call this)
 * @param gameId - Game ID
 * @param userId - User ID (must be creator)
 */
export const startRoom = async (gameId: string, userId: string): Promise<void> => {
  const response = await fetch('/api/game/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gameId, userId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to start room');
  }
};

/**
 * End the game (called when game duration is reached)
 * @param gameId - Game ID
 */
export const endRoom = async (gameId: string): Promise<void> => {
  const response = await fetch('/api/game/end', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gameId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to end room');
  }
};

// ============================================
// GAME ACTION FUNCTIONS (TO BE IMPLEMENTED WITH BACKEND)
// ============================================

/**
 * Buy banana coins
 */
export const buyCoins = async (
  userId: string,
  numBC: number,
  gameId: string
): Promise<void> => {
  const response = await fetch('/api/game/buy-coins', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gameId, userId, amount: numBC }),
  });

  const data = await response.json();

  // Check for HTTP errors
  if (!response.ok) {
    throw new Error(data.error || 'Failed to buy coins');
  }

  // Check for success: false (backend returned 200 but transaction failed)
  if (data.success === false) {
    throw new Error(data.error || data.message || 'Transaction failed');
  }
};

/**
 * Sell banana coins
 */
export const sellCoins = async (
  userId: string,
  numBC: number,
  gameId: string
): Promise<void> => {
  const response = await fetch('/api/game/sell-coins', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gameId, userId, amount: numBC }),
  });

  const data = await response.json();

  // Check for HTTP errors
  if (!response.ok) {
    throw new Error(data.error || 'Failed to sell coins');
  }

  // Check for success: false (backend returned 200 but transaction failed)
  if (data.success === false) {
    throw new Error(data.error || data.message || 'Transaction failed');
  }
};

/**
 * Buy a minion
 */
export const buyMinion = async (
  minionPrice: number,
  userId: string,
  gameId: string,
  minionType: string,
  botName?: string,
  customPrompt?: string
): Promise<void> => {
  // Validate parameters
  if (!userId || userId === 'undefined' || userId === 'null') {
    throw new Error(`userId is required but was not provided (received: ${userId})`);
  }

  if (!gameId || gameId === 'undefined' || gameId === 'null') {
    throw new Error(`gameId is required but was not provided (received: ${gameId})`);
  }

  if (!minionType || minionType === 'undefined' || minionType === 'null') {
    throw new Error(`minionType is required but was not provided (received: ${minionType})`);
  }

  if (minionPrice === undefined || minionPrice === null || minionPrice <= 0) {
    throw new Error(`Invalid minionPrice: ${minionPrice}`);
  }

  const requestBody = {
    gameId,
    userId,
    botType: minionType,
    botName: botName,
    cost: minionPrice,
    customPrompt
  };

  try {
    const response = await fetch('/api/bot/buy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        throw new Error(`Minion purchase failed with status ${response.status}`);
      }

      // Handle Pydantic validation errors (FastAPI format)
      if (errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => {
            const field = err.loc ? err.loc.join('.') : 'unknown';
            const msg = err.msg || 'validation error';
            return `${field}: ${msg}`;
          }).join(', ');
          throw new Error(`Validation error: ${errorMessages}`);
        } else if (typeof errorData.detail === 'string') {
          throw new Error(errorData.detail);
        }
      }

      throw new Error(errorData.error || `Failed to buy minion (status ${response.status})`);
    }
  } catch (error) {
    throw error;
  }
};

/**
 * Toggle minion active/inactive
 */
export const toggleMinion = async (
  minionId: string,
  userId: string,
  gameId: string
): Promise<void> => {
  const response = await fetch('/api/bot/toggle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gameId, userId, botId: minionId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to toggle minion');
  }
};

/**
 * Get leaderboard for a game
 */
export const getLeaderboard = async (gameId: string): Promise<LeaderboardEntry[]> => {
  const response = await fetch(`/api/game/leaderboard/${gameId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch leaderboard');
  }

  const data = await response.json();
  return data.leaderboard || [];
};