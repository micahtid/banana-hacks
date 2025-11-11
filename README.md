# Banana Coin

**Banana Coin** is a real-time multiplayer trading game where players compete to maximize their wealth by trading a volatile virtual cryptocurrency. The game features sophisticated market dynamics, automated trading bots, banana-themed market events, and a unique "banana rot" mechanic that penalizes inactive traders—encouraging constant engagement and strategic decision-making.

Players start with $1,000 and must navigate fluctuating prices that update every second, purchase AI-powered trading minions to automate strategies, and compete against other players on a live leaderboard. Games are time-limited (5-120 minutes) and support 2-10 players in multiplayer lobbies.

## Technology Stack

### Frontend
- **Next.js 16.0.1** with App Router
- **React 19.2.0** and **TypeScript 5**
- **Tailwind CSS 4** (custom retro yellow theme)
- **Chart.js 4.5.1** for real-time price visualization
- **Firebase Authentication** (Google OAuth)

### Backend
- **FastAPI** (Python) with asyncio for real-time market updates
- **Redis 5.0+** as the primary database
- **Pydantic** for data validation
- **Uvicorn** ASGI server

### AI/ML
- **Google Gemini 2.5 Pro API** for generating custom trading bot strategies

<<<<<<< HEAD
## Infrastructure & Tools
=======
## Redis Setup

You can host your own Redis server and access it through Tailscale for secure remote access. This allows you to run Redis on a separate machine while keeping it accessible only to devices on your Tailscale network.

