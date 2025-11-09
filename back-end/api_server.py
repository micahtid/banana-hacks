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
from bot import Bot
from bot_operations import buyBot, toggleBot
from redis_helper import get_redis_connection

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
    customPrompt: Optional[str] = None

# ============================================================================
# BACKGROUND TASK: MARKET UPDATES
# ============================================================================

async def run_market_updates(game_id: str, duration: int, update_interval: float):
    """
    Background task that updates the market every `update_interval` seconds
    for the specified duration.
    """
    start_time = time.time()
    end_time = start_time + duration
    update_count = 0
    
    logger.info(f"🎮 Starting market updates for game {game_id} - Duration: {duration}s")
    
    try:
        while time.time() < end_time:
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
            
            # Wait for next update interval
            await asyncio.sleep(update_interval)
        
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
                game_id=game_id
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
            "priceHistoryLength": len(market.market_data.price_history)
        })
    
    return response


@app.get("/api/game/market-data/{game_id}")
async def get_market_data(game_id: str, history_limit: int = 100):
    """
    Get current market data including price history.
    """
    market = Market.load_from_redis(game_id)
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Get recent price history
    price_history = market.market_data.price_history[-history_limit:] if len(market.market_data.price_history) > history_limit else market.market_data.price_history
    
    return {
        "gameId": game_id,
        "currentTick": market.current_tick,
        "currentPrice": market.market_data.current_price,
        "volatility": market.market_data.volatility,
        "dollarSupply": market.dollar_supply,
        "bcSupply": market.bc_supply,
        "priceHistory": price_history,
        "startTime": market.start_time.isoformat()
    }


@app.post("/api/game/buy-coins")
async def buy_coins(request: TradeRequest):
    """
    Execute a buy trade for a user.
    """
    if request.action != "buy":
        raise HTTPException(status_code=400, detail="Use sell-coins endpoint for sell trades")
    
    # Load market to get current price
    market = Market.load_from_redis(request.gameId)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    current_price = market.market_data.current_price
    
    # Get user wallet from Redis (using existing front-end structure)
    try:
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
        
        if user_data['usd'] < cost:
            raise HTTPException(status_code=400, detail="Insufficient USD")
        
        # Execute trade
        user_data['usd'] -= cost
        user_data['coins'] += request.amount
        user_data['lastInteractionT'] = datetime.now().isoformat()
        user_data['lastInteractionV'] = market.current_tick
        
        # Update market supplies
        market.dollar_supply += cost
        market.bc_supply -= request.amount
        market.save_to_redis()
        
        # Update user in Redis
        players[user_index] = user_data
        r.hset(f"game:{request.gameId}", "players", json.dumps(players))
        
        # Update interactions counter
        interactions = int(game_data.get('interactions', 0))
        r.hset(f"game:{request.gameId}", "interactions", interactions + 1)
        
        logger.info(f"User {request.userId} bought {request.amount} BC for ${cost:.2f}")
        
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
        logger.error(f"Error executing buy trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/game/sell-coins")
