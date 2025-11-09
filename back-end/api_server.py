"""
FastAPI Server for Banana Coin Trading Game
Implements background market updates with asyncio.create_task()
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import asyncio
import time
import logging
from datetime import datetime

# Import existing modules
from market import Market, MarketData
from user import User
from wallet import UserWallet
from bot import Bot, generate_custom_bot_strategy
from bot_operations import buyBot, toggleBot
from redis_helper import get_redis_connection
from transaction_history import TransactionHistory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Banana Coin Trading API",
    description="Real-time trading game with background market updates",
    version="1.0.0"
)

# CORS middleware for front-end access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage
active_game_tasks: Dict[str, asyncio.Task] = {}
game_states: Dict[str, Dict] = {}  # Store game state info

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class GameStartRequest(BaseModel):
    gameId: str
    duration: int = Field(default=300, description="Game duration in seconds")
    totalUsd: float = Field(default=100, description="Total USD in market")
    totalBc: float = Field(default=100, description="Total BC in market")
    initialPrice: float = Field(default=1.0, description="Initial BC price")
    updateInterval: float = Field(default=1.0, description="Market update interval in seconds")

class TradeRequest(BaseModel):
    gameId: str
    userId: str
    action: str = Field(..., description="'buy' or 'sell'")
    amount: float = Field(..., gt=0, description="Amount of BC to trade")

class BotRequest(BaseModel):
    gameId: str
    userId: str
    botType: str = Field(..., description="Type of bot: random, momentum, mean_reversion, market_maker, hedger")
    parameters: Optional[Dict] = None

class BotToggleRequest(BaseModel):
    gameId: str
    userId: str
    botId: str

class BotBuyRequest(BaseModel):
    gameId: str
    userId: str
    botType: str = Field(..., description="Type of bot strategy")
    cost: float = Field(..., gt=0, description="Cost in USD")
    botName: Optional[str] = Field(None, description="Display name for the bot (e.g., 'HODL Master')")
    customPrompt: Optional[str] = None

# ============================================================================
# BACKGROUND TASK: MARKET UPDATES
# ============================================================================

async def run_market_updates(game_id: str, duration: int, update_interval: float):
    """
    Background task that updates the market every `update_interval` seconds
    for the specified duration. Optimized to maintain consistent timing.
    """
    start_time = time.time()
    end_time = start_time + duration
    update_count = 0
    next_update_time = start_time + update_interval
    
    logger.info(f"🎮 Starting market updates for game {game_id} - Duration: {duration}s")
    
    try:
        while time.time() < end_time:
            update_start = time.time()
            
            try:
                # Load market from Redis
                market = await asyncio.to_thread(Market.load_from_redis, game_id)
                
                if market is None:
                    logger.warning(f"Market {game_id} not found in Redis, stopping updates")
                    break
                
                # Update the market (runs in thread pool to avoid blocking)
                await asyncio.to_thread(market.updateMarket)
                
                update_count += 1
                
                # Log every 10 updates
                if update_count % 10 == 0:
                    logger.info(
                        f"Game {game_id}: Tick {market.current_tick}, "
                        f"Price ${market.market_data.current_price:.2f}, "
                        f"Updates: {update_count}"
                    )
                
                # Update game state info
                if game_id in game_states:
                    game_states[game_id].update({
                        'current_tick': market.current_tick,
                        'current_price': market.market_data.current_price,
                        'updates_count': update_count,
                        'last_update': datetime.now().isoformat()
                    })
                
            except Exception as e:
                logger.error(f"Error updating market {game_id}: {e}")
                # Continue running even if one update fails
            
            # Calculate sleep time to maintain consistent interval
            update_elapsed = time.time() - update_start
            sleep_time = max(0, update_interval - update_elapsed)
            
            # If we're behind schedule, log a warning
            if sleep_time == 0:
                logger.warning(f"Market update took {update_elapsed:.3f}s (longer than interval {update_interval}s)")
            
            await asyncio.sleep(sleep_time)
            next_update_time += update_interval
        
        # Game finished
        logger.info(f"✅ Game {game_id} completed after {duration} seconds, {update_count} updates")
        
        # Mark game as ended in Redis
        try:
            r = await asyncio.to_thread(get_redis_connection)
            await asyncio.to_thread(r.hset, f"game:{game_id}", "isEnded", "true")
        except Exception as e:
            logger.error(f"Error marking game {game_id} as ended: {e}")
        
    except asyncio.CancelledError:
        logger.info(f"🛑 Game {game_id} was cancelled after {update_count} updates")
        raise
    except Exception as e:
        logger.error(f"❌ Fatal error in market updates for {game_id}: {e}")
    finally:
        # Clean up task reference
        if game_id in active_game_tasks:
            del active_game_tasks[game_id]
        if game_id in game_states:
            game_states[game_id]['status'] = 'completed'

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/api/game/start-market")
async def start_market_updates(request: GameStartRequest):
    """
    Start background market updates for a game.
    This endpoint returns immediately while market updates continue in the background.
    
    The front-end should call this after creating a game and users are ready.
    """
    game_id = request.gameId
    
    # Check if game already has active updates
    if game_id in active_game_tasks and not active_game_tasks[game_id].done():
        return {
            "success": False,
            "error": "Market updates already running for this game"
        }
    
    # Initialize or load market from Redis
    try:
        # Try to load existing market
        market = Market.load_from_redis(game_id)
        
        if market is None:
            # Create new market
            market = Market(
                initial_price=request.initialPrice,
                game_id=game_id,
                duration=request.duration
            )
            market.dollar_supply = request.totalUsd
            market.bc_supply = request.totalBc
            market.market_data.dollar_supply = request.totalUsd
            market.market_data.bc_supply = request.totalBc
            market.save_to_redis()
            
            logger.info(f"Created new market for game {game_id}")
        else:
            logger.info(f"Loaded existing market for game {game_id}")
        
        # Store game state info
        game_states[game_id] = {
            'game_id': game_id,
            'start_time': datetime.now().isoformat(),
            'duration': request.duration,
            'update_interval': request.updateInterval,
            'status': 'running',
            'current_tick': market.current_tick,
            'current_price': market.market_data.current_price,
            'updates_count': 0
        }
        
        # Start background task
        task = asyncio.create_task(
            run_market_updates(game_id, request.duration, request.updateInterval)
        )
        active_game_tasks[game_id] = task
        
        return {
            "success": True,
            "message": "Market updates started in background",
            "gameId": game_id,
            "duration": request.duration,
            "updateInterval": request.updateInterval,
            "initialPrice": market.market_data.current_price,
            "currentTick": market.current_tick
        }
        
    except Exception as e:
        logger.error(f"Error starting market updates for {game_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/game/stop-market/{game_id}")
async def stop_market_updates(game_id: str):
    """
    Stop background market updates for a game.
    """
    if game_id not in active_game_tasks:
        return {
            "success": False,
            "error": "No active market updates found for this game"
        }
    
    task = active_game_tasks[game_id]
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Update game state
    if game_id in game_states:
        game_states[game_id]['status'] = 'stopped'
    
    logger.info(f"Stopped market updates for game {game_id}")
    
    return {
        "success": True,
        "message": f"Market updates stopped for game {game_id}"
    }


@app.get("/api/game/market-status/{game_id}")
async def get_market_status(game_id: str):
    """
    Check if market updates are running for a game and get current state.
    """
    is_active = game_id in active_game_tasks and not active_game_tasks[game_id].done()
    
    # Get market data from Redis
    market = Market.load_from_redis(game_id)
    
    response = {
        "gameId": game_id,
        "isActive": is_active,
        "marketExists": market is not None
    }
    
    if game_id in game_states:
        response.update(game_states[game_id])
    
    if market:
        response.update({
            "currentTick": market.current_tick,
            "currentPrice": market.market_data.current_price,
            "volatility": market.market_data.volatility,
            "dollarSupply": market.dollar_supply,
            "bcSupply": market.bc_supply,
            "priceHistoryLength": len(market.market_data.price_history),
            "eventTick": market.event_tick,
            "eventTime": market.event_time.isoformat(),
            "eventTitle": market.event_title,
            "eventTriggered": market.event_triggered
        })
    
    return response


@app.get("/api/game/market-data/{game_id}")
async def get_market_data(game_id: str, history_limit: int = 100):
    """
    Get current market data including price history.
    """
    from news_helper import get_random_generic_news, load_generic_news
    
    market = Market.load_from_redis(game_id)
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Get recent price history
    price_history = market.market_data.price_history[-history_limit:] if len(market.market_data.price_history) > history_limit else market.market_data.price_history
    
    # Get generic news if no event is triggered
    # Always provide generic news - it will be shown when event is not active
    generic_news = get_random_generic_news() if not market.event_triggered else get_random_generic_news()
    
    # Also provide all headlines for client-side rotation
    # Create a new list to ensure fresh data and avoid reference issues
    all_headlines = list(load_generic_news())  # Create new list instance
    
    return {
        "gameId": game_id,
        "currentTick": market.current_tick,
        "currentPrice": market.market_data.current_price,
        "volatility": market.market_data.volatility,
        "dollarSupply": market.dollar_supply,
        "bcSupply": market.bc_supply,
        "priceHistory": price_history,
        "startTime": market.start_time.isoformat(),
        "eventTick": market.event_tick,
        "eventTime": market.event_time.isoformat(),
        "eventTitle": market.event_title,
        "eventTriggered": market.event_triggered,
        "genericNews": generic_news,
        "allGenericNews": all_headlines  # All headlines for rotation
    }


@app.post("/api/game/buy-coins")
async def buy_coins(request: TradeRequest):
    """
    Execute a buy trade for a user.
    Retries until success if transaction fails.
    """
    if request.action != "buy":
        raise HTTPException(status_code=400, detail="Use sell-coins endpoint for sell trades")
    
    # Retry loop - keep trying until transaction succeeds
    max_retries = 100  # Prevent infinite loops
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Load market to get current price (reload each retry to get fresh price)
            market = Market.load_from_redis(request.gameId)
            if not market:
                raise HTTPException(status_code=404, detail="Market not found")
            
            current_price = market.market_data.current_price
            
            # Get user wallet from Redis (using existing front-end structure)
            r = get_redis_connection()
            game_data = r.hgetall(f"game:{request.gameId}")
            
            if not game_data:
                raise HTTPException(status_code=404, detail="Game not found")
            
            import json
            players = json.loads(game_data.get('players', '[]'))
            
            # Find the user
            user_data = None
            user_index = None
            for i, player in enumerate(players):
                if player['userId'] == request.userId:
                    user_data = player
                    user_index = i
                    break
            
            if not user_data:
                raise HTTPException(status_code=404, detail="User not found in game")
            
            # Calculate trade
            cost = request.amount * current_price
            
            # Check for sufficient funds - silently fail if insufficient (don't raise exception)
            if user_data['usd'] < cost:
                return {
                    "success": False,
                    "message": "Insufficient USD",
                    "newUsd": user_data.get('usd', user_data.get('usdBalance', 0)),
                    "newCoins": user_data.get('coins', user_data.get('coinBalance', 0))
                }
            
            # Execute trade - prevent negative balances
            user_data['usd'] = max(0.0, user_data['usd'] - cost)
            user_data['coins'] = max(0.0, user_data['coins'] + request.amount)
            user_data['lastInteractionT'] = datetime.now().isoformat()
            user_data['lastInteractionV'] = market.current_tick
            
            # Update market supplies
            market.dollar_supply += cost
            market.bc_supply -= request.amount
            market.save_to_redis()
            
            # Update user in Redis
            players[user_index] = user_data
            r.hset(f"game:{request.gameId}", "players", json.dumps(players))
            
            # NOTE: Removed interactions counter - using TransactionHistory instead
            # ⚠️ DO NOT write to 'interactions' field here - it's now an ARRAY maintained by TransactionHistory
            # The old code was overwriting the array with an integer, destroying all transaction history!
            
            # Record transaction in history
            TransactionHistory.add_transaction(request.gameId, {
                'type': 'buy',
                'actor': request.userId,
                'actor_name': user_data.get('userName', user_data.get('playerName', 'Unknown')),
                'amount': request.amount,
                'price': current_price,
                'total_cost': cost,
                'timestamp': datetime.now().isoformat(),
                'is_bot': False
            })
            
            logger.info(f"User {request.userId} bought {request.amount} BC for ${cost:.2f} (attempt {retry_count + 1})")
            
            return {
                "success": True,
                "action": "buy",
                "amount": request.amount,
                "cost": cost,
                "price": current_price,
                "newUsd": user_data['usd'],
                "newCoins": user_data['coins']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Error executing buy trade after {max_retries} retries: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            # Wait a short time before retrying (exponential backoff)
            import asyncio
            await asyncio.sleep(0.1 * retry_count)  # 0.1s, 0.2s, 0.3s, etc.
            logger.warning(f"Buy trade failed, retrying ({retry_count}/{max_retries}): {e}")
            continue


@app.post("/api/game/sell-coins")
async def sell_coins(request: TradeRequest):
    """
    Execute a sell trade for a user.
    Retries until success if transaction fails.
    If trying to sell more than available, sells all available coins.
    """
    if request.action != "sell":
        raise HTTPException(status_code=400, detail="Use buy-coins endpoint for buy trades")
    
    # Retry loop - keep trying until transaction succeeds
    max_retries = 100  # Prevent infinite loops
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Load market to get current price (reload each retry to get fresh price)
            market = Market.load_from_redis(request.gameId)
            if not market:
                raise HTTPException(status_code=404, detail="Market not found")
            
            current_price = market.market_data.current_price
            
            # Get user wallet from Redis
            r = get_redis_connection()
            game_data = r.hgetall(f"game:{request.gameId}")
            
            if not game_data:
                raise HTTPException(status_code=404, detail="Game not found")
            
            import json
            players = json.loads(game_data.get('players', '[]'))
            
            # Find the user (handle both userId and playerId fields)
            user_data = None
            user_index = None
            for i, player in enumerate(players):
                # Check both userId and playerId fields for compatibility
                player_id = player.get('userId') or player.get('playerId')
                if player_id == request.userId:
                    user_data = player
                    user_index = i
                    break
            
            if not user_data:
                raise HTTPException(status_code=404, detail="User not found in game")
            
            # Check balance (handle both field name conventions)
            user_coins = user_data.get('coins', user_data.get('coinBalance', 0))
            
            # If trying to sell more than available, sell all available coins
            actual_amount = min(request.amount, user_coins)
            
            if actual_amount <= 0:
                return {
                    "success": False,
                    "message": "No BC to sell",
                    "newUsd": user_data.get('usd', user_data.get('usdBalance', 0)),
                    "newCoins": user_data.get('coins', user_data.get('coinBalance', 0))
                }
            
            # Recalculate revenue with actual amount
            revenue = actual_amount * current_price
            
            # Execute trade (update both field name conventions) - prevent negative balances
            if 'coins' in user_data:
                user_data['coins'] = max(0.0, user_data['coins'] - actual_amount)
            if 'coinBalance' in user_data:
                user_data['coinBalance'] = max(0.0, user_data.get('coinBalance', 0) - actual_amount)
            
            if 'usd' in user_data:
                user_data['usd'] = max(0.0, user_data.get('usd', 0) + revenue)
            if 'usdBalance' in user_data:
                user_data['usdBalance'] = max(0.0, user_data.get('usdBalance', 0) + revenue)
            
            user_data['lastInteractionT'] = datetime.now().isoformat()
            user_data['lastInteractionV'] = market.current_tick
            user_data['lastInteractionTime'] = user_data['lastInteractionT']
            user_data['lastInteractionValue'] = actual_amount
            
            # Update market supplies (use actual_amount, not request.amount)
            market.dollar_supply -= revenue
            market.bc_supply += actual_amount
            market.save_to_redis()
            
            # Update user in Redis
            players[user_index] = user_data
            r.hset(f"game:{request.gameId}", "players", json.dumps(players))
            
            # NOTE: Removed interactions counter - using TransactionHistory instead
            # ⚠️ DO NOT write to 'interactions' field here - it's now an ARRAY maintained by TransactionHistory
            # The old code was overwriting the array with an integer, destroying all transaction history!
            
            # Record transaction in history (use actual_amount)
            TransactionHistory.add_transaction(request.gameId, {
                'type': 'sell',
                'actor': request.userId,
                'actor_name': user_data.get('userName', user_data.get('playerName', 'Unknown')),
                'amount': actual_amount,
                'price': current_price,
                'total_cost': revenue,
                'timestamp': datetime.now().isoformat(),
                'is_bot': False
            })
            
            logger.info(f"User {request.userId} sold {actual_amount} BC for ${revenue:.2f} (requested {request.amount}, attempt {retry_count + 1})")
            
            return {
                "success": True,
                "action": "sell",
                "amount": actual_amount,
                "revenue": revenue,
                "price": current_price,
                "newUsd": user_data.get('usd', user_data.get('usdBalance', 0)),
                "newCoins": user_data.get('coins', user_data.get('coinBalance', 0))
            }
            
        except HTTPException:
            raise
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Error executing sell trade after {max_retries} retries: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            # Wait a short time before retrying (exponential backoff)
            import asyncio
            await asyncio.sleep(0.1 * retry_count)  # 0.1s, 0.2s, 0.3s, etc.
            logger.warning(f"Sell trade failed, retrying ({retry_count}/{max_retries}): {e}")
            continue


@app.post("/api/bot/buy")
async def buy_bot(request: BotBuyRequest):
    """
    Purchase a minion for a user.
    """
    try:
        # Get user wallet from Redis
        r = get_redis_connection()
        game_data = r.hgetall(f"game:{request.gameId}")
        
        if not game_data:
            raise HTTPException(status_code=404, detail="Game not found")
        
        import json
        players = json.loads(game_data.get('players', '[]'))
        
        # Find the user (handle both userId and playerId fields)
        user_data = None
        user_index = None
        for i, player in enumerate(players):
            # Check both userId and playerId fields for compatibility
            player_id = player.get('userId') or player.get('playerId')
            if player_id == request.userId:
                user_data = player
                user_index = i
                break
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found in game")
        
        # Check if user has enough USD (handle both usd and usdBalance fields)
        user_usd = user_data.get('usd', user_data.get('usdBalance', 0))
        if user_usd < request.cost:
            raise HTTPException(status_code=400, detail="Insufficient USD")
        
        # Map front-end minion types to backend bot types
        bot_type_map = {
            'premade': 'random',
            'custom': 'custom',
            'hodler': 'mean_reversion',
            'scalper': 'momentum',
            'swing': 'momentum',
            'arbitrage': 'market_maker',
            'dip': 'mean_reversion',
            'momentum': 'momentum'
        }
        
        backend_bot_type = bot_type_map.get(request.botType, 'random')
        
        # Generate custom strategy code if minion type is custom
        custom_strategy_code = None
        if backend_bot_type == 'custom':
            if not request.customPrompt:
                raise HTTPException(status_code=400, detail="Custom prompt required for custom minion type")
            
            logger.info(f"Generating custom strategy for prompt: {request.customPrompt[:100]}...")
            try:
                custom_strategy_code = generate_custom_bot_strategy(request.customPrompt)
                logger.info(f"Generated custom strategy code ({len(custom_strategy_code)} chars)")
            except Exception as e:
                logger.error(f"Failed to generate custom strategy: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to generate custom strategy: {str(e)}")
        
        # Deduct cost from user FIRST (before minion creation) - prevent negative balances
        if 'usd' in user_data:
            user_data['usd'] = max(0.0, user_data['usd'] - request.cost)
        if 'usdBalance' in user_data:
            user_data['usdBalance'] = max(0.0, user_data['usdBalance'] - request.cost)
        
        # Add minion entry to user's bots list
        if 'bots' not in user_data:
            user_data['bots'] = []
        
        # Generate temporary minion ID for the entry
        import uuid
        bot_id = str(uuid.uuid4())
        
        # Use the display name if provided, otherwise fall back to bot type
        display_name = request.botName if request.botName else backend_bot_type
        
        user_data['bots'].append({
            'botId': bot_id,
            'botName': display_name
        })
        
        logger.info(f"After adding minion, user has {len(user_data['bots'])} minions: {user_data['bots']}")
        logger.info(f"User index: {user_index}, Total players: {len(players)}")
        
        # Update players in Redis FIRST
        players[user_index] = user_data
        players_json = json.dumps(players)
        logger.info(f"About to save. players[{user_index}]['bots'] = {players[user_index].get('bots', [])}")
        logger.info(f"Full players array: {players}")
        r.hset(f"game:{request.gameId}", "players", players_json)
        
        # Verify the save worked
        saved_data = r.hget(f"game:{request.gameId}", "players")
        saved_players = json.loads(saved_data) if saved_data else []
        logger.info(f"After save, Redis has {len(saved_players[0].get('bots', []))} minions for player 0")
        
        # NOW create the actual minion (this will use the bot_id we generated)
        # Call bot_operations directly but pass the bot_id we already created
        from bot import Bot
        # Allocate resources: 70% of purchase price as starting capital (increased from 50% for better bot performance)
        # This gives bots more resources to trade effectively
        bot_starting_capital = request.cost * 0.7
        bot = Bot(
            bot_id=bot_id,
            is_toggled=True,
            usd_given=bot_starting_capital,
            usd=bot_starting_capital,
            bc=0.0,
            bot_type=backend_bot_type,
            user_id=request.userId,
            custom_strategy_code=custom_strategy_code,
            bot_name=display_name
        )
        
        # Save minion to Redis
        bot.save_to_redis(request.gameId)
        
        # Start minion running in a separate thread
        import threading
        bot_thread = threading.Thread(
            target=bot.run,
            args=(request.gameId,),
            daemon=True,
            name=f"Bot-{bot_id}"
        )
        bot_thread.start()
        
        logger.info(f"Minion {bot_id} started for user {request.userId}")
        
        logger.info(f"User {request.userId} purchased minion {bot_id} for ${request.cost}")
        
        # Get minion details
        bot = Bot.load_from_redis(request.gameId, bot_id)
        bot_data = bot.to_dict() if bot else {}
        
        return {
            "success": True,
            "botId": bot_id,
            "botType": backend_bot_type,
            "cost": request.cost,
            "newUsd": user_data.get('usd', user_data.get('usdBalance', 0)),
            "bot": bot_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error buying minion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/toggle")
async def toggle_bot(request: BotToggleRequest):
    """
    Toggle a minion on/off.
    """
    try:
        success = await asyncio.to_thread(
            toggleBot,
            request.botId,
            request.gameId
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Minion not found")
        
        # Get minion details
        bot = Bot.load_from_redis(request.gameId, request.botId)
        if not bot:
            raise HTTPException(status_code=404, detail="Minion not found after toggle")
        
        logger.info(f"Minion {request.botId} toggled to {'ON' if bot.is_toggled else 'OFF'}")
        
        return {
            "success": True,
            "botId": request.botId,
            "isActive": bot.is_toggled,
            "bot": bot.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling minion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bot/list/{game_id}/{user_id}")
async def list_user_bots(game_id: str, user_id: str):
    """
    List all minions owned by a user in a game.
    """
    try:
        r = get_redis_connection()
        
        # Get all minions for the game
        bots_set_key = f"bots:{game_id}"
        bot_ids = r.smembers(bots_set_key)
        
        # Load user's minions
        user_bots = []
        for bot_id_bytes in bot_ids:
            bot_id = bot_id_bytes.decode('utf-8') if isinstance(bot_id_bytes, bytes) else bot_id_bytes
            bot = Bot.load_from_redis(game_id, bot_id)
            if bot:
                user_bots.append(bot.to_dict())
        
        return {
            "success": True,
            "gameId": game_id,
            "userId": user_id,
            "bots": user_bots
        }
        
    except Exception as e:
        logger.error(f"Error listing minions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/game/leaderboard/{game_id}")
async def get_wealth_leaderboard(game_id: str):
    """
    Get wealth leaderboard for all users in the game.
    Wealth = USD balance + (BananaCoin balance * current_price)
    
    Returns a sorted leaderboard by wealth (descending).
    """
    try:
        # Load market to get current price
        market = Market.load_from_redis(game_id)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        current_price = market.market_data.current_price
        
        # Get game data from Redis
        r = get_redis_connection()
        game_data = r.hgetall(f"game:{game_id}")
        
        if not game_data:
            raise HTTPException(status_code=404, detail="Game not found")
        
        import json
        players = json.loads(game_data.get('players', '[]'))
        
        if not players:
            raise HTTPException(status_code=404, detail="No players found in game")
        
        # Calculate wealth for each player (including minion balances)
        player_wealths = []
        bots_set_key = f"bots:{game_id}"
        bot_ids = r.smembers(bots_set_key)
        
        # Build a map of user_id -> list of bot_ids
        user_bots_map = {}
        for bot_id_bytes in bot_ids:
            bot_id = bot_id_bytes.decode('utf-8') if isinstance(bot_id_bytes, bytes) else bot_id_bytes
            bot = Bot.load_from_redis(game_id, bot_id)
            if bot and bot.user_id:
                if bot.user_id not in user_bots_map:
                    user_bots_map[bot.user_id] = []
                user_bots_map[bot.user_id].append(bot)
        
        for player in players:
            # Handle both field name conventions (userId/playerId, usd/usdBalance, coins/coinBalance)
            player_id = player.get('userId') or player.get('playerId')
            player_name = player.get('userName') or player.get('playerName', 'Unknown')
            
            # Get USD balance (handle both field names)
            usd_balance = float(player.get('usd', player.get('usdBalance', 0)))
            
            # Get BC balance (handle both field names)
            bc_balance = float(player.get('coins', player.get('coinBalance', 0)))
            
            # Add minion balances to player's total
            total_minion_usd = 0.0
            total_minion_bc = 0.0
            if player_id in user_bots_map:
                for bot in user_bots_map[player_id]:
                    total_minion_usd += bot.usd
                    total_minion_bc += bot.bc
            
            # Calculate total wealth: (player USD + minion USD) + ((player BC + minion BC) * current_price)
            total_usd = usd_balance + total_minion_usd
            total_bc = bc_balance + total_minion_bc
            wealth = total_usd + (total_bc * current_price)
            
            player_wealths.append({
                'userId': player_id,
                'userName': player_name,
                'usdBalance': total_usd,  # Include minion balances
                'coinBalance': total_bc,   # Include minion balances
                'wealth': wealth
            })
        
        # Sort by wealth (descending)
        player_wealths.sort(key=lambda x: x['wealth'], reverse=True)
        
        return {
            "success": True,
            "leaderboard": player_wealths
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wealth leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/{game_id}")
async def get_transactions(game_id: str, limit: int = 100, offset: int = 0):
    """
    Get transaction history for a game.
    """
    try:
        transactions = TransactionHistory.get_transactions(game_id, limit=limit, offset=offset)
        stats = TransactionHistory.get_transaction_stats(game_id)
        
        return {
            "success": True,
            "gameId": game_id,
            "transactions": transactions,
            "stats": stats,
            "count": len(transactions)
        }
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/{game_id}/user/{user_id}")
async def get_user_transactions(game_id: str, user_id: str, limit: int = 100):
    """
    Get transaction history for a specific user in a game.
    """
    try:
        transactions = TransactionHistory.get_user_transactions(game_id, user_id, limit=limit)
        
        return {
            "success": True,
            "gameId": game_id,
            "userId": user_id,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        logger.error(f"Error getting user transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/{game_id}/bots")
async def get_bot_transactions(game_id: str, limit: int = 100):
    """
    Get all bot transactions for a game.
    """
    try:
        transactions = TransactionHistory.get_bot_transactions(game_id, limit=limit)
        
        return {
            "success": True,
            "gameId": game_id,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        logger.error(f"Error getting bot transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/{game_id}/stats")
async def get_transaction_stats(game_id: str):
    """
    Get transaction statistics for a game.
    """
    try:
        stats = TransactionHistory.get_transaction_stats(game_id)
        
        return {
            "success": True,
            "gameId": game_id,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting transaction stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "activeGames": len(active_game_tasks),
        "runningTasks": sum(1 for task in active_game_tasks.values() if not task.done())
    }


@app.get("/")
async def root():
    """
    API information.
    """
    return {
        "name": "Banana Coin Trading API",
        "version": "1.0.0",
        "description": "Real-time trading game with background market updates",
        "endpoints": {
            "POST /api/game/start-market": "Start background market updates",
            "POST /api/game/stop-market/{game_id}": "Stop market updates",
            "GET /api/game/market-status/{game_id}": "Get market update status",
            "GET /api/game/market-data/{game_id}": "Get market data and price history",
            "POST /api/game/buy-coins": "Execute buy trade",
            "POST /api/game/sell-coins": "Execute sell trade",
            "GET /api/game/leaderboard/{game_id}": "Get wealth leaderboard (richest player)",
            "POST /api/bot/buy": "Purchase a minion",
            "POST /api/bot/toggle": "Toggle minion on/off",
            "GET /api/bot/list/{game_id}/{user_id}": "List user's minions",
            "GET /api/transactions/{game_id}": "Get transaction history",
            "GET /api/transactions/{game_id}/user/{user_id}": "Get user's transactions",
            "GET /api/transactions/{game_id}/bots": "Get bot transactions",
            "GET /api/transactions/{game_id}/stats": "Get transaction statistics",
            "GET /health": "Health check"
        }
    }


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("🍌 Banana Coin Trading API starting up...")
    logger.info("✅ API ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down API...")
    
    # Cancel all active game tasks
    for game_id, task in active_game_tasks.items():
        logger.info(f"Cancelling task for game {game_id}")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    logger.info("✅ API shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

