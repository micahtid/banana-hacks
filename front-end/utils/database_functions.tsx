import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithRedirect, signInWithPopup } from "firebase/auth";
import { getFirestore, collection, addDoc, doc, getDoc, updateDoc, onSnapshot, query, where, Timestamp } from "firebase/firestore";

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

export const getFireStore = (alreadyInit: boolean) => {
  if (!alreadyInit) {
    const app = initializeFirebase();
  }
  const firestore = getFirestore();
  return firestore;
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
  interactions: Interaction[];
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
  const firestore = getFireStore(true);

  const newGame: Omit<Game, 'gameId'> = {
    isStarted: false,
    isEnded: false,
    users: [
      {
        userId: creatorId,
        userName: creatorName,
        bots: [],
        coins: 0,
        usd: 10000, // Starting USD
        lastInteractionV: 0,
        lastInteractionT: new Date(),
      },
    ],
    coin: [100], // Starting coin price
    interactions: [],
    eventTimer: new Date(),
    startTime: null,
    endTime: null,
    gameDuration,
    maxPlayers,
    creatorId,
  };

  const docRef = await addDoc(collection(firestore, 'games'), newGame);
  return docRef.id;
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
  const firestore = getFireStore(true);
  const gameRef = doc(firestore, 'games', gameId);
  const gameSnap = await getDoc(gameRef);

  if (!gameSnap.exists()) {
    throw new Error('Game not found');
  }

  const gameData = gameSnap.data() as Game;

  if (gameData.isStarted) {
    throw new Error('Game has already started');
  }

  if (gameData.users.length >= gameData.maxPlayers) {
    throw new Error('Game is full');
  }

  // Check if user already in game
  if (gameData.users.some((u) => u.userId === userId)) {
    throw new Error('User already in game');
  }

  const newUser: User = {
    userId,
    userName,
    bots: [],
    coins: 0,
    usd: 10000,
    lastInteractionV: 0,
    lastInteractionT: new Date(),
  };

  await updateDoc(gameRef, {
    users: [...gameData.users, newUser],
  });
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
  const firestore = getFireStore(true);
  const gameRef = doc(firestore, 'games', gameId);

  return onSnapshot(gameRef, (docSnap) => {
    if (docSnap.exists()) {
      const data = docSnap.data();
      onUpdate({ ...data, gameId: docSnap.id } as Game);
    } else {
      onUpdate(null);
    }
  });
};

/**
 * Start the game (only creator can call this)
 * @param gameId - Game ID
 */
export const startRoom = async (gameId: string): Promise<void> => {
  const firestore = getFireStore(true);
  const gameRef = doc(firestore, 'games', gameId);

  const startTime = new Date();

  await updateDoc(gameRef, {
    isStarted: true,
    startTime: startTime,
    eventTimer: startTime,
  });

  // TO UPDATE: Call backend startGame(gameId) here
  // This will initialize the game state and start the market simulation
};

/**
 * End the game (called when game duration is reached)
 * @param gameId - Game ID
 */
export const endRoom = async (gameId: string): Promise<void> => {
  const firestore = getFireStore(true);
  const gameRef = doc(firestore, 'games', gameId);

  const endTime = new Date();

  await updateDoc(gameRef, {
    isEnded: true,
    endTime: endTime,
  });

  // TO UPDATE: Call backend to finalize game results and calculate winners
};

// ============================================
// GAME ACTION FUNCTIONS (TO BE IMPLEMENTED WITH BACKEND)
// ============================================

/**
 * Buy banana coins
 * TO UPDATE: This will call the backend buy(userId, numBC, gameId)
 */
export const buyCoins = async (
  userId: string,
  numBC: number,
  gameId: string
): Promise<void> => {
  // TO UPDATE: Call backend API
  // await fetch('/api/buy', { method: 'POST', body: JSON.stringify({ userId, numBC, gameId }) })
  console.log('TO UPDATE: Implement backend call for buyCoins', { userId, numBC, gameId });
};

/**
 * Sell banana coins
 * TO UPDATE: This will call the backend sell(userId, numBC, gameId)
 */
export const sellCoins = async (
  userId: string,
  numBC: number,
  gameId: string
): Promise<void> => {
  // TO UPDATE: Call backend API
  // await fetch('/api/sell', { method: 'POST', body: JSON.stringify({ userId, numBC, gameId }) })
  console.log('TO UPDATE: Implement backend call for sellCoins', { userId, numBC, gameId });
};

/**
 * Buy a bot
 * TO UPDATE: This will call the backend buyBot(botPriceBC, userId)
 */
export const buyBot = async (
  botPriceBC: number,
  userId: string,
  gameId: string,
  botType: 'premade' | 'custom',
  customPrompt?: string
): Promise<void> => {
  // TO UPDATE: Call backend API
  // await fetch('/api/buyBot', { method: 'POST', body: JSON.stringify({ botPriceBC, userId, gameId, botType, customPrompt }) })
  console.log('TO UPDATE: Implement backend call for buyBot', { botPriceBC, userId, gameId, botType, customPrompt });
};

/**
 * Toggle bot active/inactive
 * TO UPDATE: This will call the backend toggleBot(botId)
 */
export const toggleBot = async (botId: string): Promise<void> => {
  // TO UPDATE: Call backend API
  // await fetch('/api/toggleBot', { method: 'POST', body: JSON.stringify({ botId }) })
  console.log('TO UPDATE: Implement backend call for toggleBot', { botId });
};