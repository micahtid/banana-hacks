from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from market import Market
from pydantic import BaseModel

import time
import uuid

app = FastAPI(title="Banana Coin API")

class GameInitRequest(BaseModel):
    duration: int
    userIDs: list[str]

class GameInitResponse(BaseModel):
    gameID: str
    market: Market



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/startGame")
async def startGame(request: GameInitRequest):
    try:
        gameID = uuid.uuid4()
        market = Market()
        for userID in request.userIDs:
            market.addUser(userID)

        while (request.duration > 0):
            market.updateMarket()
            request.duration -= 1
            time.sleep(1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return GameInitResponse(gameID=gameID, market=market)


    
