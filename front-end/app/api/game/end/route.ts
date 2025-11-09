import { NextRequest, NextResponse } from 'next/server';
import { getRedisClient } from '@/utils/redis';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gameId } = body;

    if (!gameId) {
      return NextResponse.json(
        { error: 'Missing required field: gameId' },
        { status: 400 }
      );
    }

    const redis = getRedisClient();
    const gameExists = await redis.exists(`game:${gameId}`);

    if (!gameExists) {
      return NextResponse.json(
        { error: 'Game not found' },
        { status: 404 }
      );
    }

    await redis.hset(`game:${gameId}`, {
      isEnded: 'true',
      endedAt: Date.now(),
    });

    // Remove from active games
    await redis.srem('games:active', gameId);

    // Trigger backend to cache final leaderboard
    // The backend will handle caching when it detects isEnded=true
    try {
      const backendUrl = process.env.FASTAPI_URL || 'http://localhost:8000';
      // Just fetch the leaderboard once to trigger caching if not already cached
      await fetch(`${backendUrl}/api/game/leaderboard/${gameId}`).catch(() => {
        // Ignore errors - backend will cache on next request
      });
    } catch (error) {
      // Ignore errors - backend will handle caching
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error ending game:', error);
    return NextResponse.json(
      { error: 'Failed to end game' },
      { status: 500 }
    );
  }
}
