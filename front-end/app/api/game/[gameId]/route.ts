import { NextRequest, NextResponse } from 'next/server';
import { getRedisClient } from '@/utils/redis';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ gameId: string }> }
) {
  try {
    const { gameId } = await params;

    if (!gameId) {
      return NextResponse.json(
        { error: 'Missing gameId' },
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

    // Parse JSON fields and transform to match Game interface
    const players = JSON.parse(gameData.players || '[]');

    // Transform players to match User interface (convert ISO string to Date)
    const users = players.map((player: any) => ({
      ...player,
      lastInteractionT: player.lastInteractionT ? new Date(player.lastInteractionT) : new Date(),
    }));

    // ✨ NEW: Get current price and market data from FastAPI if available
    let currentPrice = parseFloat(gameData.coinPrice || '100');
    let priceHistory: number[] = [];
    let volatility = 0;
    let marketActive = false;
    
    try {
      const backendUrl = process.env.FASTAPI_URL || 'http://localhost:8000';
      const marketResponse = await fetch(`${backendUrl}/api/game/market-data/${gameId}`);
      
      if (marketResponse.ok) {
        const marketData = await marketResponse.json();
        currentPrice = marketData.currentPrice;
        priceHistory = marketData.priceHistory || [];
        volatility = marketData.volatility || 0;
        marketActive = true;
        console.log(`Fetched market data: price=$${currentPrice.toFixed(2)}, history length=${priceHistory.length}`);
      }
    } catch (error) {
      console.log('Market data not available, using static price');
      // Continue with static price if FastAPI is not available
    }

    const parsedData = {
      gameId,
      isStarted: gameData.isStarted === 'true',
      isEnded: gameData.isEnded === 'true',
      users, // Transform 'players' to 'users' to match Game interface
      coin: priceHistory.length > 0 ? priceHistory : [currentPrice], // Use price history if available, else array with current price
      interactions: parseInt(gameData.interactions || '0'), // Get trade count from Redis
      eventTimer: gameData.eventTimer ? new Date(parseInt(gameData.eventTimer)) : new Date(),
      startTime: gameData.startedAt ? new Date(parseInt(gameData.startedAt)) : null,
      endTime: gameData.endedAt ? new Date(parseInt(gameData.endedAt)) : null,
      gameDuration: parseInt(gameData.duration || '300'),
      maxPlayers: parseInt(gameData.maxPlayers || '4'),
      creatorId: gameData.creatorId,
      // ✨ NEW: Additional market data
      currentPrice,
      volatility,
      marketActive,
      priceHistoryLength: priceHistory.length
    };

    return NextResponse.json({ game: parsedData, success: true });
  } catch (error) {
    console.error('Error getting game:', error);
    return NextResponse.json(
      { error: 'Failed to get game data' },
      { status: 500 }
    );
  }
}
