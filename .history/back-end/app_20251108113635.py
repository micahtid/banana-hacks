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

def startGame(duration):
    market = Market()
    while (duration > 0):
        market.updateMarket()
        duration -= 1
        time.sleep(1)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/startGame")
async def startGame(duration: int):
    try:
        gameID = uuid.uuid4()
        market = Market()
        for userID in userIDs:
            market.addUser(userID)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return GameInitResponse(gameID=gameID, market=market)


    

