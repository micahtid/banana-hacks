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
    
    // ✨ NEW: Get dynamic price from FastAPI if available
    let coinPrice = parseFloat(gameData.coinPrice || '100');
    try {
      const backendUrl = process.env.FASTAPI_URL || 'http://localhost:8000';
      const marketResponse = await fetch(`${backendUrl}/api/game/market-data/${gameId}`);
      
      if (marketResponse.ok) {
        const marketData = await marketResponse.json();
        coinPrice = marketData.currentPrice;
        console.log(`Using dynamic price: $${coinPrice.toFixed(2)}`);
      } else {
        console.log(`Using static price: $${coinPrice.toFixed(2)} (market data not available)`);
      }
    } catch (error) {
      console.log(`Using static price: $${coinPrice.toFixed(2)} (FastAPI not reachable)`);
      // Continue with static price if FastAPI is not available
    }

    // Support both old (userId) and new (playerId) field names
    const playerIndex = players.findIndex((p: any) => (p.playerId || p.userId) === userId);
    if (playerIndex === -1) {
      return NextResponse.json(
        { error: 'Player not found in game' },
        { status: 404 }
      );
    }

    const player = players[playerIndex];
    const totalCost = amount * coinPrice;

    // Support both old and new field names
    const currentUsd = player.usdBalance ?? player.usd ?? 0;
    const currentCoins = player.coinBalance ?? player.coins ?? 0;

    if (currentUsd < totalCost) {
      return NextResponse.json(
        { error: 'Insufficient funds' },
        { status: 400 }
      );
    }

    // Update using new field names (and maintain old for backward compatibility)
    player.usdBalance = currentUsd - totalCost;
    player.coinBalance = currentCoins + amount;
    player.usd = player.usdBalance;
    player.coins = player.coinBalance;
    player.lastInteractionValue = amount;
    player.lastInteractionTime = new Date().toISOString();
    player.lastInteractionV = amount;
    player.lastInteractionT = player.lastInteractionTime;

    // Update players
    await redis.hset(`game:${gameId}`, 'players', JSON.stringify(players));

    // Track the interaction
    const interactions = JSON.parse(gameData.interactions || '[]');
    interactions.push({
      interactionName: 'Buy Coins',
      interactionDescription: `${player.playerName || player.userName} bought ${amount} BC for $${totalCost.toFixed(2)}`
    });
    await redis.hset(`game:${gameId}`, 'interactions', JSON.stringify(interactions));

    return NextResponse.json({ 
      success: true, 
      player,
      coinPrice,  // Include price used for transparency
      totalCost 
    });
  } catch (error) {
    console.error('Error buying coins:', error);
    return NextResponse.json(
      { error: 'Failed to buy coins' },
      { status: 500 }
    );
  }
}
