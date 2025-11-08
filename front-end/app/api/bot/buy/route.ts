import { NextRequest, NextResponse } from 'next/server';
import { getRedisClient } from '@/utils/redis';
import { v4 as uuidv4 } from 'uuid';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gameId, userId, botType, cost } = body;

    if (!gameId || !userId || !botType || cost === undefined) {
      return NextResponse.json(
        { error: 'Missing required fields: gameId, userId, botType, cost' },
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

    const playerIndex = players.findIndex((p: any) => p.userId === userId);
    if (playerIndex === -1) {
      return NextResponse.json(
        { error: 'Player not found in game' },
        { status: 404 }
      );
    }

    const player = players[playerIndex];

    if (player.usd < cost) {
      return NextResponse.json(
        { error: 'Insufficient funds' },
        { status: 400 }
      );
    }

    const newBot = {
      id: uuidv4(),
      type: botType,
      active: false,
      purchasedAt: Date.now(),
    };

    player.usd -= cost;
    player.bots = player.bots || [];
    player.bots.push(newBot);

    await redis.hset(`game:${gameId}`, 'players', JSON.stringify(players));

    return NextResponse.json({ success: true, bot: newBot, player });
  } catch (error) {
    console.error('Error buying bot:', error);
    return NextResponse.json(
      { error: 'Failed to buy bot' },
      { status: 500 }
    );
  }
}
