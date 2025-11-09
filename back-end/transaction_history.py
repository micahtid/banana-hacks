"""
Transaction History Management Module

Manages transaction history in Redis for tracking all trades (user and bot) with timestamps.
"""

import json
from typing import List, Dict, Optional
from datetime import datetime
from redis_helper import get_redis_connection


class TransactionHistory:
    """Manages transaction history for a game"""
    
    @staticmethod
    def add_transaction(game_id: str, transaction: Dict) -> bool:
        """
        Add a transaction to the game's transaction history
        
        Args:
            game_id: Game ID
            transaction: Transaction dict with keys:
                - type: 'buy' or 'sell'
                - actor: User ID or bot ID
                - actor_name: Display name
                - amount: Amount of BC traded
                - price: Price per BC at time of trade
                - total_cost: Total USD cost/revenue
                - timestamp: ISO format timestamp
                - is_bot: Boolean indicating if this is a bot transaction
        
        Returns:
            True if successful, False otherwise
        """
        try:
            r = get_redis_connection()
            
            # Add timestamp if not present
            if 'timestamp' not in transaction:
                transaction['timestamp'] = datetime.now().isoformat()
            
            # Add backward compatibility fields
            if 'actor_name' in transaction and 'name' not in transaction:
                transaction['name'] = transaction['actor_name']
            if 'amount' in transaction and 'value' not in transaction:
                transaction['value'] = int(transaction['amount'] * 100)  # Convert to cents
            
            # Store in Redis list (most recent first)
            tx_key = f"transactions:{game_id}"
            r.lpush(tx_key, json.dumps(transaction))
            
            # Set expiration to ensure transactions persist for the entire game period
            # 90 days is more than sufficient for any game duration
            r.expire(tx_key, 90 * 24 * 60 * 60)
            
            # Also update the legacy interactions format for backward compatibility
            TransactionHistory._update_interactions(game_id, transaction)
            
            return True
            
        except Exception as e:
            print(f"Error adding transaction to history: {e}")
            return False
    
    @staticmethod
    def _update_interactions(game_id: str, transaction: Dict):
        """Update the legacy interactions format in game data"""
        try:
            r = get_redis_connection()
            game_key = f"game:{game_id}"
            
            # Get current interactions (create empty list if game doesn't exist)
            interactions = []
            if r.exists(game_key):
                game_data = r.hgetall(game_key)
                if 'interactions' in game_data:
                    try:
                        interactions_str = game_data['interactions']
                        if isinstance(interactions_str, bytes):
                            interactions_str = interactions_str.decode('utf-8')
                        interactions = json.loads(interactions_str)
                    except:
                        interactions = []
            
            # Add new interaction in legacy format with ALL required fields
            new_interaction = {
                'name': transaction.get('actor_name', transaction.get('name', 'Unknown')),
                'type': transaction['type'],
                'value': int(transaction.get('amount', 0) * 100),  # Store as cents
                'interactionName': transaction.get('actor_name', transaction.get('name', 'Unknown')),
                'interactionDescription': f"{transaction['type'].upper()} {transaction.get('amount', 0):.2f} BC @ ${transaction.get('price', 0):.2f}"
            }
            
            interactions.append(new_interaction)
            
            # Save back to Redis (create game if it doesn't exist)
            r.hset(game_key, 'interactions', json.dumps(interactions))
            
            # Ensure game has basic fields if it's new
            if not r.hexists(game_key, 'gameId'):
                r.hset(game_key, 'gameId', game_id)
            
        except Exception as e:
            print(f"Error updating interactions: {e}")
    
    @staticmethod
    def get_transactions(game_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get transaction history for a game
        
        Args:
            game_id: Game ID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip (for pagination)
        
        Returns:
            List of transaction dictionaries, most recent first
        """
        try:
            r = get_redis_connection()
            tx_key = f"transactions:{game_id}"
            
            if not r.exists(tx_key):
                return []
            
            # Get transactions from Redis list (already ordered most recent first)
            end_idx = offset + limit - 1
            transactions_json = r.lrange(tx_key, offset, end_idx)
            
            transactions = []
            for tx_json in transactions_json:
                if isinstance(tx_json, bytes):
                    tx_json = tx_json.decode('utf-8')
                tx = json.loads(tx_json)
                
                # Add backward compatibility fields for front-end
                if 'actor_name' in tx and 'name' not in tx:
                    tx['name'] = tx['actor_name']
                if 'amount' in tx and 'value' not in tx:
                    tx['value'] = int(tx['amount'] * 100)  # Convert to cents
                
                transactions.append(tx)
            
            return transactions
            
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []
    
    @staticmethod
    def get_user_transactions(game_id: str, user_id: str, limit: int = 100) -> List[Dict]:
        """
        Get transaction history for a specific user
        
        Args:
            game_id: Game ID
            user_id: User ID to filter by
            limit: Maximum number of transactions to return
        
        Returns:
            List of transaction dictionaries for this user, most recent first
        """
        all_transactions = TransactionHistory.get_transactions(game_id, limit=1000)  # Already has backward compat fields
        user_transactions = [tx for tx in all_transactions if tx.get('actor') == user_id]
        return user_transactions[:limit]
    
    @staticmethod
    def get_bot_transactions(game_id: str, limit: int = 100) -> List[Dict]:
        """
        Get all bot transactions for a game
        
        Args:
            game_id: Game ID
            limit: Maximum number of transactions to return
        
        Returns:
            List of bot transaction dictionaries, most recent first
        """
        all_transactions = TransactionHistory.get_transactions(game_id, limit=1000)  # Already has backward compat fields
        bot_transactions = [tx for tx in all_transactions if tx.get('is_bot', False)]
        return bot_transactions[:limit]
    
    @staticmethod
    def get_transaction_stats(game_id: str) -> Dict:
        """
        Get statistics about transactions in a game
        
        Args:
            game_id: Game ID
        
        Returns:
            Dictionary with transaction statistics
        """
        try:
            r = get_redis_connection()
            tx_key = f"transactions:{game_id}"
            
            total_count = r.llen(tx_key) if r.exists(tx_key) else 0
            
            # Get all transactions to calculate stats
            transactions = TransactionHistory.get_transactions(game_id, limit=total_count)
            
            stats = {
                'total_transactions': total_count,
                'buy_count': sum(1 for tx in transactions if tx['type'] == 'buy'),
                'sell_count': sum(1 for tx in transactions if tx['type'] == 'sell'),
                'bot_transactions': sum(1 for tx in transactions if tx.get('is_bot', False)),
                'user_transactions': sum(1 for tx in transactions if not tx.get('is_bot', False)),
                'total_volume': sum(tx['amount'] for tx in transactions),
                'total_value': sum(tx['total_cost'] for tx in transactions)
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting transaction stats: {e}")
            return {
                'total_transactions': 0,
                'buy_count': 0,
                'sell_count': 0,
                'bot_transactions': 0,
                'user_transactions': 0,
                'total_volume': 0.0,
                'total_value': 0.0
            }
    
    @staticmethod
    def clear_transactions(game_id: str) -> bool:
        """
        Clear all transactions for a game (use with caution!)
        
        Args:
            game_id: Game ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            r = get_redis_connection()
            tx_key = f"transactions:{game_id}"
            r.delete(tx_key)
            return True
        except Exception as e:
            print(f"Error clearing transactions: {e}")
            return False

