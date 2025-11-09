# Transaction History API Documentation

## Overview

The transaction history system tracks all trades (both user and bot) with timestamps and detailed information. This document explains how to use the transaction history API endpoints in the front-end.

## API Endpoints

### 1. Get All Transactions

**Endpoint:** `GET /api/transactions/{game_id}`

**Query Parameters:**
- `limit` (optional, default: 100): Maximum number of transactions to return
- `offset` (optional, default: 0): Number of transactions to skip (for pagination)

**Response:**
```json
{
  "success": true,
  "gameId": "game123",
  "transactions": [
    {
      "type": "buy",
      "actor": "user123",
      "actor_name": "John Doe",
      "amount": 10.0,
      "price": 1.5,
      "total_cost": 15.0,
      "timestamp": "2025-11-09T10:30:00",
      "is_bot": false
    },
    {
      "type": "sell",
      "actor": "bot456",
      "actor_name": "Bot_bot456",
      "amount": 5.0,
      "price": 1.6,
      "total_cost": 8.0,
      "timestamp": "2025-11-09T10:31:00",
      "is_bot": true,
      "bot_type": "momentum",
      "user_id": "user123"
    }
  ],
  "stats": {
    "total_transactions": 2,
    "buy_count": 1,
    "sell_count": 1,
    "bot_transactions": 1,
    "user_transactions": 1,
    "total_volume": 15.0,
    "total_value": 23.0
  },
  "count": 2
}
```

### 2. Get User's Transactions

**Endpoint:** `GET /api/transactions/{game_id}/user/{user_id}`

**Query Parameters:**
- `limit` (optional, default: 100): Maximum number of transactions to return

**Response:**
```json
{
  "success": true,
  "gameId": "game123",
  "userId": "user123",
  "transactions": [
    {
      "type": "buy",
      "actor": "user123",
      "actor_name": "John Doe",
      "amount": 10.0,
      "price": 1.5,
      "total_cost": 15.0,
      "timestamp": "2025-11-09T10:30:00",
      "is_bot": false
    }
  ],
  "count": 1
}
```

### 3. Get Bot Transactions

**Endpoint:** `GET /api/transactions/{game_id}/bots`

**Query Parameters:**
- `limit` (optional, default: 100): Maximum number of transactions to return

**Response:**
```json
{
  "success": true,
  "gameId": "game123",
  "transactions": [
    {
      "type": "sell",
      "actor": "bot456",
      "actor_name": "Bot_bot456",
      "amount": 5.0,
      "price": 1.6,
      "total_cost": 8.0,
      "timestamp": "2025-11-09T10:31:00",
      "is_bot": true,
      "bot_type": "momentum",
      "user_id": "user123"
    }
  ],
  "count": 1
}
```

### 4. Get Transaction Statistics

**Endpoint:** `GET /api/transactions/{game_id}/stats`

**Response:**
```json
{
  "success": true,
  "gameId": "game123",
  "stats": {
    "total_transactions": 10,
    "buy_count": 6,
    "sell_count": 4,
    "bot_transactions": 3,
    "user_transactions": 7,
    "total_volume": 50.0,
    "total_value": 75.5
  }
}
```

## Front-End Integration Examples

### React/TypeScript Example

