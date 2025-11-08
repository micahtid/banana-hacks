"use client";

import { useUser } from "@/providers/UserProvider";
import { signIn, signOut, joinRoom } from "@/utils/database_functions";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Card } from "@/components/Card";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const { user } = useUser();
  const router = useRouter();
  const [gameId, setGameId] = useState("");
  const [userName, setUserName] = useState("");
  const [error, setError] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showJoinForm, setShowJoinForm] = useState(false);

  const handleCreateRoom = () => {
    if (!user) {
      setError("Please login first");
      return;
    }
    router.push(`/create-room`);
  };

  const handleJoinRoom = async () => {
    if (!user) {
      setError("Please login first");
      return;
    }
    if (!userName.trim()) {
      setError("Please enter your name");
      return;
    }
    if (!gameId.trim()) {
      setError("Please enter a game ID");
      return;
    }

    setIsJoining(true);
    setError("");

    try {
      await joinRoom(gameId, user.uid, userName);
      router.push(`/game/${gameId}`);
    } catch (err: any) {
      setError(err.message || "Failed to join room");
    } finally {
      setIsJoining(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="flex w-full max-w-md flex-col gap-6">
        {/* Title */}
        <div className="text-center">
          <h1 className="font-retro text-6xl text-[var(--primary-light)] mb-4">
            BANANA COIN
          </h1>
          <p className="text-xl text-[var(--foreground)]">
            Gamified Trading Simulator
          </p>
        </div>

        {/* Auth Status and Actions */}
        {user === undefined ? (
          <Card className="text-center">
            <p className="text-lg">Checking authentication...</p>
          </Card>
        ) : !user ? (
          <Card className="text-center">
            <p className="text-lg mb-4">Please login to continue</p>
            <Button onClick={signIn} variant="primary" fullWidth>
              Login with Google
            </Button>
          </Card>
        ) : (
          <>
            {/* Main Actions */}
            <Card padding="lg">
              <div className="flex flex-col gap-4">
                <Button
                  onClick={handleCreateRoom}
                  variant="primary"
                  size="lg"
                  fullWidth
                >
                  Create Room
                </Button>
                <Button
                  onClick={() => {
                    setShowJoinForm(true);
                    setError("");
                  }}
                  variant="success"
                  size="lg"
                  fullWidth
                >
                  Join Room
                </Button>
              </div>
            </Card>

            {/* Logout */}
            <Card className="text-center">
              <Button onClick={signOut} variant="secondary" fullWidth>
                Logout
              </Button>
            </Card>
          </>
        )}

        {/* Error Message */}
        {error && (
          <Card className="border-[var(--danger)]">
            <p className="text-[var(--danger)] text-center">{error}</p>
          </Card>
        )}

        {/* Join Room Modal */}
        {showJoinForm && user && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-8 z-50">
            <div className="w-full max-w-md">
              <Card padding="lg">
                <div className="flex flex-col gap-4">
                  <h2 className="font-retro text-3xl text-[var(--primary)] text-center">
                    JOIN ROOM
                  </h2>
                  <Input
                    label="Your Name"
                    placeholder="Enter your name"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    fullWidth
                  />
                  <Input
                    label="Game ID"
                    placeholder="Enter game ID"
                    value={gameId}
                    onChange={(e) => setGameId(e.target.value)}
                    fullWidth
                  />
                  <Button
                    onClick={handleJoinRoom}
                    variant="success"
                    size="lg"
                    fullWidth
                    disabled={isJoining}
                  >
                    {isJoining ? "Joining..." : "Join Game"}
                  </Button>
                  <Button
                    onClick={() => {
                      setShowJoinForm(false);
                      setGameId("");
                      setUserName("");
                    }}
                    variant="secondary"
                    size="sm"
                    fullWidth
                  >
                    Cancel
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
