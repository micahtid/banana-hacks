import { NextRequest, NextResponse } from 'next/server';
import { getRedisClient } from '@/utils/redis';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gameId, userId } = body;

    if (!gameId || !userId) {
      return NextResponse.json(
        { error: 'Missing required fields: gameId, userId' },
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

    const gameData = await redis.hgetall(`game:${gameId}`);

    // Verify user is the creator
    if (gameData.creatorId !== userId) {
      return NextResponse.json(
        { error: 'Only the creator can start the game' },
        { status: 403 }
      );
    }

    if (gameData.isStarted === 'true') {
      return NextResponse.json(
        { error: 'Game already started' },
        { status: 400 }
      );
    }

    await redis.hset(`game:${gameId}`, {
      isStarted: 'true',
      startedAt: Date.now(),
    });

    // ✨ NEW: Start background market updates via FastAPI
    try {
      const backendUrl = process.env.FASTAPI_URL || 'http://localhost:8000';
      const durationMinutes = parseInt(gameData.duration || '300');
      const durationSeconds = durationMinutes * 60; // Convert minutes to seconds for FastAPI
      
      const fastApiResponse = await fetch(`${backendUrl}/api/game/start-market`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gameId,
          duration: durationSeconds,  // Now in seconds!
          totalUsd: 1000000,
          totalBc: 1000000,
          initialPrice: parseFloat(gameData.coinPrice || '1.0'),
          updateInterval: 1.0
        })
      });

      if (!fastApiResponse.ok) {
        console.error('Failed to start market updates:', await fastApiResponse.text());
        // Continue anyway - game can still work with static prices
      } else {
        const marketData = await fastApiResponse.json();
        console.log('Market updates started:', marketData);
      }
    } catch (error) {
      console.error('Error calling FastAPI:', error);
      // Continue anyway - game can still work without market updates
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error starting game:', error);
    return NextResponse.json(
      { error: 'Failed to start game' },
      { status: 500 }
    );
  }
}
