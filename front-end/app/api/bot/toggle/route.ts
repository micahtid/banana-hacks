import { NextRequest, NextResponse } from 'next/server';
import { getRedisClient } from '@/utils/redis';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gameId, userId, botId } = body;

    if (!gameId || !userId || !botId) {
      return NextResponse.json(
        { error: 'Missing required fields: gameId, userId, botId' },
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
    const botIndex = player.bots?.findIndex((b: any) => b.id === botId);

    if (botIndex === -1 || botIndex === undefined) {
      return NextResponse.json(
        { error: 'Bot not found' },
        { status: 404 }
      );
    }

    player.bots[botIndex].active = !player.bots[botIndex].active;

    await redis.hset(`game:${gameId}`, 'players', JSON.stringify(players));

    return NextResponse.json({ success: true, bot: player.bots[botIndex] });
  } catch (error) {
    console.error('Error toggling bot:', error);
    return NextResponse.json(
      { error: 'Failed to toggle bot' },
      { status: 500 }
    );
  }
}
