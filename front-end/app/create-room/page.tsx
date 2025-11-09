"use client";

import { useUser } from "@/providers/UserProvider";
import { createRoom } from "@/utils/database_functions";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Card } from "@/components/Card";
import { useState, Suspense } from "react";
import { useRouter } from "next/navigation";

function CreateRoomContent() {
  const { user } = useUser();
  const router = useRouter();
  const [gameDuration, setGameDuration] = useState("30");
  const [maxPlayers, setMaxPlayers] = useState("4");
  const [userName, setUserName] = useState("");
  const [error, setError] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateRoom = async () => {
    if (!user) {
      setError("Please login first");
      router.push("/");
      return;
    }

    if (!userName.trim()) {
      setError("Please enter your name");
      return;
    }

    const duration = parseInt(gameDuration);
    const players = parseInt(maxPlayers);

    if (isNaN(duration) || duration < 5 || duration > 120) {
      setError("Game duration must be between 5 and 120 minutes");
      return;
    }

    if (isNaN(players) || players < 2 || players > 10) {
      setError("Number of players must be between 2 and 10");
      return;
    }

    setIsCreating(true);
    setError("");

    try {
      const gameId = await createRoom(user.uid, userName, duration, players);
      router.push(`/game/${gameId}`);
    } catch (err: any) {
      setError(err.message || "Failed to create room");
      setIsCreating(false);
    }
  };

  if (user === undefined) {
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

  return (
    <div className="flex min-h-screen items-center justify-center p-8 bg-[var(--background)]">
      <div className="flex w-full max-w-md flex-col gap-6">
        {/* Title */}
        <div className="text-center">
          <h1 className="font-retro text-5xl text-[var(--primary-light)] mb-2">
            CREATE GAME ROOM
          </h1>
          <p className="text-lg text-[var(--foreground)]">
            Set up your trading competition
          </p>
        </div>

        {/* Main Form */}
        <Card padding="lg">
          <div className="flex flex-col gap-4">
            <Input
              label="Your Name"
              placeholder="Enter your name"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              fullWidth
            />

            <Input
              label="Game Duration (minutes)"
              type="number"
              placeholder="30"
              value={gameDuration}
              onChange={(e) => setGameDuration(e.target.value)}
              fullWidth
              min="5"
              max="120"
            />

            <Input
              label="Maximum Number of Players"
              type="number"
              placeholder="4"
              value={maxPlayers}
              onChange={(e) => setMaxPlayers(e.target.value)}
              fullWidth
              min="2"
              max="10"
            />

            <Button
              onClick={handleCreateRoom}
              variant="primary"
              size="lg"
              fullWidth
              disabled={isCreating}
            >
              {isCreating ? "Creating..." : "Create Room"}
            </Button>

            <Button
              onClick={() => router.push("/")}
              variant="secondary"
              size="lg"
              fullWidth
              disabled={isCreating}
            >
              Cancel
            </Button>
          </div>
        </Card>

        {/* Error Message */}
        {error && (
          <Card className="border-[var(--danger)]">
            <p className="text-[var(--danger)] text-center">{error}</p>
          </Card>
        )}
      </div>
    </div>
  );
}

export default function CreateRoom() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <p className="font-retro text-2xl text-[var(--primary)]">Loading...</p>
      </div>
    }>
      <CreateRoomContent />
    </Suspense>
  );
}
