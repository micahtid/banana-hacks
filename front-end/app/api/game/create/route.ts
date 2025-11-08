import { NextRequest, NextResponse } from 'next/server';
import { getRedisClient } from '@/utils/redis';
import { v4 as uuidv4 } from 'uuid';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { userId, userName, duration, maxPlayers } = body;

    if (!userId || !userName) {
      return NextResponse.json(
        { error: 'Missing required fields: userId, userName' },
        { status: 400 }
      );
    }

    const redis = getRedisClient();
    const gameId = uuidv4();

    const gameData = {
      gameId,
      creatorId: userId,
      isStarted: false,
      isEnded: false,
      duration: duration || 300,
      maxPlayers: maxPlayers || 4,
      players: JSON.stringify([{
        userId,
        userName,
        coins: 0,
        usd: 1000,
        bots: [],
        lastInteractionV: 0,
        lastInteractionT: new Date().toISOString(),
      }]),
      coinPrice: 100,
      interactions: 0,
      eventTimer: 0,
      createdAt: Date.now(),
    };

    await redis.hset(`game:${gameId}`, gameData);
    await redis.sadd('games:active', gameId);

    return NextResponse.json({ gameId, success: true });
  } catch (error) {
    console.error('Error creating game:', error);
    return NextResponse.json(
      { error: 'Failed to create game' },
      { status: 500 }
    );
  }
}
