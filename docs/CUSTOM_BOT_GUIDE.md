# Custom Bot with Gemini - Quick Guide

## Overview

Create AI-powered trading bots using natural language. Powered by Google Gemini 2.5 Flash.

## Setup

Add to `.env`:
```env
GEMINI_API_KEY=your_api_key_here
```

Get API key: https://ai.google.dev/

## Usage

### Create a Custom Bot

```javascript
// Front-end API call
fetch('/api/bot/buy', {
  method: 'POST',
  body: JSON.stringify({
    gameId: 'game-123',
    userId: 'user-456',
    botType: 'custom',
    cost: 50.0,
    customPrompt: 'Buy when price increases by 5%, sell when it drops by 3%'
  })
})
```

### Example Prompts

- "Buy when price is trending upward, sell when trending downward"
- "Always buy 1 coin if I have less than 5 coins"
- "Sell when volatility is high, buy when it's low"

## API Endpoint

**POST** `/api/bot/buy`

Required fields:
- `gameId`: string
- `userId`: string  
- `botType`: "custom"
- `cost`: number
- `customPrompt`: string (your strategy description)

## How It Works

1. User provides natural language prompt
2. Gemini generates Python strategy code
3. Bot executes code in sandboxed environment
4. Bot trades based on strategy decisions

## Testing

```bash
# Run unit tests
python test/test_custom_bot.py

# Run API tests (backend must be running)
python test/test_custom_bot_api.py
```

## Security

- Sandboxed code execution (no file/network access)
- Input/output validation
- Safe error handling (defaults to 'hold')

## Troubleshooting

**Bot not working?**
- Check `GEMINI_API_KEY` is set in `.env`
- Verify backend is running
- Check logs for error messages

**Bot always holds?**
- Verify Gemini API key is valid
- Check Redis for generated code: `redis-cli HGET bot:{gameId}:{botId} custom_strategy_code`
