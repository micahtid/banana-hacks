"""
Interactive game test with matplotlib visualization
- Graphs market price each second
- Press 'b' to buy, 's' to sell
- Shows portfolio value and balances
"""
import sys
import os
import time
import threading
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle

# Get the project root directory (works whether script is run from test/ or root/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
back_end_dir = os.path.join(project_root, 'back-end')

# Change to back-end directory to ensure imports work
original_cwd = os.getcwd()
os.chdir(back_end_dir)

# Add back-end directory to Python path
if back_end_dir not in sys.path:
    sys.path.insert(0, back_end_dir)

# Also add project root in case of relative imports
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import game components
try:
    from market import Market
    from user import User
    from wallet import UserWallet
except ImportError as e:
    # Restore original directory before raising error
    os.chdir(original_cwd)
    print(f"[ERROR] Failed to import modules: {e}")
    print(f"Script dir: {script_dir}")
    print(f"Project root: {project_root}")
    print(f"Back-end dir: {back_end_dir}")
    print(f"Back-end exists: {os.path.exists(back_end_dir)}")
    print(f"Python path: {sys.path[:3]}")
    raise

# Restore original directory after successful imports
os.chdir(original_cwd)

class InteractiveGame:
    def __init__(self):
        # Initialize game components
        self.game_id = "interactive-test"
        self.market = Market(initial_price=1.0, game_id=self.game_id)
        self.user_id = "player1"
        self.user = User(
            user_id=self.user_id,
            user_name="Player",
            coins=1000.0,
            usd=1000.0,
            last_interaction_v=0
        )
        self.market.addUser(self.user_id)
        
        # Trading parameters
        self.trade_amount = 10.0  # Default trade amount
        
        # Data for plotting
        self.price_history = deque(maxlen=100)  # Keep last 100 prices
        self.time_history = deque(maxlen=100)
        self.portfolio_history = deque(maxlen=100)
        
        # Initialize with starting values
        self.price_history.append(self.market.market_data.current_price)
        self.time_history.append(0)
        self.portfolio_history.append(self.user.get_portfolio_value(self.market.market_data.current_price))
        
        # Plotting setup
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('Banana Coin Trading Game', fontsize=16, fontweight='bold')
        
        # Price chart
        self.price_line, = self.ax1.plot([], [], 'b-', linewidth=2, label='Price')
        self.ax1.set_xlabel('Time (seconds)')
        self.ax1.set_ylabel('Price (USD)', color='b')
        self.ax1.tick_params(axis='y', labelcolor='b')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend(loc='upper left')
        self.ax1.set_title('Market Price Over Time')
        
        # Portfolio value chart
        self.portfolio_line, = self.ax2.plot([], [], 'g-', linewidth=2, label='Portfolio Value')
        self.ax2.set_xlabel('Time (seconds)')
        self.ax2.set_ylabel('Portfolio Value (USD)', color='g')
        self.ax2.tick_params(axis='y', labelcolor='g')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend(loc='upper left')
        self.ax2.set_title('Your Portfolio Value')
        
        # Text display for stats
        self.stats_text = self.fig.text(0.02, 0.02, '', fontsize=10, 
                                        verticalalignment='bottom',
                                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Keyboard input handling
        self.key_pressed = None
        self.input_thread = None
        self.running = True
        
        # Setup keyboard listener
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        
    def on_key_press(self, event):
        """Handle keyboard input"""
        if event.key == 'b':
            self.key_pressed = 'buy'
        elif event.key == 's':
            self.key_pressed = 'sell'
        elif event.key == 'q':
            self.running = False
        elif event.key == '+' or event.key == '=':
            self.trade_amount *= 1.5
        elif event.key == '-' or event.key == '_':
            self.trade_amount /= 1.5
            self.trade_amount = max(0.1, self.trade_amount)  # Minimum 0.1
        
    def update_stats_text(self):
        """Update the statistics text display"""
        current_price = self.market.market_data.current_price
        portfolio_value = self.user.get_portfolio_value(current_price)
        
        stats = (
            f"Tick: {self.market.current_tick} | "
            f"Price: ${current_price:.4f} | "
            f"Volatility: {self.market.market_data.volatility:.4%} | "
            f"BC: {self.user.coins:.2f} | "
            f"USD: ${self.user.usd:.2f} | "
            f"Portfolio: ${portfolio_value:.2f} | "
            f"Trade Amount: {self.trade_amount:.2f} BC\n"
            f"Controls: [b] Buy | [s] Sell | [+] Increase trade | [-] Decrease trade | [q] Quit"
        )
        self.stats_text.set_text(stats)
    
    def process_trade(self):
        """Process pending trade from keyboard input"""
        if self.key_pressed is None:
            return
        
        current_price = self.market.market_data.current_price
        action = self.key_pressed
        self.key_pressed = None  # Reset
        
        if action == 'buy':
            success = self.user.buy_bc(self.trade_amount, current_price, self.market.current_tick)
            if success:
                print(f"✓ Bought {self.trade_amount:.2f} BC at ${current_price:.4f}")
            else:
                print(f"✗ Buy failed: Insufficient USD (need ${self.trade_amount * current_price:.2f})")
        elif action == 'sell':
            success = self.user.sell_bc(self.trade_amount, current_price, self.market.current_tick)
            if success:
                print(f"✓ Sold {self.trade_amount:.2f} BC at ${current_price:.4f}")
            else:
                print(f"✗ Sell failed: Insufficient BC (have {self.user.coins:.2f})")
    
    def update_plot(self, frame):
        """Update the plot with new data"""
        if not self.running:
            return
        
        # Process any pending trades
        self.process_trade()
        
        # Update market
        self.market.updateMarket()
        
        # Get current values
        current_price = self.market.market_data.current_price
        current_tick = self.market.current_tick
        portfolio_value = self.user.get_portfolio_value(current_price)
        
        # Update data
        self.price_history.append(current_price)
        self.time_history.append(current_tick)
        self.portfolio_history.append(portfolio_value)
        
        # Update plots
        if len(self.time_history) > 0:
            self.price_line.set_data(list(self.time_history), list(self.price_history))
            self.portfolio_line.set_data(list(self.time_history), list(self.portfolio_history))
            
            # Auto-scale axes
            self.ax1.relim()
            self.ax1.autoscale_view()
            self.ax2.relim()
            self.ax2.autoscale_view()
        
        # Update stats
        self.update_stats_text()
        
        return self.price_line, self.portfolio_line, self.stats_text
    
    def run(self):
        """Run the interactive game"""
        print("=" * 60)
        print("Interactive Banana Coin Trading Game")
        print("=" * 60)
        print(f"Starting with {self.user.coins:.2f} BC and ${self.user.usd:.2f} USD")
        print(f"Initial price: ${self.market.market_data.current_price:.4f}")
        print("\nControls:")
        print("  [b] - Buy BananaCoin")
        print("  [s] - Sell BananaCoin")
        print("  [+] - Increase trade amount")
        print("  [-] - Decrease trade amount")
        print("  [q] - Quit game")
        print("\nMake sure the plot window is focused to use keyboard controls!")
        print("=" * 60)
        
        # Start animation (updates every 1000ms = 1 second)
        ani = animation.FuncAnimation(
            self.fig, 
            self.update_plot, 
            interval=1000,  # Update every second
            blit=False,
            cache_frame_data=False
        )
        
        plt.show()
        
        print("\nGame ended!")

def main():
    """Main entry point"""
    try:
        game = InteractiveGame()
        game.run()
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

