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
      durationMinutes: duration || 30,  // Default: 30 minutes
      maxPlayers: maxPlayers || 4,
      eventTime: new Date().toISOString(),
      players: JSON.stringify([{
        playerId: userId,
        playerName: userName,
        coinBalance: 0,
        usdBalance: 10000,
        lastInteractionValue: 0,
        lastInteractionTime: new Date().toISOString(),
        bots: [],
      }]),
      coinHistory: JSON.stringify([1.0]),  // Initial price
      totalCoin: 1000000,  // 1M coins in market
      totalUsd: 1000000,   // 1M USD in market
      interactions: JSON.stringify([]),
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
