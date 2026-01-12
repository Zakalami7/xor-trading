//! Order Router - Smart order routing and execution

use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};

use anyhow::Result;
use chrono::{DateTime, Utc};
use dashmap::DashMap;
use parking_lot::RwLock;
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use tokio::sync::mpsc;
use tracing::{info, warn, error};
use uuid::Uuid;

use crate::config::Config;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderType {
    Market,
    Limit,
    StopMarket,
    StopLimit,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderSide {
    Buy,
    Sell,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Order {
    pub id: String,
    pub bot_id: String,
    pub exchange: String,
    pub symbol: String,
    pub side: OrderSide,
    pub order_type: OrderType,
    pub quantity: f64,
    pub price: Option<f64>,
    pub stop_price: Option<f64>,
    pub reduce_only: bool,
    pub client_order_id: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderResult {
    pub order_id: String,
    pub exchange_order_id: String,
    pub status: String,
    pub filled_quantity: f64,
    pub average_price: f64,
    pub latency_ms: u64,
    pub timestamp: DateTime<Utc>,
}

pub struct OrderRouter {
    config: Config,
    redis: redis::aio::ConnectionManager,
    pending_orders: DashMap<String, Order>,
    latency_stats: Arc<RwLock<LatencyStats>>,
}

#[derive(Debug, Default)]
struct LatencyStats {
    total_orders: u64,
    total_latency_ms: u64,
    min_latency_ms: u64,
    max_latency_ms: u64,
}

impl OrderRouter {
    pub async fn new(config: Config) -> Result<Self> {
        let client = redis::Client::open(config.redis_url.clone())?;
        let redis = redis::aio::ConnectionManager::new(client).await?;
        
        Ok(Self {
            config,
            redis,
            pending_orders: DashMap::new(),
            latency_stats: Arc::new(RwLock::new(LatencyStats::default())),
        })
    }
    
    pub async fn subscribe_orders(&self, tx: mpsc::Sender<Order>) -> Result<()> {
        let client = redis::Client::open(self.config.redis_url.clone())?;
        let mut pubsub = client.get_async_pubsub().await?;
        pubsub.subscribe("xor:orders:execute").await?;
        
        info!("Subscribed to order execution channel");
        
        tokio::spawn(async move {
            loop {
                match pubsub.on_message().next().await {
                    Some(msg) => {
                        let payload: String = msg.get_payload().unwrap_or_default();
                        if let Ok(order) = serde_json::from_str::<Order>(&payload) {
                            if tx.send(order).await.is_err() {
                                error!("Failed to send order to processor");
                                break;
                            }
                        }
                    }
                    None => {
                        warn!("Redis subscription ended");
                        break;
                    }
                }
            }
        });
        
        Ok(())
    }
    
    pub async fn process_orders(self: Arc<Self>, mut rx: mpsc::Receiver<Order>) {
        info!("Order processor started");
        
        while let Some(order) = rx.recv().await {
            let router = self.clone();
            
            // Process order in separate task for parallelism
            tokio::spawn(async move {
                let start = Instant::now();
                
                match router.execute_order(&order).await {
                    Ok(result) => {
                        let latency = start.elapsed().as_millis() as u64;
                        router.update_latency_stats(latency);
                        
                        info!(
                            "Order executed: {} | Status: {} | Latency: {}ms",
                            order.id, result.status, latency
                        );
                        
                        // Publish result
                        if let Err(e) = router.publish_result(&result).await {
                            error!("Failed to publish order result: {}", e);
                        }
                    }
                    Err(e) => {
                        error!("Order execution failed: {} | Error: {}", order.id, e);
                    }
                }
            });
        }
    }
    
    async fn execute_order(&self, order: &Order) -> Result<OrderResult> {
        let start = Instant::now();
        
        // Add to pending
        self.pending_orders.insert(order.id.clone(), order.clone());
        
        // Route to appropriate exchange
        let result = match order.exchange.as_str() {
            "binance" => self.execute_binance(order).await?,
            "bybit" => self.execute_bybit(order).await?,
            _ => {
                return Err(anyhow::anyhow!("Unsupported exchange: {}", order.exchange));
            }
        };
        
        // Remove from pending
        self.pending_orders.remove(&order.id);
        
        let latency = start.elapsed().as_millis() as u64;
        
        Ok(OrderResult {
            order_id: order.id.clone(),
            exchange_order_id: result.exchange_order_id,
            status: result.status,
            filled_quantity: result.filled_quantity,
            average_price: result.average_price,
            latency_ms: latency,
            timestamp: Utc::now(),
        })
    }
    
    async fn execute_binance(&self, order: &Order) -> Result<OrderResult> {
        // Placeholder - would use actual Binance API
        // In production, use binance-rs or similar crate
        Ok(OrderResult {
            order_id: order.id.clone(),
            exchange_order_id: Uuid::new_v4().to_string(),
            status: "filled".to_string(),
            filled_quantity: order.quantity,
            average_price: order.price.unwrap_or(0.0),
            latency_ms: 0,
            timestamp: Utc::now(),
        })
    }
    
    async fn execute_bybit(&self, order: &Order) -> Result<OrderResult> {
        // Placeholder - would use actual Bybit API
        Ok(OrderResult {
            order_id: order.id.clone(),
            exchange_order_id: Uuid::new_v4().to_string(),
            status: "filled".to_string(),
            filled_quantity: order.quantity,
            average_price: order.price.unwrap_or(0.0),
            latency_ms: 0,
            timestamp: Utc::now(),
        })
    }
    
    async fn publish_result(&self, result: &OrderResult) -> Result<()> {
        let mut conn = self.redis.clone();
        let payload = serde_json::to_string(result)?;
        conn.publish::<_, _, ()>("xor:orders:result", payload).await?;
        Ok(())
    }
    
    fn update_latency_stats(&self, latency_ms: u64) {
        let mut stats = self.latency_stats.write();
        stats.total_orders += 1;
        stats.total_latency_ms += latency_ms;
        
        if stats.min_latency_ms == 0 || latency_ms < stats.min_latency_ms {
            stats.min_latency_ms = latency_ms;
        }
        if latency_ms > stats.max_latency_ms {
            stats.max_latency_ms = latency_ms;
        }
    }
    
    pub fn get_stats(&self) -> (u64, f64, u64, u64) {
        let stats = self.latency_stats.read();
        let avg = if stats.total_orders > 0 {
            stats.total_latency_ms as f64 / stats.total_orders as f64
        } else {
            0.0
        };
        (stats.total_orders, avg, stats.min_latency_ms, stats.max_latency_ms)
    }
}

use futures_util::StreamExt;
