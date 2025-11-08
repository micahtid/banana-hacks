import { NextRequest, NextResponse } from 'next/server';
import { getRedisClient } from '@/utils/redis';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gameId, userId, amount } = body;

    if (!gameId || !userId || amount === undefined) {
      return NextResponse.json(
        { error: 'Missing required fields: gameId, userId, amount' },
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
    const players = JSON.parse(gameData.players || '[]');
    const coinPrice = parseFloat(gameData.coinPrice || '100');

    const playerIndex = players.findIndex((p: any) => p.userId === userId);
    if (playerIndex === -1) {
      return NextResponse.json(
        { error: 'Player not found in game' },
        { status: 404 }
      );
    }

    const player = players[playerIndex];

    if (player.coins < amount) {
      return NextResponse.json(
        { error: 'Insufficient coins' },
        { status: 400 }
      );
    }

    const totalRevenue = amount * coinPrice;
    player.coins -= amount;
    player.usd += totalRevenue;

    await redis.hset(`game:${gameId}`, 'players', JSON.stringify(players));

    return NextResponse.json({ success: true, player });
  } catch (error) {
    console.error('Error selling coins:', error);
    return NextResponse.json(
      { error: 'Failed to sell coins' },
      { status: 500 }
    );
  }
}