```typescript
// Transaction interface
interface Transaction {
  type: 'buy' | 'sell';
  actor: string;
  actor_name: string;
  amount: number;
  price: number;
  total_cost: number;
  timestamp: string;
  is_bot: boolean;
  bot_type?: string;
  user_id?: string;
}

interface TransactionStats {
  total_transactions: number;
  buy_count: number;
  sell_count: number;
  bot_transactions: number;
  user_transactions: number;
  total_volume: number;
  total_value: number;
}

// Fetch all transactions
async function fetchTransactions(gameId: string, limit: number = 100): Promise<Transaction[]> {
  const response = await fetch(`/api/transactions/${gameId}?limit=${limit}`);
  const data = await response.json();
  
  if (!data.success) {
    throw new Error('Failed to fetch transactions');
  }
  
  return data.transactions;
}

// Fetch user's transactions
async function fetchUserTransactions(gameId: string, userId: string): Promise<Transaction[]> {
  const response = await fetch(`/api/transactions/${gameId}/user/${userId}`);
  const data = await response.json();
  
  if (!data.success) {
    throw new Error('Failed to fetch user transactions');
  }
  
  return data.transactions;
}

// Fetch transaction stats
async function fetchTransactionStats(gameId: string): Promise<TransactionStats> {
  const response = await fetch(`/api/transactions/${gameId}/stats`);
  const data = await response.json();
  
  if (!data.success) {
    throw new Error('Failed to fetch transaction stats');
  }
  
  return data.stats;
}

// React component example
import React, { useState, useEffect } from 'react';

function TransactionHistory({ gameId, userId }: { gameId: string; userId: string }) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [stats, setStats] = useState<TransactionStats | null>(null);
  const [filter, setFilter] = useState<'all' | 'user' | 'bot'>('all');
  
  useEffect(() => {
    const loadTransactions = async () => {
      try {
        let data: Transaction[];
        
        switch (filter) {
          case 'user':
            data = await fetchUserTransactions(gameId, userId);
            break;
          case 'bot':
            const response = await fetch(`/api/transactions/${gameId}/bots`);
            const json = await response.json();
            data = json.transactions;
            break;
          default:
            data = await fetchTransactions(gameId);
        }
        
        setTransactions(data);
        
        // Load stats
        const statsData = await fetchTransactionStats(gameId);
        setStats(statsData);
      } catch (error) {
        console.error('Failed to load transactions:', error);
      }
    };
    
    loadTransactions();
    
    // Poll for new transactions every 5 seconds
    const interval = setInterval(loadTransactions, 5000);
    
    return () => clearInterval(interval);
  }, [gameId, userId, filter]);
  
  return (
    <div>
      <h2>Transaction History</h2>
      
      {/* Filter buttons */}
      <div>
        <button onClick={() => setFilter('all')}>All</button>
        <button onClick={() => setFilter('user')}>My Trades</button>
        <button onClick={() => setFilter('bot')}>Bot Trades</button>
      </div>
      
      {/* Statistics */}
      {stats && (
        <div>
          <p>Total Transactions: {stats.total_transactions}</p>
          <p>Buys: {stats.buy_count} | Sells: {stats.sell_count}</p>
          <p>Total Volume: {stats.total_volume.toFixed(2)} BC</p>
        </div>
      )}
      
      {/* Transaction list */}
      <div>
        {transactions.map((tx, index) => (
          <div key={index} className={`transaction ${tx.type}`}>
            <span>{tx.actor_name}</span>
            <span>{tx.type.toUpperCase()}</span>
            <span>{tx.amount.toFixed(2)} BC</span>
            <span>${tx.price.toFixed(2)}</span>
            <span>${tx.total_cost.toFixed(2)}</span>
            <span>{new Date(tx.timestamp).toLocaleString()}</span>
            {tx.is_bot && <span className="badge">BOT</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

export default TransactionHistory;
```

### Updating Existing Transactions Component

To integrate with your existing `Transactions.tsx` component, you can replace the current data source:

```typescript
// In front-end/components/game/Transactions.tsx

import { useEffect, useState } from "react";

// ... existing imports ...

export default function Transactions({ game, currentUser }: TransactionsProps) {
  const [transactions, setTransactions] = useState([]);
  const [filter, setFilter] = useState<FilterType>("all");
  const [isLoading, setIsLoading] = useState(true);

  // Fetch transactions from API instead of using game.interactions
  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setIsLoading(true);
        
        let url = `/api/transactions/${game.gameId}`;
        if (filter === 'bot') {
          url = `/api/transactions/${game.gameId}/bots`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
          // Transform to match existing format
          const transformed = data.transactions.map(tx => ({
            name: tx.actor_name,
            type: tx.type,
            value: Math.round(tx.amount * 100), // Convert to cents
            timestamp: tx.timestamp,
            isBot: tx.is_bot
          }));
          
          setTransactions(transformed);
        }
      } catch (error) {
        console.error('Failed to fetch transactions:', error);
        // Fall back to game.interactions if API fails
        setTransactions(game.interactions || []);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTransactions();
    
    // Poll for new transactions every 2 seconds
    const interval = setInterval(fetchTransactions, 2000);
    return () => clearInterval(interval);
  }, [game.gameId, filter]);

  // ... rest of component ...
}
```

## Benefits

1. **Real-time Updates**: The transaction history is updated in real-time as trades happen
2. **Filtering**: Easy to filter by user, bot, or transaction type
3. **Statistics**: Get comprehensive statistics about trading activity
4. **Pagination**: Support for large transaction histories
5. **Timestamps**: All transactions have accurate timestamps
6. **Bot Attribution**: Bot transactions are linked to their owner user

## Backward Compatibility

The transaction history system maintains backward compatibility with the existing `interactions` field in the game data. All transactions are automatically added to both:
- The new transaction history system (Redis list with full details)
- The legacy interactions array (for existing front-end code)

This ensures that existing front-end code continues to work while new code can take advantage of the enhanced transaction history features.

