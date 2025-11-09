"""
Market Events System for BananaCoin
Handles random market events that affect coin prices throughout the game.
Events are themed around bananas and stored in Redis.
"""

import random
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from scipy.interpolate import CubicSpline
from redis_helper import get_redis_connection


@dataclass
class MarketEvent:
    """Represents a market event that affects BananaCoin price"""
    event_id: str
    event_type: str  # 'positive', 'negative', 'neutral'
    name: str
    description: str
    duration: int  # How many ticks the event lasts (0 = instant)
    tick_occurred: int  # Tick when event occurred
    severity: str  # 'minor', 'moderate', 'major', 'extreme'
    impact: float  # Price multiplier (e.g., 1.15 = +15% increase)

    '''
    MODIFY THE FOLLOWING TO ACCESS 3 FUTURE POINTS OF COINS!
    '''

    spline_points: Optional[List[Tuple[float, float]]] = None
    _spline: Optional[CubicSpline] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Initialize spline once event is created."""
        self._build_spline()
    

    def _build_spline(self):
        """Construct a smooth cubic spline curve for the event."""
        # For instant events (duration=0), no spline needed
        if self.duration == 0:
            self._spline = None
            return
        
        duration = max(self.duration, 1)
        peak_impact = self.impact
        
        # Default symmetric curve: start at 1.0 → peak → return to 1.0
        self.spline_points = [
            (0, 1.0),
            (duration / 2, peak_impact),
            (duration, 1.0)
        ]
        
        x = np.array([p[0] for p in self.spline_points])
        y = np.array([p[1] for p in self.spline_points])
        self._spline = CubicSpline(x, y, bc_type='natural')
    
    def get_dynamic_impact(self, current_tick: int) -> float:
        """
        Compute the current price multiplier for this tick.
        
        Args:
            current_tick: Current game tick
            
        Returns:
            Price multiplier for this tick
        """
        # For instant events, return the impact directly
        if self.duration == 0:
            return self.impact
        
        # For duration events, use the spline
        if self._spline is None:
            self._build_spline()
            if self._spline is None:
                return self.impact
        
        ticks_elapsed = current_tick - self.tick_occurred
        duration = max(self.duration, 1)
        t = np.clip(ticks_elapsed, 0, duration)
        impact = float(self._spline(t))
        
        return max(0.01, impact)  # prevent negative or zero prices
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary for Redis storage"""
        result = {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'name': self.name,
            'description': self.description,
            'duration': str(self.duration),
            'tick_occurred': str(self.tick_occurred),
            'severity': self.severity,
            'impact': str(self.impact)
        }
        if self.spline_points is not None:
            # Serialize spline_points as JSON string
            result['spline_points'] = json.dumps(self.spline_points)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MarketEvent':
        """Create event from dictionary loaded from Redis"""
        spline_points = None
        if 'spline_points' in data and data['spline_points']:
            try:
                spline_points = json.loads(data['spline_points'])
            except (json.JSONDecodeError, TypeError):
                spline_points = None
        
        event = cls(
            event_id=data.get('event_id', ''),
            event_type=data.get('event_type', 'neutral'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            duration=int(data.get('duration', 0)),
            tick_occurred=int(data.get('tick_occurred', 0)),
            severity=data.get('severity', 'minor'),
            impact=float(data.get('impact', 1.0)),
            spline_points=spline_points
        )
        # Spline is automatically built in __post_init__
        return event


class MarketEventSystem:
    """
    Manages random market events for BananaCoin games.
    Events are stored in Redis and affect market prices.
    """
    
    # Event definitions - Banana-themed market events
    EVENT_TEMPLATES = [
        # POSITIVE EVENTS (Price Appreciation)
        {
            'type': 'positive',
            'name': 'Bumper Banana Harvest',
            'description': 'Perfect weather conditions lead to a record-breaking banana harvest!',
            'impact_range': (1.10, 1.25),  # +10% to +25%
            'duration': 0,
            'severity': 'major',
            'probability_weight': 15
        },
        {
            'type': 'positive',
            'name': 'Celebrity Banana Endorsement',
            'description': 'A famous influencer promotes BananaCoin on social media!',
            'impact_range': (1.05, 1.15),  # +5% to +15%
            'duration': 3,  # Lasts 3 ticks
            'severity': 'moderate',
            'probability_weight': 20
        },
        {
            'type': 'positive',
            'name': 'Major Retailer Adoption',
            'description': 'A major grocery chain starts accepting BananaCoin!',
            'impact_range': (1.12, 1.20),  # +12% to +20%
            'duration': 0,
            'severity': 'major',
            'probability_weight': 10
        },
        {
            'type': 'positive',
            'name': 'Banana Shortage Creates Demand',
            'description': 'Global banana supply shortage increases demand for BananaCoin!',
            'impact_range': (1.08, 1.18),  # +8% to +18%
            'duration': 5,  # Lasts 5 ticks
            'severity': 'moderate',
            'probability_weight': 12
        },
        {
            'type': 'positive',
            'name': 'New Banana-Based Product Launch',
            'description': 'Revolutionary banana-based product creates market excitement!',
            'impact_range': (1.06, 1.14),  # +6% to +14%
            'duration': 2,
            'severity': 'moderate',
            'probability_weight': 18
        },
        {
            'type': 'positive',
            'name': 'BananaCoin Listed on Major Exchange',
            'description': 'BananaCoin gets listed on a major cryptocurrency exchange!',
            'impact_range': (1.15, 1.30),  # +15% to +30%
            'duration': 0,
            'severity': 'extreme',
            'probability_weight': 5
        },
        
        # NEGATIVE EVENTS (Price Depreciation)
        {
            'type': 'negative',
            'name': 'Banana Ship Sinks',
            'description': 'A cargo ship carrying bananas sinks, causing supply concerns!',
            'impact_range': (0.80, 0.90),  # -20% to -10%
            'duration': 0,
            'severity': 'major',
            'probability_weight': 12
        },
        {
            'type': 'negative',
            'name': 'Fungus Outbreak in Plantations',
            'description': 'Panama disease spreads through banana plantations!',
            'impact_range': (0.85, 0.95),  # -15% to -5%
            'duration': 4,  # Lasts 4 ticks
            'severity': 'moderate',
            'probability_weight': 15
        },
        {
            'type': 'negative',
            'name': 'Banana Import Ban',
            'description': 'A major country bans banana imports, reducing demand!',
            'impact_range': (0.88, 0.95),  # -12% to -5%
            'duration': 0,
            'severity': 'moderate',
            'probability_weight': 10
        },
        {
            'type': 'negative',
            'name': 'Negative Health Study',
            'description': 'A controversial study questions banana health benefits!',
            'impact_range': (0.90, 0.97),  # -10% to -3%
            'duration': 2,
            'severity': 'minor',
            'probability_weight': 18
        },
        {
            'type': 'negative',
            'name': 'BananaCoin Security Breach',
            'description': 'Security concerns arise in the BananaCoin network!',
            'impact_range': (0.75, 0.85),  # -25% to -15%
            'duration': 0,
            'severity': 'extreme',
            'probability_weight': 3
        },
        {
            'type': 'negative',
            'name': 'Overproduction Crisis',
            'description': 'Massive banana overproduction floods the market!',
            'impact_range': (0.85, 0.92),  # -15% to -8%
            'duration': 3,
            'severity': 'moderate',
            'probability_weight': 14
        },
        {
            'type': 'negative',
            'name': 'Banana Tariff Increase',
            'description': 'New tariffs make bananas more expensive, reducing demand!',
            'impact_range': (0.88, 0.94),  # -12% to -6%
            'duration': 0,
            'severity': 'minor',
            'probability_weight': 12
        },
        
        # NEUTRAL/MIXED EVENTS
        {
            'type': 'neutral',
            'name': 'Banana Festival Announcement',
            'description': 'Annual banana festival creates temporary market volatility!',
            'impact_range': (0.95, 1.05),  # -5% to +5% (volatile)
            'duration': 1,
            'severity': 'minor',
            'probability_weight': 20
        },
        {
            'type': 'neutral',
            'name': 'Banana Research Breakthrough',
            'description': 'New banana research creates mixed market sentiment!',
            'impact_range': (0.98, 1.02),  # -2% to +2%
            'duration': 0,
            'severity': 'minor',
            'probability_weight': 25
        }
    ]
    
    def __init__(self, game_id: str):
        """
        Initialize event system for a game
        
        Args:
            game_id: Game identifier
        """
        self.game_id = game_id
        self._total_probability_weight = sum(
            event['probability_weight'] for event in self.EVENT_TEMPLATES
        )
    
    def check_for_event(self, current_tick: int, base_probability: float = 0.03) -> Optional[MarketEvent]:
        """
        Check if a random event should occur at this tick.
        
        Args:
            current_tick: Current game tick
            base_probability: Base probability of any event occurring (default: 3%)
        
        Returns:
            MarketEvent if event occurs, None otherwise
        """
        # Check if event should trigger
        if random.random() > base_probability:
            return None
        
        # Check if there's already an active event
        active_events = self.get_active_events(current_tick)
        if active_events:
            # Reduce probability if events are already active
            return None
        
        # Select random event based on weighted probability
        event_template = self._select_random_event()
        
        # Generate impact within range
        impact = random.uniform(*event_template['impact_range'])
        
        # Create event
        event_id = f"event_{self.game_id}_{current_tick}_{random.randint(1000, 9999)}"
        event = MarketEvent(
            event_id=event_id,
            event_type=event_template['type'],
            name=event_template['name'],
            description=event_template['description'],
            impact=impact,
            duration=event_template['duration'],
            tick_occurred=current_tick,
            severity=event_template['severity']
        )
        
        # Save to Redis
        self._save_event_to_redis(event)
        
        return event
    
    def _select_random_event(self) -> Dict:
        """Select a random event template based on weighted probability"""
        rand = random.uniform(0, self._total_probability_weight)
        cumulative = 0
        
        for event_template in self.EVENT_TEMPLATES:
            cumulative += event_template['probability_weight']
            if rand <= cumulative:
                return event_template
        
        # Fallback (shouldn't happen)
        return self.EVENT_TEMPLATES[0]
    
    def get_active_events(self, current_tick: int) -> List[MarketEvent]:
        """
        Get all currently active events for the game.
        
        Args:
            current_tick: Current game tick
        
        Returns:
            List of active MarketEvent objects
        """
        try:
            r = get_redis_connection()
            events_key = f"events:{self.game_id}"
            
            if not r.exists(events_key):
                return []
            
            # Get all event IDs
            event_ids = r.smembers(events_key)
            active_events = []
            
            for event_id in event_ids:
                event_key = f"event:{self.game_id}:{event_id}"
                if r.exists(event_key):
                    event_data = r.hgetall(event_key)
                    event = MarketEvent.from_dict(event_data)
                    
                    # Check if event is still active
                    ticks_elapsed = current_tick - event.tick_occurred
                    if event.duration == 0:
                        # Instant event - only active on the tick it occurred
                        if ticks_elapsed == 0:
                            active_events.append(event)
                    else:
                        # Duration event - active for duration ticks
                        if 0 <= ticks_elapsed < event.duration:
                            active_events.append(event)
            
            return active_events
            
        except Exception as e:
            print(f"Error getting active events: {e}")
            return []
    
    def get_all_events(self) -> List[MarketEvent]:
        """
        Get all events that have occurred in this game (active and past).
        
        Returns:
            List of all MarketEvent objects
        """
        try:
            r = get_redis_connection()
            events_key = f"events:{self.game_id}"
            
            if not r.exists(events_key):
                return []
            
            event_ids = r.smembers(events_key)
            all_events = []
            
            for event_id in event_ids:
                event_key = f"event:{self.game_id}:{event_id}"
                if r.exists(event_key):
                    event_data = r.hgetall(event_key)
                    event = MarketEvent.from_dict(event_data)
                    all_events.append(event)
            
            # Sort by tick_occurred (most recent first)
            all_events.sort(key=lambda e: e.tick_occurred, reverse=True)
            return all_events
            
        except Exception as e:
            print(f"Error getting all events: {e}")
            return []
    
    def calculate_price_impact(self, current_tick: int, base_price: float) -> Tuple[float, List[MarketEvent]]:
        """
        Calculate the total price impact from all active events.
        
        Args:
            current_tick: Current game tick
            base_price: Base price before event impacts
        
        Returns:
            Tuple of (new_price, list_of_active_events)
        """
        active_events = self.get_active_events(current_tick)
        
        if not active_events:
            return base_price, []
        
        # Calculate cumulative impact
        # For multiple events, we multiply impacts
        # Use dynamic impact for events with duration, static impact for instant events
        total_multiplier = 1.0
        for event in active_events:
            dynamic_impact = event.get_dynamic_impact(current_tick)
            total_multiplier *= dynamic_impact
        
        new_price = base_price * total_multiplier
        
        # Ensure price doesn't go below minimum
        new_price = max(0.01, new_price)
        
        return new_price, active_events
    
    def _save_event_to_redis(self, event: MarketEvent):
        """Save event to Redis"""
        try:
            r = get_redis_connection()
            
            # Add event ID to events set
            events_key = f"events:{self.game_id}"
            r.sadd(events_key, event.event_id)
            
            # Save event data
            event_key = f"event:{self.game_id}:{event.event_id}"
            r.hset(event_key, mapping=event.to_dict())
            
            # Set expiration (keep events for 24 hours after game ends)
            r.expire(event_key, 86400)
            
        except Exception as e:
            print(f"Error saving event to Redis: {e}")
    
    def cleanup_old_events(self, current_tick: int, max_age_ticks: int = 1000):
        """
        Remove old events from Redis that are no longer active and past max_age.
        
        Args:
            current_tick: Current game tick
            max_age_ticks: Maximum age in ticks before cleanup
        """
        try:
            r = get_redis_connection()
            events_key = f"events:{self.game_id}"
            
            if not r.exists(events_key):
                return
            
            event_ids = r.smembers(events_key)
            events_to_remove = []
            
            for event_id in event_ids:
                event_key = f"event:{self.game_id}:{event_id}"
                if r.exists(event_key):
                    event_data = r.hgetall(event_key)
                    event = MarketEvent.from_dict(event_data)
                    
                    # Check if event is old enough to clean up
                    ticks_elapsed = current_tick - event.tick_occurred
                    max_duration = max(event.duration, 1)  # At least 1 tick
                    
                    if ticks_elapsed > max(max_duration, max_age_ticks):
                        events_to_remove.append(event_id)
                        r.delete(event_key)
            
            # Remove from set
            if events_to_remove:
                r.srem(events_key, *events_to_remove)
                
        except Exception as e:
            print(f"Error cleaning up old events: {e}")
    
    def get_event_statistics(self) -> Dict:
        """
        Get statistics about events in this game.
        
        Returns:
            Dictionary with event statistics
        """
        all_events = self.get_all_events()
        
        stats = {
            'total_events': len(all_events),
            'positive_events': len([e for e in all_events if e.event_type == 'positive']),
            'negative_events': len([e for e in all_events if e.event_type == 'negative']),
            'neutral_events': len([e for e in all_events if e.event_type == 'neutral']),
            'extreme_events': len([e for e in all_events if e.severity == 'extreme']),
            'major_events': len([e for e in all_events if e.severity == 'major']),
            'average_impact': 0.0
        }
        
        if all_events:
            # Calculate average absolute impact
            impacts = [abs(e.impact - 1.0) for e in all_events]
            stats['average_impact'] = sum(impacts) / len(impacts)
        
        return stats
    
    def remove_all_events(self):
        """Remove all events for this game from Redis"""
        try:
            r = get_redis_connection()
            events_key = f"events:{self.game_id}"
            
            if not r.exists(events_key):
                return
            
            event_ids = r.smembers(events_key)
            for event_id in event_ids:
                event_key = f"event:{self.game_id}:{event_id}"
                r.delete(event_key)
            
            r.delete(events_key)
            
        except Exception as e:
            print(f"Error removing all events: {e}")


def integrate_event_system_with_market(market, current_tick: int) -> Tuple[float, List[MarketEvent]]:
    """
    Helper function to integrate event system with Market.updateMarket()
    
    Args:
        market: Market instance
        current_tick: Current game tick
    
    Returns:
        Tuple of (price_after_events, active_events)
    """
    event_system = MarketEventSystem(market.game_id)
    
    # Check for new event
    new_event = event_system.check_for_event(current_tick)
    if new_event:
        print(f"[EVENT] {new_event.name}: {new_event.description}")
        print(f"        Impact: {((new_event.impact - 1.0) * 100):+.1f}%")
    
    # Calculate price impact from active events
    base_price = market.market_data.current_price
    final_price, active_events = event_system.calculate_price_impact(current_tick, base_price)
    
    # Cleanup old events periodically
    if current_tick % 100 == 0:  # Every 100 ticks
        event_system.cleanup_old_events(current_tick)
    
    return final_price, active_events