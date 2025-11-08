from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from market import Market, MarketData
from user import User
from wallet import UserWallet
from bot import BotManager
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
import time
import uuid
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
# REQUEST/RESPONSE MODELS
# ============================================================================

class GameInitRequest(BaseModel):
    duration: int = Field(..., gt=0, description="Game duration in seconds")
    userIDs: List[str] = Field(..., min_items=1, description="List of user IDs to participate")
    userNames: Optional[List[str]] = Field(None, description="Optional list of user names")
    initial_price: float = Field(1.0, gt=0, description="Initial coin price")
    starting_coins: float = Field(1000.0, ge=0, description="Starting coin balance per user")
    starting_usd: float = Field(1000.0, ge=0, description="Starting USD balance per user")
    
    @validator('userNames')
    def validate_user_names(cls, v, values):
        """Ensure userNames length matches userIDs if provided"""
        if v is not None and 'userIDs' in values:
            if len(v) != len(values['userIDs']):
                raise ValueError("userNames length must match userIDs length")
        return v

class BotAddRequest(BaseModel):
    gameID: str = Field(..., description="Game ID to add bot to")
    userID: str = Field(..., description="User ID to add bot for")
    bot_type: str = Field(..., description="Bot type: random, momentum, mean_reversion, market_maker, hedger")
    bot_name: Optional[str] = Field(None, description="Optional custom bot name")
    parameters: Optional[Dict] = Field(None, description="Optional bot-specific parameters")
    
    @validator('bot_type')
    def validate_bot_type(cls, v):
        """Validate bot type is one of the allowed types"""
        allowed_types = ['random', 'momentum', 'mean_reversion', 'market_maker', 'hedger']
        if v.lower() not in allowed_types:
            raise ValueError(f"bot_type must be one of: {', '.join(allowed_types)}")
        return v.lower()

class TradeRequest(BaseModel):
    gameID: str = Field(..., description="Game ID")
    userID: str = Field(..., description="User ID executing the trade")
    action: str = Field(..., description="Trade action: 'buy' or 'sell'")
    amount: float = Field(..., gt=0, description="Amount of coins to trade")
    price: Optional[float] = Field(None, gt=0, description="Optional price (uses market price if None)")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action is buy or sell"""
        if v.lower() not in ['buy', 'sell']:
            raise ValueError("action must be 'buy' or 'sell'")
        return v.lower()

class GameStateResponse(BaseModel):
    gameID: str
    current_tick: int
    current_price: float
    volatility: float
    users: List[Dict]
    market_data: Dict

class GameInitResponse(BaseModel):
    gameID: str
    message: str
    market: Dict
    users: List[Dict]

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
    
    def to_dict(self) -> Dict:
        """Convert game state to dictionary for API response"""
        return {
            "gameID": self.game_id,
            "current_tick": self.market.current_tick,
            "current_price": self.market.market_data.current_price,
            "volatility": self.market.market_data.volatility,
            "users": [user.to_dict() for user in self.users.values()],
            "market_data": {
                "current_price": self.market.market_data.current_price,
                "current_tick": self.market.market_data.current_tick,
                "volatility": self.market.market_data.volatility,
                "price_history": self.market.market_data.price_history[-10:]  # Last 10 prices
            }
        }

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

@app.post("/startGame", response_model=GameInitResponse)
async def start_game(request: GameInitRequest):
    """Initialize a new game with users and market"""
    try:
        game_id = str(uuid.uuid4())
        
        # Create market with game_id for Redis storage
        market = Market(initial_price=request.initial_price, game_id=game_id)
        
        # Create users and wallets
        users: Dict[str, User] = {}
        wallets: Dict[str, UserWallet] = {}
        
        user_names = request.userNames if request.userNames else [f"User_{i+1}" for i in range(len(request.userIDs))]
        
        for i, user_id in enumerate(request.userIDs):
            user_name = user_names[i] if i < len(user_names) else f"User_{i+1}"
            
            # Create User
            user = User(
                user_id=user_id,
                user_name=user_name,
                coins=request.starting_coins,
                usd=request.starting_usd,
                last_interaction_v=0
            )
            users[user_id] = user
            
            # Create UserWallet for bot trading
            wallet = UserWallet(
                user_id=user_id,
                coins=request.starting_coins,
                usd=request.starting_usd,
                last_interaction_tick=0
            )
            wallets[user_id] = wallet
            
            # Add user to market
            market.addUser(user_id)
        
        # Create bot manager
        bot_manager = BotManager()
        
        # Create game state
        game_state = GameState(game_id, market, users, wallets, bot_manager)
        games[game_id] = game_state
        
        return GameInitResponse(
            gameID=game_id,
            message="Game started successfully",
            market={
                "current_price": market.market_data.current_price,
                "current_tick": market.market_data.current_tick,
                "volatility": market.market_data.volatility
            },
            users=[user.to_dict() for user in users.values()]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gameState/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """Get current state of a game"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_state = games[game_id]
    return GameStateResponse(**game_state.to_dict())

