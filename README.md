# Banana Coin

Banana Coin is a simple trading game. You buy and sell coins while its price changes every second. If you stop playing for a while, your wallet slowly rots. You can unlock small "minion" bots that trade for you.

| <img src="images/1.png" width="300" /> | <img src="images/2.png" width="300" /> | <img src="images/3.png" width="300" /> |
|:--------------------------------------:|:--------------------------------------:|:--------------------------------------:|

## Technology

- <img src="https://raw.githubusercontent.com/github/explore/main/topics/react/react.png" width="18" /> React + Next.js
- <img src="https://raw.githubusercontent.com/github/explore/main/topics/fastapi/fastapi.png" width="18" /> FastAPI
- <img src="https://raw.githubusercontent.com/github/explore/main/topics/redis/redis.png" width="18" /> Redis
- <img src="https://raw.githubusercontent.com/github/explore/main/topics/firebase/firebase.png" width="18" /> Firebase Auth

## Environment

Copy from `example.env`.

- Back‑end: `REDIS_IP`, `REDIS_PORT`, `REDIS_PASSWORD`
- Front‑end: `NEXT_PUBLIC_API_BASE`, Firebase Client Vars

## Server Architecture

### Redis Setup

This application uses a **local Redis server** for real-time game state management, price updates, and player interactions. Redis handles:
- Live price data and market events
- Player wallets and trading history
- Trading bot state and operations
- Real-time leaderboard updates

You can host your own Redis server locally or on a separate machine.

### Tailscale for Remote Access

The project is configured to use **Tailscale** for secure remote access to the Redis server. This setup allows:
- Running Redis on any machine on your Tailscale network
- Secure, encrypted connections without exposing Redis to the internet
- Easy multi-device access (play from laptop, run server on desktop)

To set up Tailscale for your Redis server:
1. Install Tailscale on both the server machine and client devices
2. Note the Tailscale IP address of your Redis server (e.g., `100.x.y.z`)
3. Set `REDIS_IP` in your `.env` to the Tailscale IP
4. Your Redis server is now securely accessible across your Tailscale network

For more details, see the [Tailscale documentation on accessing services](https://tailscale.com/kb/1015/100.x-addresses).

## Setup

- Back‑end
  1. `cd back-end`
  2. `python -m venv .venv && . .venv/Scripts/activate` (Windows) or `source .venv/bin/activate`
  3. `pip install -r requirements.txt`
  4. `python app.py`

- Front‑end
  1. `cd front-end`
  2. `npm install`
  3. `npm run dev`
  4. Open http://localhost:3000

## Front-End Architecture

### Overview

The front-end is built with **Next.js 14 (App Router)**, **React**, **TypeScript**, and **Tailwind CSS**, providing a real-time trading game interface with retro gaming aesthetics.

### Project Structure

```
front-end/
├── app/
│   ├── api/                   # API route handlers (proxy to Python backend)
│   ├── create-room/           # Create game room page
│   ├── game/[gameId]/         # Dynamic game page
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── game/
│   │   ├── GameDashboard.tsx  # Main game wrapper & navigation
│   │   ├── MainDashboard.tsx  # Trading dashboard with live chart
│   │   ├── Shops.tsx          # Minion shop interface
│   │   ├── Transactions.tsx   # Transaction history
│   │   └── WaitingRoom.tsx    # Pre-game lobby
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Input.tsx
│   ├── Modal.tsx
│   ├── NewsBanner.tsx
│   └── StatDisplay.tsx
├── hooks/
│   ├── useEventNews.ts        # Event and news state management
│   └── useGameTimer.ts        # Game timer and countdown logic
├── constants/
│   └── minions.ts             # Bot prices and configurations
├── providers/
│   └── UserProvider.tsx       # Firebase auth state management
└── utils/
    └── database_functions.tsx # Firebase & API client functions
```

### User Flow

1. **Authentication**: Google Sign-In via Firebase Auth
2. **Create / Join Room**: Set game duration (5-120 min) and max players (2-10)
3. **Waiting Room**: Players join, creator starts game
4. **Game Session**: 
   - **Main Dashboard**: Live price chart, buy / sell coins, manage minions, view wallet
   - **Shops**: Purchase 5 prebuilt or custom AI-powered minions ($300-$1750)
   - **Transactions**: View buy / sell history
5. **End Game**: Final leaderboard and rankings

### Key Features

- **Real-Time Trading**: 1-second polling for live price updates
- **Banana Rot System**: Coins decay exponentially if inactive (encourages trading)
- **Trading Minions**: Automated bots with different strategies (Random, Momentum, Mean Reversion, Market Maker, Hedger, Custom)
- **Market Events**: Random events trigger scrolling news banner alerts

### Game Mechanics

**Banana Rot**: 
- Cooldown: 1-7.5 seconds (scales with trade size)
- Decay: Exponential `e^(-coefficient × time)` after cooldown

**Minion Performance**:
- Tracks BC balance and % change since purchase
- Custom minions use natural language strategy prompts
