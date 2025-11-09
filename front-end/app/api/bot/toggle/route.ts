import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gameId, userId, botId } = body;

    console.log('[Bot Toggle] Request received:', { gameId, userId, botId });

    if (!gameId || !userId || !botId) {
      console.error('[Bot Toggle] Missing required fields');
      return NextResponse.json(
        { error: 'Missing required fields: gameId, userId, botId' },
        { status: 400 }
      );
    }

    // Call Python backend to toggle bot
    console.log('[Bot Toggle] Calling Python backend...');
    const response = await fetch(`${PYTHON_API_URL}/api/bot/toggle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        gameId,
        userId,
        botId,
      }),
    });

    console.log('[Bot Toggle] Python backend response:', response.status);

    if (!response.ok) {
      const errorData = await response.json();
      console.error('[Bot Toggle] Error from Python:', errorData);
      return NextResponse.json(
        { error: errorData.detail || 'Failed to toggle bot' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[Bot Toggle] Success! New state:', data.isActive);
    
    // Transform response to match front-end format
    const bot = {
      id: data.botId,
      active: data.isActive,
      ...data.bot,
    };

    return NextResponse.json({ 
      success: true, 
      bot 
    });
  } catch (error) {
    console.error('Error toggling bot:', error);
    return NextResponse.json(
      { error: 'Failed to toggle bot' },
      { status: 500 }
    );
  }
}
