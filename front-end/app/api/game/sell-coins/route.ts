import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

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

    if (amount <= 0) {
      return NextResponse.json(
        { error: 'Amount must be positive' },
        { status: 400 }
      );
    }

    // Call backend API which has all the proper safeguards
    console.log('[Sell Coins] Calling backend API:', `${BACKEND_URL}/api/game/sell-coins`);
    
    let response;
    try {
      response = await fetch(`${BACKEND_URL}/api/game/sell-coins`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          gameId,
          userId,
          action: 'sell',
          amount,
        }),
      });
    } catch (fetchError) {
      console.error('[Sell Coins] Failed to connect to backend:', fetchError);
      return NextResponse.json(
        { error: 'Cannot connect to backend API. Is it running on port 8000?' },
        { status: 503 }
      );
    }

    console.log('[Sell Coins] Backend response status:', response.status);

    if (!response.ok) {
      let errorData;
      let rawText;
      try {
        rawText = await response.text();
        console.error('[Sell Coins] Raw response from backend:', rawText);
        errorData = JSON.parse(rawText);
      } catch (e) {
        console.error('[Sell Coins] Could not parse backend response, raw text:', rawText);
        errorData = { detail: rawText || 'Unknown error from backend' };
      }
      console.error('[Sell Coins] Parsed error data:', errorData);
      
      // Handle backend error response format
      if (errorData.detail) {
        return NextResponse.json(
          { error: errorData.detail },
          { status: response.status }
        );
      }
      
      // Handle success: false format from backend
      if (errorData.success === false) {
        return NextResponse.json(
          { 
            success: false,
            error: errorData.message || 'Transaction failed',
            ...errorData
          },
          { status: 200 } // Return 200 since backend returned success: false (not an HTTP error)
        );
      }
      
      return NextResponse.json(
        { error: errorData.error || errorData.message || 'Failed to sell coins' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[Sell Coins] Success:', data);
    
    // Transform backend response to match front-end format
    return NextResponse.json({ 
      success: data.success !== false, // Backend returns success: true or success: false
      player: {
        usdBalance: data.newUsd,
        coinBalance: data.newCoins,
        usd: data.newUsd,
        coins: data.newCoins,
      },
      coinPrice: data.price,
      totalRevenue: data.revenue
    });
  } catch (error) {
    console.error('[Sell Coins] Unexpected error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to sell coins', 
        details: error instanceof Error ? error.message : String(error) 
      },
      { status: 500 }
    );
  }
}
