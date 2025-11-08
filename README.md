## Data Structure

```json
{
  "gameId": "string",
  "isStarted": "boolean",
  "durationMinutes": "int",
  "maxPlayers": "int",
  "eventTime": "Date",

  "players": [
    {
      "playerId": "string",
      "playerName": "string",
      "coinBalance": "float",
      "usdBalance": "float",
      "lastInteractionValue": "int",
      "lastInteractionTime": "Date",
      "bots": [
        {
          "botId": "string",
          "botName": "string",
          "startingUsdBalance": "float",
          "usdBalance": "float",
          "coinBalance": "float",
          "isActive": "boolean"
        }
      ]
    }
  ],

  "coinHistory": ["float"],
  "totalCoin": "float",
  "totalUsd": "int",

  "interactions": [
    {
      "interactionName": "string",
      "interactionDescription": "string"
    }
  ]
}
