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
    const coinHistory = JSON.parse(gameData.coinHistory || '[1.0]');
    const interactions = JSON.parse(gameData.interactions || '[]');

    // Transform players to match both new and old interface (convert ISO string to Date)
    const transformedPlayers = players.map((player: any) => {
      // Support both old and new field names
      const playerId = player.playerId || player.userId;
      const playerName = player.playerName || player.userName;
      const coinBalance = player.coinBalance ?? player.coins ?? 0;
      const usdBalance = player.usdBalance ?? player.usd ?? 10000;
      const lastInteractionValue = player.lastInteractionValue ?? player.lastInteractionV ?? 0;
      const lastInteractionTime = player.lastInteractionTime || player.lastInteractionT;

      return {
        playerId,
        playerName,
        coinBalance,
        usdBalance,
        lastInteractionValue,
        lastInteractionTime: lastInteractionTime ? new Date(lastInteractionTime) : new Date(),
        bots: player.bots || [],
        // Aliases for backward compatibility
        userId: playerId,
        userName: playerName,
        coins: coinBalance,
        usd: usdBalance,
        lastInteractionV: lastInteractionValue,
        lastInteractionT: lastInteractionTime ? new Date(lastInteractionTime) : new Date(),
      };
    });

    // ✨ NEW: Get current price and market data from FastAPI if available
    let currentPrice = parseFloat(gameData.coinPrice || '100');
    let priceHistory: number[] = [];
    let volatility = 0;
    let marketActive = false;
    
    try {
      const backendUrl = process.env.FASTAPI_URL || 'http://localhost:8000';

      // Add timeout to prevent slow API calls from blocking
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 500); // 500ms timeout

      const marketResponse = await fetch(`${backendUrl}/api/game/market-data/${gameId}`, {
        signal: controller.signal,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      });

      clearTimeout(timeoutId);

      if (marketResponse.ok) {
        const marketData = await marketResponse.json();
        currentPrice = marketData.currentPrice;
        priceHistory = marketData.priceHistory || [];
        volatility = marketData.volatility || 0;
        marketActive = true;
      }
    } catch (error) {
      // Continue with static price if FastAPI is not available or times out
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Market data fetch timed out');
      }
    }

    const parsedData = {
      gameId,
      isStarted: gameData.isStarted === 'true',
      durationMinutes: parseInt(gameData.durationMinutes || gameData.duration || '30'),
      maxPlayers: parseInt(gameData.maxPlayers || '4'),
      eventTime: gameData.eventTime ? new Date(gameData.eventTime) : new Date(),

      players: transformedPlayers,

      coinHistory: priceHistory.length > 0 ? priceHistory : coinHistory,
      totalCoin: parseFloat(gameData.totalCoin || '1000000'),
      totalUsd: parseFloat(gameData.totalUsd || '1000000'),

      interactions: interactions,

      // Additional fields for backward compatibility
      isEnded: gameData.isEnded === 'true',
      startTime: gameData.startedAt ? new Date(parseInt(gameData.startedAt)) : null,
      endTime: gameData.endedAt ? new Date(parseInt(gameData.endedAt)) : null,
      creatorId: gameData.creatorId,

      // Aliases for backward compatibility
      users: transformedPlayers,
      coin: priceHistory.length > 0 ? priceHistory : coinHistory,
      gameDuration: parseInt(gameData.durationMinutes || gameData.duration || '30'),
      eventTimer: gameData.eventTime ? new Date(gameData.eventTime) : new Date(),

      // Additional market data
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
