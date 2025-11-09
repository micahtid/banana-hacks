/**
 * Home Page (Landing Page)
 * 
 * Entry point for the application
 * Handles authentication and game room creation/joining
 */

"use client";

import { useUser } from "@/providers/UserProvider";
import { signIn, signOut, joinRoom } from "@/utils/database_functions";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Card } from "@/components/Card";
import { useState } from "react";
import { useRouter } from "next/navigation";

/* ============================================
   COMPONENT
   ============================================ */

export default function Home() {
  /* ============================================
     STATE & HOOKS
     ============================================ */
  
  const { user } = useUser();
  const router = useRouter();
  
  // Form state
  const [gameId, setGameId] = useState("");
  const [userName, setUserName] = useState("");
  const [error, setError] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  
  // UI state
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showJoinForm, setShowJoinForm] = useState(false);

  /* ============================================
     EVENT HANDLERS
     ============================================ */

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

  /* ============================================
     RENDER
     ============================================ */

  return (
    <div className="flex min-h-screen items-center justify-center p-8 bg-[var(--background)]">
      <div className="flex w-full max-w-md flex-col gap-8">
        {/* ========== Title Section ========== */}
        <div className="text-center">
          <h1 className="font-retro text-6xl text-[var(--primary-light)] mb-4">
            BANANA COIN
          </h1>
          <p className="text-lg text-[var(--foreground)] max-w-lg mx-auto leading-relaxed">
            Compete with friends in real-time trading! Create or join game rooms,
            trade virtual Banana Coins, deploy automated trading bots, and see who
            can maximize their portfolio value before time runs out.
          </p>
        </div>

        {/* ========== Authentication Status ========== */}
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
            {/* ========== Authenticated: Main Actions ========== */}
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

            {/* ========== Logout Button ========== */}
            <Card className="text-center">
              <Button onClick={signOut} variant="secondary" fullWidth>
                Logout
              </Button>
            </Card>
          </>
        )}

        {/* ========== Error Display ========== */}
        {error && (
          <Card className="border-[var(--danger)]">
            <p className="text-[var(--danger)] text-center">{error}</p>
          </Card>
        )}

        {/* ========== Join Room Modal ========== */}
        {showJoinForm && user && (
          <div className="fixed inset-0 bg-[var(--background)] flex items-center justify-center p-8 z-50">
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
                    size="lg"
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