For additional setup steps, see the [Tailscale documentation on accessing services](https://tailscale.com/kb/1015/100.x-addresses).

## Setup
>>>>>>> c22b7081549282ac6aad13e3f942afdff5ccfc50

### Redis Database with Tailscale VPN

The application uses a **centralized Redis server** (IP: `100.98.130.5`, port `6379`) accessible via **Tailscale VPN**. This infrastructure enables:

- **Secure remote access** across multiple devices through Tailscale's private mesh network
- **Real-time game state synchronization** for all players
- **Persistent storage** of market data, player wallets, bot states, and transaction histories
- **Low-latency multiplayer** support for competitive trading

Redis stores all critical game data including:
- Game room configurations and player lists
- Real-time market prices and event states
- Individual player wallets and wealth calculations
- Trading bot configurations and balances
- Complete transaction histories for auditing

### Other Tools
- **Firebase Console** for authentication management
- **Python asyncio** for concurrent background tasks (market updates, bot threads)
- **CORS-enabled API** for local development

## Features

### Core Gameplay
- **Real-time Price Fluctuations**: Market prices update every second with simulated volatility
- **Banana Rot Mechanic**: Coins decay exponentially after a cooldown period if not traded (1-7.5 seconds based on trade size), discouraging hoarding
- **Multiplayer Lobbies**: Create or join game rooms with customizable duration and player limits
- **Live Leaderboard**: Real-time wealth rankings based on USD + (BananaCoin balance × current price)
- **Transaction History**: Complete audit log of all buy/sell trades

### Trading Minions (Automated Bots)
Players can purchase six types of AI-powered trading bots:

1. **Random Bot** ($300) - Executes random trades
2. **Momentum Bot** ($800) - Follows price trends using moving averages
3. **Mean Reversion Bot** ($750) - Buys dips and sells peaks
4. **Market Maker Bot** ($1,200) - Maintains balanced 50/50 USD/BC portfolio
5. **Hedger Bot** ($1,000) - Protects against volatility
6. **Custom Bot** ($1,750) - AI-generated strategy using natural language prompts via Gemini API

Each bot receives 70% of its purchase price as starting capital and trades independently in background threads. Bots can be toggled on/off and their performance is tracked in real-time.

### Market Events
Random banana-themed events occur with 3% probability per tick, triggering:
- **Positive Events**: Bumper Harvest (+10-25%), Celebrity Endorsement (+5-15%)
- **Negative Events**: Ship Sinks (-20 to -10%), Fungus Outbreak (-15 to -5%)
- **Neutral Events**: Policy changes, seasonal variations

Events use cubic spline interpolation for smooth price transitions over 1-5 ticks.

## Environment Setup

Copy `example.env` to `.env` in both directories and configure:

**Backend** (`back-end/.env`):
```
REDIS_IP=your_redis_ip
REDIS_PORT=6379
REDIS_PASSWORD=your_password
GEMINI_API_KEY=your_gemini_api_key
```

**Frontend** (`front-end/.env.local`):
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_auth_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_storage_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

## Installation & Running

### Backend
```bash
cd back-end
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python api_server.py
```

The backend API will run at `http://localhost:8000`.

### Frontend
```bash
cd front-end
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

## Project Structure

```
banana-coin/
├── back-end/              # FastAPI backend
│   ├── api_server.py      # Main server with 13 endpoints
│   ├── bot.py             # Bot AI strategies and Gemini integration
│   ├── market.py          # Price simulation engine
│   ├── market_events.py   # 14 banana-themed market events
│   ├── user.py            # Player wallet management
│   ├── transaction_history.py
│   └── redis_helper.py    # Redis connection helper
├── front-end/             # Next.js frontend
│   ├── app/               # Next.js pages and API routes
│   │   ├── api/           # Proxy endpoints to backend
│   │   ├── create-room/   # Room creation page
│   │   ├── game/[gameId]/ # Main game interface
│   │   └── page.tsx       # Landing page
│   ├── components/        # Reusable React components
│   │   ├── game/          # Game-specific components
│   │   │   ├── GameDashboard.tsx
│   │   │   ├── MainDashboard.tsx (trading UI + chart)
│   │   │   ├── Shops.tsx  (minion shop)
│   │   │   ├── Transactions.tsx
│   │   │   └── WaitingRoom.tsx
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── Modal.tsx
│   ├── providers/
│   │   └── UserProvider.tsx  # Firebase auth context
│   └── utils/
│       └── database_functions.tsx  # API client
└── docs/                  # Comprehensive documentation
```

## User Flow

1. **Sign In**: Authenticate via Google using Firebase
2. **Create/Join Room**: Configure game duration (5-120 min) and player limits (2-10)
3. **Waiting Room**: Players join; room creator starts the game
4. **Trading Session**: Navigate three tabs:
   - **Main**: Live price chart, buy/sell interface, wallet status, bot management
   - **Shops**: Purchase and customize trading minions
   - **Transactions**: View complete trade history
5. **Game End**: Final leaderboard with wealth rankings

## Known Issues & Limitations

### Trading Accuracy
- **Buy/Sell Price Skew**: When a player's wallet is depleting rapidly, buy and sell transactions may become slightly skewed due to timing between balance checks and transaction execution. This can occasionally result in minor discrepancies in expected vs. actual trade prices.

### Bot Performance
- **Bot Purchase Limit**: Players are currently limited to purchasing a maximum of 5 trading minions per game to prevent performance degradation.
- **Bot Reliability**: Trading bots occasionally exhibit inconsistent behavior under high market volatility or when multiple bots execute trades simultaneously. This is due to race conditions in concurrent thread execution and is most noticeable with custom Gemini-generated strategies.

### Scalability
- **Performance Degradation**: As more players join a game room, the system experiences increased latency in market updates and transaction processing. Games with 8-10 players may see delays of 1-3 seconds in real-time updates due to Redis query overhead and frontend polling frequency.

### Recommendations
For optimal gameplay experience:
- Limit games to 6-8 players
- Avoid purchasing all 5 bots simultaneously at game start
- Monitor wallet balance closely during rapid trading sequences

## Testing

The project includes comprehensive test suites:

```bash
# Backend unit tests
cd back-end
pytest test_comprehensive.py

# Integration tests
python test_integration.py

# Bot purchase endpoint test
python test_bot_buy_endpoint.py
```

See `docs/TESTING_GUIDE.md` for detailed testing documentation.

## Documentation

Additional documentation is available in the `/docs` folder:
- Bug fix summaries and resolution strategies
- Custom bot creation guide
- Redis data structure reference
- Race condition fixes and transaction improvements

## License

This project was developed for educational purposes during a hackathon event.
