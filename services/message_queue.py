# src/backend/services/message_queue.py

import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
import redis.asyncio as redis
from core.config import settings

logger = logging.getLogger(__name__)

class MessageQueueService:
    """
    Redis-based message queue service for handling packet data pipeline.
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers = {}
        
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def publish_packet_data(self, channel: str, packet_data: Dict[str, Any]) -> bool:
        """
        Publish packet data to a Redis channel.
        
        Args:
            channel: Redis channel name
            packet_data: Packet information dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return False
            
        try:
            message = json.dumps(packet_data)
            await self.redis_client.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    async def subscribe_to_channel(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to a Redis channel and process messages with callback.
        
        Args:
            channel: Redis channel name
            callback: Function to process received messages
        """
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return
            
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            logger.info(f"Subscribed to channel: {channel}")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await callback(data)  # Make callback async
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
        finally:
            if 'pubsub' in locals():
                await pubsub.close()
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


# Global instance
message_queue = MessageQueueService()
