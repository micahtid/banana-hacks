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

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error starting game:', error);
    return NextResponse.json(
      { error: 'Failed to start game' },
      { status: 500 }
    );
  }
}
