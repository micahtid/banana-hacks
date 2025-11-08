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

  useEffect(() => {
    if (!gameId) return;

    const unsubscribe = getRoom(gameId, (gameData) => {
      if (gameData) {
        setGame(gameData);
        setError("");
      } else {
        setError("Game not found");
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, [gameId]);

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
  const currentUser = game.users.find((u) => u.userId === user.uid);
  if (!currentUser) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <Card className="max-w-md">
          <div className="text-center">
            <p className="font-retro text-2xl text-[var(--danger)] mb-4">
              You are not in this game
            </p>
            <Button onClick={() => router.push("/")} variant="primary">
              Return Home
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {!game.isStarted ? (
        <WaitingRoom game={game} currentUser={currentUser} />
      ) : (
        <GameDashboard game={game} currentUser={currentUser} />
      )}
    </div>
  );
}
