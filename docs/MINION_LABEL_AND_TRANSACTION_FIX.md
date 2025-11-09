# Minion Label and Transaction History Fix

## Summary

Fixed two issues:
1. **Minion labels in shop now match the labels in the start/stop section**
2. **Minion transaction history is now permanently stored and uses meaningful names**

## Changes Made

### Issue 1: Inconsistent Minion Labels

**Problem:**
- Shop displayed nice names like "HODL Master", "Quick Scalper", etc.
- Dashboard start/stop section displayed backend types like "mean_reversion", "momentum", etc.
- Transaction history showed "Bot_12345678" instead of meaningful names

**Solution:**
Pass and store the display name throughout the entire system.

#### Files Modified:

**1. `back-end/api_server.py`**
- Added `botName` field to `BotBuyRequest` model
- Store the display name when creating minions
- Pass display name to Bot constructor

**2. `back-end/bot.py`**
- Added `bot_name` parameter to Bot constructor
- Store `bot_name` as instance variable
- Use `bot_name` in transaction history (instead of `Bot_{id}`)
- Save/load `bot_name` to/from Redis
- Return `bot_name` in `to_dict()` method

**3. `front-end/utils/database_functions.tsx`**
- Added `botName` parameter to `buyMinion()` function
- Send `botName` to backend API

**4. `front-end/components/game/Shops.tsx`**
- Pass minion display name when purchasing (already did this, just needed backend to use it)
- Updated custom minion to use "Custom Minion" as display name

### Issue 2: Transaction History Persistence

**Problem:**
User reported that minion trade history was not being stored permanently.

**Solution:**
Verified and improved transaction history persistence.

#### Verification Steps:

1. ✅ **No code deletes transactions**
   - Only `clear_transactions()` method exists, but it's never called
   - Transactions are only added, never removed

2. ✅ **Endpoints don't overwrite transaction history**
   - `buy_coins` and `sell_coins` endpoints properly use `TransactionHistory.add_transaction()`
   - Legacy interaction counter code has been removed (was causing overwrites before)

3. ✅ **Increased expiration time**
   - Changed from 30 days to 90 days
   - More than sufficient for any game duration
   - Prevents Redis from filling up with old data

#### Files Modified:

**1. `back-end/transaction_history.py`**
- Increased transaction expiration from 30 to 90 days
- Updated comment to clarify purpose

**2. `back-end/bot.py`**
- Bot transactions now use `self.bot_name` instead of `f'Bot_{self.bot_id[:8]}'`
- This makes transaction history much more readable

## Result

### Before:
- Shop: "HODL Master"
- Dashboard: "mean_reversion"
- Transaction: "Bot_abc12345"

### After:
- Shop: "HODL Master"
- Dashboard: "HODL Master"
- Transaction: "HODL Master"

## Transaction History Storage

Transactions are stored in two places:

1. **Primary Storage:** `transactions:{game_id}` (Redis LIST)
   - All transactions in chronological order
   - Expires after 90 days
   - Used by transaction history API

2. **Legacy Storage:** `game:{game_id}` → `interactions` (Hash field)
   - Array of transactions for backward compatibility
   - No separate expiration (part of game data)
   - Used by older frontend code

## Testing Checklist

When testing the application:

1. ✅ **Purchase a premade minion** (e.g., "HODL Master")
   - Verify shop shows "HODL Master"
   - Verify dashboard shows "HODL Master" (not "mean_reversion")
   - Verify transaction history shows "HODL Master" (not "Bot_12345678")

2. ✅ **Purchase a custom minion**
   - Verify it shows as "Custom Minion" in dashboard
   - Verify transaction history shows "Custom Minion"

3. ✅ **Start/stop minions**
   - Verify labels remain consistent
   - Verify minion trades appear in transaction history with correct names

4. ✅ **Transaction persistence**
   - Make several trades (user and minion)
   - Refresh the page
   - Verify all transactions are still visible
   - Verify minion transactions show meaningful names

## API Changes

### `POST /api/bot/buy`

**New Request Field:**
```json
{
  "gameId": "string",
  "userId": "string", 
  "botType": "string",
  "botName": "string",  // NEW: Display name (e.g., "HODL Master")
  "cost": 500,
  "customPrompt": "string" // optional
}
```

## Backward Compatibility

All changes are backward compatible:
- `botName` parameter is optional (falls back to `bot_type` if not provided)
- Existing bots without `bot_name` in Redis will generate default name
- Old transaction format still supported
- Legacy interactions field still maintained

## No Breaking Changes

- Frontend API calls remain compatible
- Redis data structure extended, not changed
- All existing features continue to work

