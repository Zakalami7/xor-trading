//! XOR Execution Engine - High-performance order execution
//! 
//! This engine handles low-latency order routing and execution
//! with support for multiple exchanges and order types.

use std::sync::Arc;
use tokio::sync::mpsc;
use tracing::{info, error, Level};
use tracing_subscriber::FmtSubscriber;

mod config;
mod order_router;
mod executor;
mod connection;
mod metrics;

use config::Config;
use order_router::OrderRouter;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize logging
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();
    tracing::subscriber::set_global_default(subscriber)?;
    
    info!("Starting XOR Execution Engine v1.0.0");
    
    // Load configuration
    let config = Config::from_env()?;
    
    info!("Config loaded: {:?}", config.redis_url);
    
    // Initialize order router
    let router = Arc::new(OrderRouter::new(config.clone()).await?);
    
    // Create channels for order processing
    let (order_tx, order_rx) = mpsc::channel(10000);
    
    // Start order processing loop
    let router_clone = router.clone();
    tokio::spawn(async move {
        router_clone.process_orders(order_rx).await;
    });
    
    // Subscribe to Redis for incoming orders
    router.subscribe_orders(order_tx).await?;
    
    info!("Execution Engine running. Press Ctrl+C to stop.");
    
    // Wait for shutdown signal
    tokio::signal::ctrl_c().await?;
    
    info!("Shutting down Execution Engine");
    Ok(())
}