@app.post("/addBot")
async def add_bot(request: BotAddRequest):
    """Add a bot to a user in a game"""
    if request.gameID not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_state = games[request.gameID]
    
    if request.userID not in game_state.users:
        raise HTTPException(status_code=404, detail="User not found in game")
    
    # Get current market state
    market_data = game_state.market.market_data
    current_tick = market_data.current_tick
    current_price = market_data.current_price
    
    # Add bot to bot manager
    success, bot_id = game_state.bot_manager.add_bot_to_user(
        user_id=request.userID,
        bot_type=request.bot_type,
        current_tick=current_tick,
        current_price=current_price,
        parameters=request.parameters
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Invalid bot type: {request.bot_type}")
    
    # Add bot to user's bot list
    bot_name = request.bot_name or request.bot_type
    user = game_state.users[request.userID]
    user.add_bot(bot_id, bot_name)
    
    return {
        "success": True,
        "bot_id": bot_id,
        "bot_name": bot_name,
        "message": f"Bot '{bot_name}' added successfully"
    }

@app.post("/executeTrade")
async def execute_trade(request: TradeRequest):
    """Execute a manual trade for a user"""
    if request.gameID not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_state = games[request.gameID]
    
    if request.userID not in game_state.users:
        raise HTTPException(status_code=404, detail="User not found in game")
    
    user = game_state.users[request.userID]
    market_data = game_state.market.market_data
    price = request.price if request.price else market_data.current_price
    
    if request.action.lower() == "buy":
        success = user.buy_bc(request.amount, price, market_data.current_tick)
        if not success:
            raise HTTPException(status_code=400, detail="Insufficient USD for purchase")
    elif request.action.lower() == "sell":
        success = user.sell_bc(request.amount, price, market_data.current_tick)
        if not success:
            raise HTTPException(status_code=400, detail="Insufficient BC for sale")
    else:
        raise HTTPException(status_code=400, detail="Action must be 'buy' or 'sell'")
    
    # Update wallet to match user state
    wallet = game_state.wallets[request.userID]
    wallet.coins = user.coins
    wallet.usd = user.usd
    wallet.last_interaction_tick = market_data.current_tick
    
    return {
        "success": True,
        "action": request.action,
        "amount": request.amount,
        "price": price,
        "new_balance": {
            "coins": user.coins,
            "usd": user.usd
        }
    }

@app.post("/updateMarket/{game_id}")
async def update_market(game_id: str):
    """Update the market state (increment tick, update price, run bots)"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_state = games[game_id]
    
    # Update market
    game_state.market.updateMarket()
    market_data = game_state.market.market_data
    
    # Run all bots
    bot_results = game_state.bot_manager.run_all_bots(market_data, game_state.wallets)
    
    # Update user wallets from bot trades
    for result in bot_results:
        user_id = result['user_id']
        if user_id in game_state.users:
            user = game_state.users[user_id]
            wallet = game_state.wallets[user_id]
            # Sync user state with wallet
            user.coins = wallet.coins
            user.usd = wallet.usd
            user.last_interaction_v = wallet.last_interaction_tick
    
    return {
        "success": True,
        "current_tick": market_data.current_tick,
        "current_price": market_data.current_price,
        "volatility": market_data.volatility,
        "bot_trades_executed": len(bot_results)
    }

@app.get("/botPerformance/{game_id}/{user_id}")
async def get_bot_performance(game_id: str, user_id: str):
    """Get performance metrics for all bots of a user"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_state = games[game_id]
    
    if user_id not in game_state.users:
        raise HTTPException(status_code=404, detail="User not found in game")
    
    market_data = game_state.market.market_data
    wallets = game_state.wallets
    
    performance = game_state.bot_manager.get_all_bot_performance(market_data, wallets)
    
    # Filter to user's bots only
    user_bots = {bot_id: metrics for bot_id, metrics in performance.items() 
                 if game_state.bot_manager.get_bot(bot_id) and 
                 game_state.bot_manager.get_bot(bot_id).user_id == user_id}
    
    return {
        "user_id": user_id,
        "bots": user_bots
    }

@app.delete("/game/{game_id}")
async def delete_game(game_id: str):
    """Delete a game"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    del games[game_id]
    return {"success": True, "message": "Game deleted"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Banana Coin API",
        "version": "1.0.0",
        "endpoints": {
            "POST /startGame": "Initialize a new game",
            "GET /gameState/{game_id}": "Get game state",
            "POST /addBot": "Add a bot to a user",
            "POST /executeTrade": "Execute a manual trade",
            "POST /updateMarket/{game_id}": "Update market and run bots",
            "GET /botPerformance/{game_id}/{user_id}": "Get bot performance",
            "DELETE /game/{game_id}": "Delete a game"
        }
    }
    