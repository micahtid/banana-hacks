# Banana Coin

Banana Coin is a simple trading game. You buy and sell coins while its price changes every second. If you stop playing for a while, your wallet slowly rots. You can unlock small “minion” bots that trade for you.

## Technology

- <img src="https://raw.githubusercontent.com/github/explore/main/topics/react/react.png" width="18" /> React + Next.js
- <img src="https://raw.githubusercontent.com/github/explore/main/topics/fastapi/fastapi.png" width="18" /> FastAPI
- <img src="https://raw.githubusercontent.com/github/explore/main/topics/redis/redis.png" width="18" /> Redis
- <img src="https://raw.githubusercontent.com/github/explore/main/topics/firebase/firebase.png" width="18" /> Firebase Auth

## Environment

Copy from `example.env`.

- Back‑end: `REDIS_IP`, `REDIS_PORT`, `REDIS_PASSWORD` (optional)
- Front‑end: `NEXT_PUBLIC_API_BASE`, Firebase client vars

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

## Notes

- Start a game via the UI (or `POST /startGame?gameID={id}`) to begin live price updates.
- Ensure Redis is running locally (default 6379).