async def sell_coins(request: TradeRequest):
    """
    Execute a sell trade for a user.
    """
    if request.action != "sell":
        raise HTTPException(status_code=400, detail="Use buy-coins endpoint for buy trades")
    
    # Load market to get current price
    market = Market.load_from_redis(request.gameId)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    current_price = market.market_data.current_price
    
    # Get user wallet from Redis
    try:
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
        revenue = request.amount * current_price
        
        if user_data['coins'] < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient BC")
        
        # Execute trade
        user_data['coins'] -= request.amount
        user_data['usd'] += revenue
        user_data['lastInteractionT'] = datetime.now().isoformat()
        user_data['lastInteractionV'] = market.current_tick
        
        # Update market supplies
        market.dollar_supply -= revenue
        market.bc_supply += request.amount
        market.save_to_redis()
        
        # Update user in Redis
        players[user_index] = user_data
        r.hset(f"game:{request.gameId}", "players", json.dumps(players))
        
        # Update interactions counter
        interactions = int(game_data.get('interactions', 0))
        r.hset(f"game:{request.gameId}", "interactions", interactions + 1)
        
        logger.info(f"User {request.userId} sold {request.amount} BC for ${revenue:.2f}")
        
        return {
            "success": True,
            "action": "sell",
            "amount": request.amount,
            "revenue": revenue,
            "price": current_price,
            "newUsd": user_data['usd'],
            "newCoins": user_data['coins']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing sell trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/buy")
async def buy_bot(request: BotBuyRequest):
    """
    Purchase a bot for a user.
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
        
        # Map front-end bot types to backend bot types
        bot_type_map = {
            'premade': 'random',
            'custom': 'random',
            'hodler': 'mean_reversion',
            'scalper': 'momentum',
            'swing': 'momentum',
            'arbitrage': 'market_maker',
            'dip': 'mean_reversion',
            'momentum': 'momentum'
        }
        
        backend_bot_type = bot_type_map.get(request.botType, 'random')
        
        # Deduct cost from user FIRST (before bot creation)
        if 'usd' in user_data:
            user_data['usd'] -= request.cost
        if 'usdBalance' in user_data:
            user_data['usdBalance'] -= request.cost
        
        # Add bot entry to user's bots list
        if 'bots' not in user_data:
            user_data['bots'] = []
        
        # Generate temporary bot ID for the entry
        import uuid
        bot_id = str(uuid.uuid4())
        
        user_data['bots'].append({
            'botId': bot_id,
            'botName': backend_bot_type
        })
        
        logger.info(f"After adding bot, user has {len(user_data['bots'])} bots: {user_data['bots']}")
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
        logger.info(f"After save, Redis has {len(saved_players[0].get('bots', []))} bots for player 0")
        
        # NOW create the actual bot (this will use the bot_id we generated)
        # Call bot_operations directly but pass the bot_id we already created
        from bot import Bot
        bot = Bot(
            bot_id=bot_id,
            is_toggled=True,
            usd_given=request.cost * 0.2,
            usd=request.cost * 0.2,
            bc=0.0,
            bot_type=backend_bot_type,
            user_id=request.userId
        )
        
        # Save bot to Redis
        bot.save_to_redis(request.gameId)
        
        # Start bot running in a separate thread
        import threading
        bot_thread = threading.Thread(
            target=bot.run,
            args=(request.gameId,),
            daemon=True,
            name=f"Bot-{bot_id}"
        )
        bot_thread.start()
        
        logger.info(f"Bot {bot_id} started for user {request.userId}")
        
        logger.info(f"User {request.userId} purchased bot {bot_id} for ${request.cost}")
        
        # Get bot details
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
        logger.error(f"Error buying bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/toggle")
async def toggle_bot(request: BotToggleRequest):
    """
    Toggle a bot on/off.
    """
    try:
        success = await asyncio.to_thread(
            toggleBot,
            request.botId,
            request.gameId
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get bot details
        bot = Bot.load_from_redis(request.gameId, request.botId)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found after toggle")
        
        logger.info(f"Bot {request.botId} toggled to {'ON' if bot.is_toggled else 'OFF'}")
        
        return {
            "success": True,
            "botId": request.botId,
            "isActive": bot.is_toggled,
            "bot": bot.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bot/list/{game_id}/{user_id}")
async def list_user_bots(game_id: str, user_id: str):
    """
    List all bots owned by a user in a game.
    """
    try:
        r = get_redis_connection()
        
        # Get all bots for the game
        bots_set_key = f"bots:{game_id}"
        bot_ids = r.smembers(bots_set_key)
        
        # Load user's bots
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
        logger.error(f"Error listing bots: {e}")
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
        
        # Calculate wealth for each player
        player_wealths = []
        for player in players:
            # Handle both field name conventions (userId/playerId, usd/usdBalance, coins/coinBalance)
            player_id = player.get('userId') or player.get('playerId')
            player_name = player.get('userName') or player.get('playerName', 'Unknown')
            
            # Get USD balance (handle both field names)
            usd_balance = float(player.get('usd', player.get('usdBalance', 0)))
            
            # Get BC balance (handle both field names)
            bc_balance = float(player.get('coins', player.get('coinBalance', 0)))
            
            # Calculate wealth: USD + (BC * current_price)
            wealth = usd_balance + (bc_balance * current_price)
            
            player_wealths.append({
                'userId': player_id,
                'userName': player_name,
                'usdBalance': usd_balance,
                'coinBalance': bc_balance,
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
            "POST /api/bot/buy": "Purchase a bot",
            "POST /api/bot/toggle": "Toggle bot on/off",
            "GET /api/bot/list/{game_id}/{user_id}": "List user's bots",
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

