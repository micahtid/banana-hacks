from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from market import Market, MarketData
from user import User
from wallet import UserWallet
from bot import BotManager
from typing import Dict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Banana Coin API",
    description="API for managing Banana Coin trading games with bots",
    version="1.0.0"
)

# ============================================================================
# GAME STATE MANAGEMENT
# ============================================================================

class GameState:
    """Manages the state of a single game"""
    
    def __init__(self, game_id: str, market: Market, users: Dict[str, User], 
                 wallets: Dict[str, UserWallet], bot_manager: BotManager):
        self.game_id = game_id
        self.market = market
        self.users = users
        self.wallets = wallets
        self.bot_manager = bot_manager
        self.created_at = datetime.now()
        self.is_active = True

# Global game storage (in production, use Redis or database)
games: Dict[str, GameState] = {}

# ============================================================================
# MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/startGame")
async def start_game(gameID: str = Query(..., description="Game ID")):
    """
    Start a game with the given game ID.
    
    Args:
        gameID: String identifier for the game
    """
    try:
        logger.info(f"Starting game {gameID}")
        
        # Check if game already exists
        if gameID in games:
            logger.warning(f"Game {gameID} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Game {gameID} already exists"
            )
        
        # Create market with default settings
        market = Market(initial_price=1.0, game_id=gameID)
        logger.debug(f"Market created for game {gameID}")
        
        # Create empty users and wallets dicts
        users: Dict[str, User] = {}
        wallets: Dict[str, UserWallet] = {}
        
        # Create bot manager
        bot_manager = BotManager()
        
        # Create game state
        game_state = GameState(gameID, market, users, wallets, bot_manager)
        games[gameID] = game_state
        
        logger.info(f"Game {gameID} started successfully")
        
        return {
            "success": True,
            "gameID": gameID,
            "message": "Game started successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error starting game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start game"
        )

@app.post("/buy")
async def buy(
    userID: str = Query(..., description="User ID"),
    numBC: int = Query(..., gt=0, description="Number of BananaCoins to buy"),
    gameID: int = Query(..., description="Game ID")
):
    """
    Buy BananaCoins for a user.
    
    Args:
        userID: String identifier for the user
        numBC: Integer number of BananaCoins to buy
        gameID: Integer identifier for the game
    """
    game_id_str = str(gameID)
    
    if game_id_str not in games:
        logger.warning(f"Game {gameID} not found when buying")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {gameID} not found"
        )
    
    game_state = games[game_id_str]
    
    if userID not in game_state.users:
        logger.warning(f"User {userID} not found in game {gameID}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {userID} not found in game"
        )
    
    user = game_state.users[userID]
    market_data = game_state.market.market_data
    price = market_data.current_price
    
    try:
        success = user.buy_bc(numBC, price, market_data.current_tick)
        if not success:
            logger.warning(f"User {userID} insufficient USD for purchase of {numBC} at {price}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient USD for purchase"
            )
        
        # Update wallet to match user state
        wallet = game_state.wallets[userID]
        wallet.coins = user.coins
        wallet.usd = user.usd
        wallet.last_interaction_tick = market_data.current_tick
        
        logger.info(f"User {userID} bought {numBC} BC at {price}")
        
        return {
            "success": True,
            "action": "buy",
            "amount": numBC,
            "price": price,
            "new_balance": {
                "coins": user.coins,
                "usd": user.usd
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error executing buy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute buy"
        )

@app.post("/sell")
async def sell(
    userID: str = Query(..., description="User ID"),
    numBC: int = Query(..., gt=0, description="Number of BananaCoins to sell"),
    gameID: int = Query(..., description="Game ID")
):
    """
    Sell BananaCoins for a user.
    
    Args:
        userID: String identifier for the user
        numBC: Integer number of BananaCoins to sell
        gameID: Integer identifier for the game
    """
    game_id_str = str(gameID)
    
    if game_id_str not in games:
        logger.warning(f"Game {gameID} not found when selling")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {gameID} not found"
        )
    
    game_state = games[game_id_str]
    
    if userID not in game_state.users:
        logger.warning(f"User {userID} not found in game {gameID}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {userID} not found in game"
        )
    
    user = game_state.users[userID]
    market_data = game_state.market.market_data
    price = market_data.current_price
    
    try:
        success = user.sell_bc(numBC, price, market_data.current_tick)
        if not success:
            logger.warning(f"User {userID} insufficient BC for sale of {numBC}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient BC for sale"
            )
        
        # Update wallet to match user state
        wallet = game_state.wallets[userID]
        wallet.coins = user.coins
        wallet.usd = user.usd
        wallet.last_interaction_tick = market_data.current_tick
        
        logger.info(f"User {userID} sold {numBC} BC at {price}")
        
        return {
            "success": True,
            "action": "sell",
            "amount": numBC,
            "price": price,
            "new_balance": {
                "coins": user.coins,
                "usd": user.usd
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error executing sell: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute sell"
        )

@app.post("/buyBot")
async def buy_bot(
    botPriceBC: str = Query(..., description="Bot price in BananaCoins"),
    userID: int = Query(..., description="User ID")
):
    """
    Buy a bot for a user.
    
    Args:
        botPriceBC: String representation of bot price in BananaCoins
        userID: Integer identifier for the user
    """
    try:
        # Convert botPriceBC string to float
        bot_price = float(botPriceBC)
        user_id_str = str(userID)
        
        # Find the game and user
        game_state = None
        game_id = None
        
        for gid, gs in games.items():
            if user_id_str in gs.users:
                game_state = gs
                game_id = gid
                break
        
        if game_state is None:
            logger.warning(f"User {userID} not found in any game")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {userID} not found in any game"
            )
        
        user = game_state.users[user_id_str]
        market_data = game_state.market.market_data
        
        # Check if user has enough BC to buy the bot
        if user.coins < bot_price:
            logger.warning(f"User {userID} insufficient BC to buy bot (price: {bot_price})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient BC to buy bot"
            )
        
        # Deduct bot price from user's BC
        user.coins -= bot_price
        user._update_interaction(market_data.current_tick)
        
        # Update wallet
        wallet = game_state.wallets[user_id_str]
        wallet.coins = user.coins
        wallet.last_interaction_tick = market_data.current_tick
        
        logger.info(f"User {userID} bought bot for {bot_price} BC")
        
        return {
            "success": True,
            "message": "Bot purchased successfully",
            "bot_price": bot_price,
            "new_balance": {
                "coins": user.coins,
                "usd": user.usd
            }
        }
    except ValueError as e:
        logger.error(f"Invalid botPriceBC value: {botPriceBC}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid botPriceBC: {botPriceBC}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error buying bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to buy bot"
        )

@app.post("/toggleBot")
async def toggle_bot(botID: str = Query(..., description="Bot ID")):
    """
    Toggle a bot on/off.
    
    Args:
        botID: String identifier for the bot
    """
    try:
        # Find the bot across all games
        bot_found = False
        bot = None
        
        for game_state in games.values():
            bot = game_state.bot_manager.get_bot(botID)
            if bot is not None:
                bot_found = True
                break
        
        if not bot_found:
            logger.warning(f"Bot {botID} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bot {botID} not found"
            )
        
        # Toggle bot active state
        bot.is_active = not bot.is_active
        new_state = "active" if bot.is_active else "inactive"
        
        logger.info(f"Bot {botID} toggled to {new_state}")
        
        return {
            "success": True,
            "botID": botID,
            "is_active": bot.is_active,
            "message": f"Bot is now {new_state}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error toggling bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle bot"
        )
