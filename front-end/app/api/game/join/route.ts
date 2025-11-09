import { NextRequest, NextResponse } from 'next/server';
import { getRedisClient } from '@/utils/redis';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gameId, userId, userName } = body;

    if (!gameId || !userId || !userName) {
      return NextResponse.json(
        { error: 'Missing required fields: gameId, userId, userName' },
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

    if (gameData.isStarted === 'true') {
      return NextResponse.json(
        { error: 'Game already started' },
        { status: 400 }
      );
    }

    const players = JSON.parse(gameData.players || '[]');
    const maxPlayers = parseInt(gameData.maxPlayers || '4');

    if (players.length >= maxPlayers) {
      return NextResponse.json(
        { error: 'Game is full' },
        { status: 400 }
      );
    }

    // Check if player already in game
    if (players.some((p: any) => p.userId === userId)) {
      return NextResponse.json(
        { error: 'Player already in game' },
        { status: 400 }
      );
    }

    players.push({
      playerId: userId,
      playerName: userName,
      coinBalance: 0,
      usdBalance: 10000,
      bots: [],
      lastInteractionValue: 0,
      lastInteractionTime: new Date().toISOString(),
    });

    await redis.hset(`game:${gameId}`, 'players', JSON.stringify(players));

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error joining game:', error);
    return NextResponse.json(
      { error: 'Failed to join game' },
      { status: 500 }
    );
  }
}
