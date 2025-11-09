# Bot Transaction History - Debugging Guide

## Expected Behavior

### 1. Bot Transactions Should Have This Format

When a bot makes a trade, the transaction should look like:

```javascript
{
  name: "Bot_12345678",        // ✅ Contains "Bot" prefix
  type: "buy" or "sell",
  value: 1000,                 // Amount in cents
  interactionName: "Bot_12345678",
  interactionDescription: "BUY 10.00 BC @ $15.00"
}
```

### 2. Front-End Filter Logic

**Line 21-28 in `Transactions.tsx`:**

```typescript
const filteredInteractions = interactions.filter((interaction) => {
  if (!interaction.name) return false;
  
  if (filter === "all") return true;
  if (filter === "bot") return interaction.name.includes("Bot");  // ← This checks for "Bot" in name
  return interaction.type && interaction.type.toLowerCase() === filter;
});
```

**Logic:**
- `filter === "all"` → Show all transactions
- `filter === "bot"` → Show only transactions where `name` contains "Bot"
- `filter === "buy"` or `"sell"` → Show transactions matching that type (both user and bot)

### 3. Bot Stats Counter

**Line 219:**
```typescript
{interactions.filter((i) => i.name && i.name.includes("Bot")).length}
```

Counts all transactions where `name` contains "Bot".

## Potential Issues

### Issue 1: Case Sensitivity ❓

The check is **case-sensitive**: `interaction.name.includes("Bot")`

**✅ Correct:** "Bot_12345678" → Contains "Bot" → ✅ Matches  
**❌ Wrong:** "bot_12345678" → Contains "bot" → ❌ Doesn't match

**Backend code (bot.py line 598, 669):**
```python
'actor_name': f'Bot_{self.bot_id[:8]}'
```
→ Uses capital "B", so this should work ✅

### Issue 2: Name Field Missing ❓

Bot transactions created before the fix might not have the `name` field.

**Check:**
```javascript
// In browser console:
console.log(game.interactions.filter(i => i.interactionName && i.interactionName.includes("Bot")));
```

If this shows bot transactions but the bot filter doesn't work, it means old transactions have `interactionName` but not `name`.

**Fix:** Run migration script again or wait for new bot transactions.

### Issue 3: Bot Transactions Not Being Created ❓

Maybe bots aren't trading at all?

**Check in backend logs:**
- Look for "Bot_xxxxx bought X BC"
- Look for "Bot_xxxxx sold X BC"
- Check if bots are active: `bot.is_toggled = True`

### Issue 4: Filter Logic Issue with Buy/Sell ❓

When you click "BUYS" or "SELLS", it shows **both user and bot** transactions of that type.

This is correct behavior, but if you want to see:
- **Bot buys only** → Need to combine filters (not currently supported)
- **User buys only** → Need to exclude bots (not currently supported)

Current filter options:
- **ALL** → Everything (user + bot + buy + sell)
- **BUYS** → All buy transactions (user + bot)
- **SELLS** → All sell transactions (user + bot)  
- **BOT TRADES** → All bot transactions (buy + sell)

## Diagnostic Questions

Please answer these to help identify the issue:

1. **What exactly doesn't work?**
   - [ ] Bot filter button doesn't filter anything
   - [ ] Bot filter button shows 0 transactions when you know bots have traded
   - [ ] Bot stats counter shows 0 when bots have traded
   - [ ] Bot transactions show up in "ALL" but not in "BOT TRADES"
   - [ ] Something else? _______________________

2. **Do bots appear to be trading?**
   - Check the backend terminal/logs
   - Check if bot balances are changing
   - Check the main dashboard for bot activity

3. **When you click "ALL", do you see any transactions with "BOT" badges?**
   - Lines 166-169 show a "BOT" badge for transactions where `interaction.name.includes("Bot")`

4. **Browser Console Check:**
   Open browser console (F12) and run:
   ```javascript
   // Check all interactions
   console.log('All interactions:', game.interactions);
   
   // Check bot interactions (by name field)
   console.log('Bot transactions (by name):', 
     game.interactions.filter(i => i.name && i.name.includes("Bot")));
   
   // Check bot interactions (by interactionName field - legacy)
   console.log('Bot transactions (by interactionName):', 
     game.interactions.filter(i => i.interactionName && i.interactionName.includes("Bot")));
   
   // Check if any interactions are missing name field
   console.log('Interactions missing name:', 
     game.interactions.filter(i => !i.name));
   ```

## Quick Fix Options

### Option 1: Ignore Case in Filter

Change line 26 in `Transactions.tsx`:

```typescript
// Before
if (filter === "bot") return interaction.name.includes("Bot");

// After (case-insensitive)
if (filter === "bot") return interaction.name.toLowerCase().includes("bot");
```

### Option 2: Check Both name and interactionName

Change line 26 to support legacy format:

```typescript
// Before
if (filter === "bot") return interaction.name.includes("Bot");

// After (check both fields)
if (filter === "bot") {
  return (interaction.name && interaction.name.includes("Bot")) ||
         (interaction.interactionName && interaction.interactionName.includes("Bot"));
}
```

### Option 3: Use is_bot Flag

If transactions have the `is_bot` field from backend:

```typescript
// Most reliable
if (filter === "bot") return interaction.is_bot === true;
```

But this requires the `is_bot` field to be passed from backend to frontend.

## Testing

To verify bot transactions are working:

1. **Start a game with bots enabled**
2. **Wait for bots to trade** (watch backend logs)
3. **Go to Transactions tab**
4. **Click "BOT TRADES"** filter
5. **Expected:** Should show bot transactions
6. **Check bot stats counter** at bottom - should be > 0

## Current Status

Based on the code review:

✅ **Backend** - Bots create transactions with `actor_name: 'Bot_xxxxx'`  
✅ **Backend** - TransactionHistory maps `actor_name` → `name`  
✅ **Frontend** - Filter checks for `name.includes("Bot")`  
✅ **Frontend** - Stats counter checks for `name.includes("Bot")`  

**This should work!** Unless one of the potential issues above is occurring.

Please provide more details about what specifically isn't working so I can fix it!

