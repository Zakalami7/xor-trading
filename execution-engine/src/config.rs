//! Configuration module

use std::env;
use anyhow::Result;

#[derive(Debug, Clone)]
pub struct Config {
    pub redis_url: String,
    pub binance_api_key: Option<String>,
    pub binance_api_secret: Option<String>,
    pub bybit_api_key: Option<String>,
    pub bybit_api_secret: Option<String>,
    pub max_order_rate: u32,
    pub enable_testnet: bool,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        Ok(Self {
            redis_url: env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379".into()),
            binance_api_key: env::var("BINANCE_API_KEY").ok(),
            binance_api_secret: env::var("BINANCE_API_SECRET").ok(),
            bybit_api_key: env::var("BYBIT_API_KEY").ok(),
            bybit_api_secret: env::var("BYBIT_API_SECRET").ok(),
            max_order_rate: env::var("MAX_ORDER_RATE")
                .unwrap_or_else(|_| "100".into())
                .parse()
                .unwrap_or(100),
            enable_testnet: env::var("ENABLE_TESTNET")
                .map(|v| v == "true" || v == "1")
                .unwrap_or(false),
        })
    }
}
