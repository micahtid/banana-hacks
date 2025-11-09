import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ gameId: string }> }
) {
  try {
    const { gameId } = await params;

    if (!gameId) {
      return NextResponse.json(
        { error: 'Missing gameId parameter' },
        { status: 400 }
      );
    }

    // Get the backend URL from environment variable
    const backendUrl = process.env.FASTAPI_URL || 'http://localhost:8000';

    // Fetch leaderboard from FastAPI backend
    const response = await fetch(`${backendUrl}/api/game/leaderboard/${gameId}`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to fetch leaderboard' }));
      return NextResponse.json(
        { error: errorData.error || errorData.detail || 'Failed to fetch leaderboard' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching leaderboard:', error);
    return NextResponse.json(
      { error: 'Failed to fetch leaderboard' },
      { status: 500 }
    );
  }
}
