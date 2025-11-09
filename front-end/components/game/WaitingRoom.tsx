"use client";

import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { startRoom, type Game, type User } from "@/utils/database_functions";
import { useState } from "react";
import { useUser } from "@/providers/UserProvider";
import Image from "next/image";

interface WaitingRoomProps {
  game: Game;
  currentUser: User;
}

export default function WaitingRoom({ game, currentUser }: WaitingRoomProps) {
  const { user } = useUser();
  const [isStarting, setIsStarting] = useState(false);
  const isCreator = user?.uid === game.creatorId;

  const handleStartGame = async () => {
    if (!user?.uid) return;
    setIsStarting(true);
    try {
      await startRoom(game.gameId, user.uid);
    } catch (error) {
      console.error("Failed to start game:", error);
      setIsStarting(false);
    }
  };

  const copyGameId = () => {
    navigator.clipboard.writeText(game.gameId);
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="w-full max-w-2xl flex flex-col gap-4">
        {/* Header */}
        <div className="text-center">
          <h1 className="font-retro text-5xl text-[var(--primary-light)] mb-2">
            WAITING ROOM
          </h1>
        </div>

        {/* Game ID */}
        <Card padding="lg">
          <p className="text-[var(--foreground)] mb-3 text-center">
            Share this Game ID with other players:
          </p>
          <div className="flex items-center gap-3">
            <div className="flex-1 p-3 bg-[var(--background)] border-2 border-[var(--border)] font-mono text-[var(--primary)] text-center">
              {game.gameId}
            </div>
            <Button onClick={copyGameId} variant="primary">
              Copy
            </Button>
          </div>
        </Card>

        {/* Players List */}
        <Card title={`${game.users.length} / ${game.maxPlayers}`} padding="lg">
          <div className="grid grid-cols-2 gap-3">
            {game.users.map((player) => (
              <div
                key={player.userId}
                className={`
                  p-3 border-2
                  ${
                    player.userId === currentUser.userId
                      ? "border-[var(--primary)] bg-[var(--border)]"
                      : "border-[var(--border)]"
                  }
                `}
              >
                <div className="font-retro text-lg text-[var(--primary-light)] flex items-center gap-2">
                  <span>{player.userName}</span>
                  {player.userId === game.creatorId && (
                    <Image
                      src="/crown.svg"
                      alt="Creator"
                      width={16}
                      height={16}
                      className="inline-block"
                    />
                  )}
                  {player.userId === currentUser.userId && <span>(You)</span>}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Start Button or Waiting Message */}
        {isCreator ? (
          <Card padding="lg">
            <Button
              onClick={handleStartGame}
              variant="success"
              size="lg"
              fullWidth
              disabled={isStarting}
            >
              {isStarting ? "Starting..." : `Start (${game.gameDuration} min)`}
            </Button>
          </Card>
        ) : (
          <Card className="text-center">
            <p className="text-lg text-[var(--foreground)]">
              Waiting for the creator to start the game...
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
