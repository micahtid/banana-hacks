import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

// initializing firebase: auth and login
// sign in and sign out functions

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
}


export const signIn = () => {
  const auth = getUserAuth(false);
  const provider = new GoogleAuthProvider();
//   signInWithRedirect(auth, provider);
  signInWithPopup(auth, provider);
}

export const signOut = () => {
  const auth = getUserAuth(false);
  auth.signOut();
}

// ============================================
// GAME FUNCTIONS
// ============================================

export interface Bot {
  botId: string;
  botName: string;
}

export interface User {
  userId: string;
  userName: string;
  bots: Bot[];
  coins: number;
  usd: number;
  lastInteractionV: number;
  lastInteractionT: Date;
}

export interface Interaction {
  name: string;
  type: string;
  value: number;
}

export interface Game {
  gameId: string;
  isStarted: boolean;
  isEnded: boolean;
  users: User[];
  coin: number[];
  interactions: number; // Count of total trades
  eventTimer: Date;
  startTime: Date | null;
  endTime: Date | null;
  gameDuration: number;
  maxPlayers: number;
  creatorId: string;
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
      console.error('Error fetching game:', error);
      onUpdate(null);
    }
  };

  // Initial fetch
  fetchGame();

  // Poll every 2 seconds for updates
  intervalId = setInterval(fetchGame, 2000);

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

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to buy coins');
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

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to sell coins');
  }
};

/**
 * Buy a bot
 */
export const buyBot = async (
  botPriceBC: number,
  userId: string,
  gameId: string,
  botType: 'premade' | 'custom',
  customPrompt?: string
): Promise<void> => {
  const response = await fetch('/api/bot/buy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gameId, userId, botType, cost: botPriceBC, customPrompt }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to buy bot');
  }
};

/**
 * Toggle bot active/inactive
 */
export const toggleBot = async (
  botId: string,
  userId: string,
  gameId: string
): Promise<void> => {
  const response = await fetch('/api/bot/toggle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gameId, userId, botId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to toggle bot');
  }
};