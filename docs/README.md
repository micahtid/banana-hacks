# Documentation

Documentation for Banana Coin Trading Game custom bot feature.

## Files

- **[CUSTOM_BOT_GUIDE.md](CUSTOM_BOT_GUIDE.md)** - Quick guide for using custom bots
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details

## Quick Start

### Setup
```env
# Add to .env file
GEMINI_API_KEY=your_api_key_here
```

### Test
```bash
python test/test_custom_bot.py
```

### Use
```javascript
// Front-end call
fetch('/api/bot/buy', {
  method: 'POST',
  body: JSON.stringify({
    botType: 'custom',
    customPrompt: 'Buy when price goes up, sell when it goes down'
  })
})
```

## Status

✅ Backend complete (5/5 tests passing)  
✅ API ready  
⏳ UI component needed

---

Get Gemini API key: https://ai.google.dev/
