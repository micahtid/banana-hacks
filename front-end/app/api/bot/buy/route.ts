import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gameId, userId, botType, cost, customPrompt } = body;

    console.log('[Bot Buy] Request received:', { gameId, userId, botType, cost });

    if (!gameId || !userId || !botType || cost === undefined) {
      return NextResponse.json(
        { error: 'Missing required fields: gameId, userId, botType, cost' },
        { status: 400 }
      );
    }

    // Check if Python backend is reachable
    console.log('[Bot Buy] Calling Python backend at:', `${PYTHON_API_URL}/api/bot/buy`);

    let response;
    try {
      response = await fetch(`${PYTHON_API_URL}/api/bot/buy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          gameId,
          userId,
          botType,
          cost,
          customPrompt,
        }),
      });
    } catch (fetchError) {
      console.error('[Bot Buy] Failed to connect to Python backend:', fetchError);
      return NextResponse.json(
        { error: 'Cannot connect to Python backend. Is it running on port 8000?' },
        { status: 503 }
      );
    }

    console.log('[Bot Buy] Python backend response status:', response.status);

    if (!response.ok) {
      let errorData;
      let rawText;
      try {
        rawText = await response.text();
        console.error('[Bot Buy] Raw response from Python:', rawText);
        errorData = JSON.parse(rawText);
      } catch (e) {
        console.error('[Bot Buy] Could not parse Python response, raw text:', rawText);
        errorData = { detail: rawText || 'Unknown error from Python backend' };
      }
      console.error('[Bot Buy] Parsed error data:', errorData);
      return NextResponse.json(
        { error: errorData.detail || errorData.error || 'Failed to buy bot' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[Bot Buy] Success, bot created:', data.botId);
    
    // Transform response to match front-end format
    const bot = {
      id: data.botId,
      type: data.botType,
      active: true,
      purchasedAt: Date.now(),
      ...data.bot,
    };

    return NextResponse.json({ 
      success: true, 
      bot,
      newUsd: data.newUsd
    });
  } catch (error) {
    console.error('[Bot Buy] Unexpected error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to buy bot', 
        details: error instanceof Error ? error.message : String(error) 
      },
      { status: 500 }
    );
  }
}
