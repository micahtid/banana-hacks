"use client";

import { useUser } from "@/providers/UserProvider";
import { getRoom, startRoom, type Game } from "@/utils/database_functions";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import WaitingRoom from "@/components/game/WaitingRoom";
import GameDashboard from "@/components/game/GameDashboard";

export default function GamePage() {
  const { user } = useUser();
  const params = useParams();
  const router = useRouter();
  const gameId = params.gameId as string;
  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCountdown, setShowCountdown] = useState(false);
  const [countdownNumber, setCountdownNumber] = useState(3);
  const [wasStarted, setWasStarted] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);

  useEffect(() => {
    if (!gameId) return;

    let unsubscribe: (() => void) | null = null;

    const startPolling = () => {
      unsubscribe = getRoom(gameId, (gameData) => {
        if (gameData) {
          // Detect when game transitions from not started to started
          if (!wasStarted && gameData.isStarted) {
            setWasStarted(true);
            setShowCountdown(true);
            setCountdownNumber(3);
          }

          // Check if game has ended
          if (gameData.startTime && gameData.isStarted) {
            const now = new Date();
            let startTime: Date;

            if (
              typeof gameData.startTime === "object" &&
              gameData.startTime !== null &&
              "seconds" in gameData.startTime &&
              typeof (gameData.startTime as any).seconds === "number"
            ) {
              startTime = new Date((gameData.startTime as { seconds: number }).seconds * 1000);
            } else if (gameData.startTime instanceof Date) {
              startTime = gameData.startTime;
            } else {
              startTime = new Date(gameData.startTime as any);
            }

            const durationMinutes = typeof gameData.gameDuration === "number" ? gameData.gameDuration : gameData.durationMinutes || 0;
            const endTime = new Date(startTime.getTime() + durationMinutes * 60000);
            const diff = endTime.getTime() - now.getTime();

            // If game has ended, stop polling
            if (diff <= 0) {
              if (unsubscribe) {
                unsubscribe();
                unsubscribe = null;
              }
            }
          }

          setGame(gameData);
          setError("");
        } else {
          setError("Game not found");
        }
        setLoading(false);
      });
    };

    startPolling();

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [gameId, wasStarted]);

  // Countdown effect
  useEffect(() => {
    if (!showCountdown) return;

    if (countdownNumber === 0) {
      // Show "SPLIT!" for 1 second, then start fade out
      const timer = setTimeout(() => {
        setIsFadingOut(true);
        // Hide completely after fade animation (500ms)
        setTimeout(() => {
          setShowCountdown(false);
          setIsFadingOut(false);
        }, 500);
      }, 1000);
      return () => clearTimeout(timer);
    }

    const timer = setTimeout(() => {
      setCountdownNumber(countdownNumber - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [showCountdown, countdownNumber]);

  if (user === undefined || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="font-retro text-2xl text-[var(--primary)]">Loading...</p>
      </div>
    );
  }

  if (!user) {
    router.push("/");
    return null;
  }

  if (error || !game) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <Card className="max-w-md">
          <div className="text-center">
            <p className="font-retro text-2xl text-[var(--danger)] mb-4">
              {error || "Game not found"}
            </p>
            <Button onClick={() => router.push("/")} variant="primary">
              Return Home
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Check if user is in the game
  // Use players (primary) or users (backward compatibility)
  const playersList = game.players || game.users || [];
  
  console.log('[Game Page] Debug:', {
    firebaseUid: user.uid,
    playersCount: playersList.length,
    players: playersList.map(p => ({ 
      userId: (p as any).userId, 
      playerId: (p as any).playerId,
      userName: (p as any).userName || (p as any).playerName 
    }))
  });

  // Try to find user by userId (should match Firebase UID)
  const currentUser = playersList.find((u) => (u as any).userId === user.uid);
  
  if (!currentUser) {
    console.error('[Game Page] Current user not found in game', {
      firebaseUid: user.uid,
      availableUserIds: playersList.map(p => (p as any).userId)
    });
    
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <Card className="max-w-md">
          <div className="text-center">
            <p className="font-retro text-2xl text-[var(--danger)] mb-4">
              You are not in this game
            </p>
            <p className="text-sm text-[var(--foreground)] mb-4">
              Debug: Your ID: {user.uid}
            </p>
            <p className="text-sm text-[var(--foreground)] mb-4">
              Players in game: {playersList.length}
            </p>
            <Button onClick={() => router.push("/")} variant="primary">
              Return Home
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  console.log('[Game Page] Current user found:', {
    userId: (currentUser as any).userId,
    userName: (currentUser as any).userName,
    usd: (currentUser as any).usd,
    coins: (currentUser as any).coins
  });

  return (
    <div className="min-h-screen">
      {!game.isStarted ? (
        <WaitingRoom game={game} currentUser={currentUser as any} />
      ) : (
        <GameDashboard game={game} currentUser={currentUser as any} />
      )}

      {/* Countdown Overlay */}
      {showCountdown && (
        <div
          className={`fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 transition-opacity duration-500 ${
            isFadingOut ? 'opacity-0' : 'opacity-100'
          }`}
        >
          <div className="text-center">
            <div
              key={countdownNumber}
              className="font-retro text-9xl text-[var(--primary-light)] animate-bounce"
            >
              {countdownNumber === 0 ? "SPLIT!" : countdownNumber}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
