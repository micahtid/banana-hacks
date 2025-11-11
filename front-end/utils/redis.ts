import Redis from 'ioredis';

let redis: Redis | null = null;

/**
 * Get singleton Redis client instance
 * Environment variables:
 * - REDIS_IP: Redis server IP address
 * - REDIS_PORT: Redis server port
 * - REDIS_PASSWORD: Redis password
 *
 * Note: Default credentials are for development only.
 * Set environment variables in production for security.
 */
export function getRedisClient(): Redis {
  if (!redis) {
    redis = new Redis({
      host: process.env.REDIS_IP || '100.98.130.5',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      password: process.env.REDIS_PASSWORD || 'micah_is_a_cutie',
      retryStrategy: (times) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
    });

    redis.on('error', (err) => {
      // Redis connection error
    });

    redis.on('connect', () => {
      // Connected to Redis
    });
  }

  return redis;
}

export async function closeRedisConnection() {
  if (redis) {
    await redis.quit();
    redis = null;
  }
}
