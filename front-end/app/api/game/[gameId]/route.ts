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

    // Batch fetch all bot data in one go for better performance
    const allBotIds = players.flatMap((player: any) =>
      (player.bots || []).map((bot: any) => `bot:${gameId}:${bot.botId}`)
    );

    // Use pipeline to fetch all bots at once
    const pipeline = redis.pipeline();
    allBotIds.forEach((botKey: string) => {
      pipeline.hgetall(botKey);
    });
    const botResults = allBotIds.length > 0 ? await pipeline.exec() : [];

    // Create a map of bot data for quick lookup
    const botDataMap = new Map();
    botResults?.forEach((result, index) => {
      if (result && result[1]) {
        botDataMap.set(allBotIds[index], result[1]);
      }
    });

    // Transform players to match both new and old interface (convert ISO string to Date)
    const transformedPlayers = players.map((player: any) => {
      // Support both old and new field names
      const playerId = player.playerId || player.userId;
      const playerName = player.playerName || player.userName;
      const coinBalance = player.coinBalance ?? player.coins ?? 0;
      const usdBalance = player.usdBalance ?? player.usd ?? 10000;
      const lastInteractionValue = player.lastInteractionValue ?? player.lastInteractionV ?? 0;
      const lastInteractionTime = player.lastInteractionTime || player.lastInteractionT;

      // Process bot details using cached data
      const playerBots = player.bots || [];

      const fullBotDetails = playerBots.map((bot: any) => {
        const botKey = `bot:${gameId}:${bot.botId}`;
        const botData = botDataMap.get(botKey);

        if (!botData) {
          // Bot not found in Redis, return minimal info
          return {
            botId: bot.botId,
            botName: bot.botName || 'Bot',
            isActive: bot.isActive ?? false,
            usdBalance: 0,
            coinBalance: 0,
            startingUsdBalance: 0,
          };
        }

        // Safely parse numeric values with fallback to 0
        const parseFloatSafe = (value: any): number => {
          if (value === null || value === undefined) return 0;
          const parsed = parseFloat(String(value));
          return isNaN(parsed) ? 0 : parsed;
        };

        // Parse isActive - Redis stores Python booleans as "True" or "False" strings
        const rawIsToggled = botData.is_toggled;
        const isActive = rawIsToggled === 'True' || rawIsToggled === 'true' || rawIsToggled === '1';

        return {
          botId: bot.botId,
          botName: bot.botName || botData.bot_type || 'Bot',
          isActive,
          usdBalance: parseFloatSafe(botData.usd),
          coinBalance: parseFloatSafe(botData.bc),
          startingUsdBalance: parseFloatSafe(botData.usd_given),
          botType: botData.bot_type || 'unknown',
        };
      });

      return {
        playerId,
        playerName,
        coinBalance,
        usdBalance,
        lastInteractionValue,
        lastInteractionTime: lastInteractionTime ? new Date(lastInteractionTime) : new Date(),
        bots: fullBotDetails,
        // Aliases for backward compatibility
        userId: playerId,
        userName: playerName,
        coins: coinBalance,
        usd: usdBalance,
        lastInteractionV: lastInteractionValue,
        lastInteractionT: lastInteractionTime ? new Date(lastInteractionTime) : new Date(),
      };
    });

    // ✨ NEW: Get current price and market data directly from Redis
    let currentPrice = parseFloat(gameData.coinPrice || '1.0');
    let priceHistory: number[] = [];
    let volatility = 0;
    let marketActive = false;
    let eventTitle = '';
    let eventTriggered = false;
    let genericNews = '';
    let allGenericNews: string[] = [];
    
    try {
      // First, try to read market data directly from Redis (faster and more reliable)
      const marketDataKey = `market:${gameId}:data`;
      const marketDataExists = await redis.exists(marketDataKey);
      
      if (marketDataExists) {
        const marketData = await redis.hgetall(marketDataKey);
        
        if (marketData && marketData.current_price) {
          currentPrice = parseFloat(marketData.current_price);
          priceHistory = JSON.parse(marketData.price_history || '[]');
          volatility = parseFloat(marketData.volatility || '0');
          marketActive = true;
        }
      }
      
      // Fetch event data from market basic info
      const marketKey = `market:${gameId}`;
      const marketKeyExists = await redis.exists(marketKey);
      if (marketKeyExists) {
        const marketInfo = await redis.hgetall(marketKey);
        if (marketInfo) {
          eventTitle = marketInfo.event_title || '';
          eventTriggered = marketInfo.event_triggered === 'True' || marketInfo.event_triggered === 'true';
        }
      }
      
      // Always try to get generic news from FastAPI (even if we have Redis data)
      // This ensures we always have generic news when there's no event
      const backendUrl = process.env.FASTAPI_URL || 'http://localhost:8000';
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 200);

        const marketResponse = await fetch(`${backendUrl}/api/game/market-data/${gameId}`, {
          signal: controller.signal,
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
          },
        });

        clearTimeout(timeoutId);

        if (marketResponse.ok) {
          const marketData = await marketResponse.json();
          
          // If Redis market data is not available, use FastAPI data
          if (!marketActive) {
            currentPrice = marketData.currentPrice;
            priceHistory = marketData.priceHistory || [];
            volatility = marketData.volatility || 0;
            eventTitle = marketData.eventTitle || '';
            eventTriggered = marketData.eventTriggered || false;
            marketActive = true;
          }
          
          // Always get generic news from market data if available
          // Check for both truthy value and non-empty string
          if (marketData.genericNews && marketData.genericNews.trim() !== '') {
            genericNews = marketData.genericNews;
          }
          // Get all headlines for rotation
          // Always update to get latest headlines from backend
          // Create a new array reference to ensure React detects the change
          if (marketData.allGenericNews && Array.isArray(marketData.allGenericNews)) {
            allGenericNews = [...marketData.allGenericNews];
          }
        } else if (marketResponse.status === 404) {
          // Market doesn't exist yet - provide fallback generic news
          // This happens when game is created but market hasn't started
          genericNews = "Market Opening Soon";
        }
      } catch (error) {
        // Silently fail - we'll just use Redis data
      }
    } catch (error) {
      // Continue with static price if market data is not available
      // Don't log errors to reduce console spam
    }
    
    // Ensure we always have a fallback generic news if none was provided
    if (!genericNews || genericNews.trim() === '') {
      genericNews = "Market Activity Normal";
    }
    // Ensure we have fallback headlines for rotation
    if (!allGenericNews || allGenericNews.length === 0) {
      allGenericNews = [
        "Market Analysts Predict Bullish Trend",
        "New Trading Features Announced",
        "Investor Confidence Remains High",
        "Price Stability Maintained",
        "Trading Activity Increases",
        "Market Activity Normal"
      ];
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
      priceHistoryLength: priceHistory.length,
      eventTitle,
      eventTriggered,
      genericNews: genericNews, // Will be populated from market data if available
      allGenericNews: allGenericNews // All headlines for rotation
    };

    const response = NextResponse.json({ game: parsedData, success: true });

    // Add cache headers to ensure fresh data on every request
    response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
    response.headers.set('Pragma', 'no-cache');
    response.headers.set('Expires', '0');

    return response;
  } catch (error) {
    console.error('Error getting game:', error);
    return NextResponse.json(
      { error: 'Failed to get game data' },
      { status: 500 }
    );
  }
}
