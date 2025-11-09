import threading
from typing import Optional, Dict
import json
from bot import Bot
from redis_helper import get_redis_connection


# Global dictionary to track running bot threads
_running_bots: Dict[str, threading.Thread] = {}


def buyBot(user_id: str, game_id: str, bot_type: str = 'random', 
           initial_usd: float = 1000.0) -> Optional[str]:
    """
    Create a new bot for a user and start it running.
    
    Args:
        user_id: User ID who is buying the bot
        game_id: Game ID where the bot will operate
        bot_type: Type of bot strategy (random, momentum, mean_reversion, market_maker, hedger)
        initial_usd: Initial USD balance for the bot
    
    Returns:
        bot_id if successful, None otherwise
    """
    try:
        r = get_redis_connection()
        
        # Load game data from Redis
        game_key = f"game:{game_id}"
        if not r.exists(game_key):
            print(f"Game {game_id} not found in Redis")
            return None
        
        game_data = r.hgetall(game_key)
        
        # Parse players data
        players = json.loads(game_data.get('players', '[]'))
        user_found = False
        user_index = -1
        
        for i, player in enumerate(players):
            if player.get('userId') == user_id:
                user_found = True
                user_index = i
                break
        
        if not user_found:
            print(f"User {user_id} not found in game {game_id}")
            return None
        
        # Create new bot
        bot = Bot(
            bot_id=None,  # Will be auto-generated
            is_toggled=True,
            usd_given=initial_usd,
            usd=initial_usd,
            bc=0.0,
            bot_type=bot_type
        )
        
        bot_id = bot.bot_id
        
        # Append bot to user's bots list
        if 'bots' not in players[user_index]:
            players[user_index]['bots'] = []
        
        players[user_index]['bots'].append({
            'botId': bot_id,
            'botName': bot_type
        })
        
        # Save bot to Redis
        bot.save_to_redis(game_id)
        
        # Update game data in Redis
        r.hset(game_key, 'players', json.dumps(players))
        
        # Start bot running in a separate thread
        bot_thread = threading.Thread(
            target=bot.run,
            args=(game_id,),
            daemon=True,
            name=f"Bot-{bot_id}"
        )
        bot_thread.start()
        
        # Track running bot
        _running_bots[f"{game_id}:{bot_id}"] = bot_thread
        
        print(f"Bot {bot_id} created and started for user {user_id} in game {game_id}")
        return bot_id
        
    except Exception as e:
        print(f"Error in buyBot: {e}")
        import traceback
        traceback.print_exc()
        return None


def toggleBot(bot_id: str, game_id: str) -> bool:
    """
    Toggle a bot on/off. Updates Redis and ensures the bot stops trading when toggled off.
    
    Args:
        bot_id: Bot ID to toggle
        game_id: Game ID where the bot operates
    
    Returns:
        True if successful, False otherwise
    """
    try:
        r = get_redis_connection()
        
        # Load bot from Redis
        bot = Bot.load_from_redis(game_id, bot_id)
        if bot is None:
            print(f"Bot {bot_id} not found in game {game_id}")
            return False
        
        # Toggle the bot state
        bot.is_toggled = not bot.is_toggled
        
        # Save updated state to Redis
        bot.save_to_redis(game_id)
        
        # Update user's bot list in game data
        game_key = f"game:{game_id}"
        if r.exists(game_key):
            game_data = r.hgetall(game_key)
            players = json.loads(game_data.get('players', '[]'))
            
            for player in players:
                if 'bots' in player:
                    for bot_entry in player['bots']:
                        if bot_entry.get('botId') == bot_id:
                            # Update bot entry if needed (e.g., isActive field)
                            if 'isActive' not in bot_entry:
                                bot_entry['isActive'] = bot.is_toggled
                            else:
                                bot_entry['isActive'] = bot.is_toggled
                            break
            
            r.hset(game_key, 'players', json.dumps(players))
        
        print(f"Bot {bot_id} toggled to {'ON' if bot.is_toggled else 'OFF'}")
        return True
        
    except Exception as e:
        print(f"Error in toggleBot: {e}")
        import traceback
        traceback.print_exc()
        return False

