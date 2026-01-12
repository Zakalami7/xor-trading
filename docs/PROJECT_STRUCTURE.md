# XOR Trading Platform - Structure du Projet

```
xor-trading-platform/
│
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md               # Architecture technique
│   ├── PROJECT_STRUCTURE.md          # Cette documentation
│   ├── API.md                        # Documentation API
│   ├── DEPLOYMENT.md                 # Guide déploiement
│   ├── SECURITY.md                   # Bonnes pratiques sécurité
│   └── STRATEGIES.md                 # Guide des stratégies
│
├── backend/                           # Backend Python (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # Point d'entrée FastAPI
│   │   ├── config.py                 # Configuration globale
│   │   │
│   │   ├── api/                      # Routes API
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py           # Authentification
│   │   │   │   ├── users.py          # Gestion utilisateurs
│   │   │   │   ├── bots.py           # CRUD bots
│   │   │   │   ├── strategies.py     # Stratégies
│   │   │   │   ├── exchanges.py      # Exchanges
│   │   │   │   ├── orders.py         # Ordres
│   │   │   │   ├── positions.py      # Positions
│   │   │   │   ├── analytics.py      # Analytics
│   │   │   │   ├── backtesting.py    # Backtesting
│   │   │   │   └── websocket.py      # WebSocket handlers
│   │   │   └── deps.py               # Dependencies
│   │   │
│   │   ├── core/                     # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── security.py           # Sécurité/Chiffrement
│   │   │   ├── auth.py               # JWT/OAuth
│   │   │   ├── events.py             # Event system
│   │   │   └── exceptions.py         # Custom exceptions
│   │   │
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── bot.py
│   │   │   ├── strategy.py
│   │   │   ├── order.py
│   │   │   ├── trade.py
│   │   │   ├── position.py
│   │   │   ├── api_credential.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── schemas/                  # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── bot.py
│   │   │   ├── strategy.py
│   │   │   ├── order.py
│   │   │   ├── trade.py
│   │   │   └── common.py
│   │   │
│   │   ├── services/                 # Business services
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py
│   │   │   ├── bot_service.py
│   │   │   ├── order_service.py
│   │   │   └── analytics_service.py
│   │   │
│   │   └── db/                       # Database
│   │       ├── __init__.py
│   │       ├── session.py            # Session management
│   │       ├── base.py               # Base model
│   │       └── migrations/           # Alembic migrations
│   │
│   ├── tests/                        # Tests backend
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_bots.py
│   │   └── test_strategies.py
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── strategy-engine/                   # Moteur de Stratégies (Python)
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── core.py                   # Core engine
│   │   ├── event_bus.py              # Event bus Redis
│   │   ├── signal_generator.py       # Générateur signaux
│   │   │
│   │   ├── strategies/               # Stratégies de trading
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Classe de base
│   │   │   ├── grid.py               # Grid Trading
│   │   │   ├── dca.py                # Dollar Cost Averaging
│   │   │   ├── scalping.py           # Scalping HF
│   │   │   ├── trend_following.py    # Tendance
│   │   │   ├── mean_reversion.py     # Mean Reversion
│   │   │   └── ai_signals.py         # Stratégie IA
│   │   │
│   │   ├── indicators/               # Indicateurs techniques
│   │   │   ├── __init__.py
│   │   │   ├── momentum.py           # RSI, MACD, etc
│   │   │   ├── volatility.py         # ATR, Bollinger
│   │   │   ├── trend.py              # MA, EMA, etc
│   │   │   └── volume.py             # Volume indicators
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   │
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── risk-engine/                       # Moteur de Risque (Python)
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── core.py                   # Core risk engine
│   │   ├── position_manager.py       # Gestion positions
│   │   ├── drawdown_controller.py    # Contrôle drawdown
│   │   ├── kill_switch.py            # Kill switch auto
│   │   ├── pnl_tracker.py            # Tracking PnL
│   │   ├── correlation.py            # Corrélation actifs
│   │   └── validators.py             # Validation ordres
│   │
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── execution-engine/                  # Moteur d'Exécution (Rust)
│   ├── src/
│   │   ├── main.rs
│   │   ├── lib.rs
│   │   ├── config.rs
│   │   │
│   │   ├── order_router/             # Order routing
│   │   │   ├── mod.rs
│   │   │   ├── smart_router.rs       # Smart order routing
│   │   │   └── algorithms.rs         # TWAP, VWAP, Iceberg
│   │   │
│   │   ├── executor/                 # Exécution ordres
│   │   │   ├── mod.rs
│   │   │   ├── market.rs             # Market orders
│   │   │   ├── limit.rs              # Limit orders
│   │   │   └── stop.rs               # Stop orders
│   │   │
│   │   ├── connection/               # Connexions exchanges
│   │   │   ├── mod.rs
│   │   │   ├── websocket.rs          # WebSocket pool
│   │   │   └── failover.rs           # Failover logic
│   │   │
│   │   └── metrics/                  # Métriques performance
│   │       ├── mod.rs
│   │       └── latency.rs
│   │
│   ├── tests/
│   ├── Cargo.toml
│   └── Dockerfile
│
├── exchange-adapter/                  # Abstraction Exchanges (Python)
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py                   # Interface de base
│   │   ├── binance/
│   │   │   ├── __init__.py
│   │   │   ├── spot.py               # Binance Spot
│   │   │   ├── futures.py            # Binance Futures
│   │   │   └── websocket.py          # WebSocket handler
│   │   ├── bybit/
│   │   │   ├── __init__.py
│   │   │   ├── futures.py
│   │   │   └── websocket.py
│   │   ├── okx/
│   │   │   ├── __init__.py
│   │   │   ├── unified.py
│   │   │   └── websocket.py
│   │   └── kraken/
│   │       ├── __init__.py
│   │       ├── spot.py
│   │       └── websocket.py
│   │
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── backtesting-engine/                # Backtesting (Python)
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── core.py                   # Moteur principal
│   │   ├── data_loader.py            # Chargement données
│   │   ├── simulator.py              # Simulateur marché
│   │   ├── metrics.py                # Métriques performance
│   │   ├── slippage.py               # Modèle slippage
│   │   ├── commission.py             # Modèle commissions
│   │   └── monte_carlo.py            # Simulation Monte Carlo
│   │
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── ai-engine/                         # Moteur IA (Python + PyTorch)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── price_predictor.py        # Prédiction prix
│   │   ├── sentiment.py              # Analyse sentiment
│   │   ├── volatility.py             # Prédiction volatilité
│   │   └── signal_classifier.py      # Classification signaux
│   │
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py                  # Scripts training
│   │   └── data_pipeline.py          # Pipeline données
│   │
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── onnx_runtime.py           # ONNX pour production
│   │   └── server.py                 # Serveur inférence
│   │
│   ├── saved_models/                 # Modèles entraînés
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                          # Frontend Next.js
│   ├── src/
│   │   ├── app/                      # App Router (Next.js 14)
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Landing page
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx          # Dashboard principal
│   │   │   │   ├── bots/
│   │   │   │   │   ├── page.tsx      # Liste bots
│   │   │   │   │   ├── new/page.tsx  # Création bot
│   │   │   │   │   └── [id]/page.tsx # Détail bot
│   │   │   │   ├── analytics/page.tsx
│   │   │   │   ├── positions/page.tsx
│   │   │   │   ├── orders/page.tsx
│   │   │   │   └── settings/page.tsx
│   │   │   └── api/                  # API routes
│   │   │
│   │   ├── components/               # Composants React
│   │   │   ├── ui/                   # UI primitives
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   └── ...
│   │   │   ├── charts/               # Charts TradingView
│   │   │   │   ├── PriceChart.tsx
│   │   │   │   ├── PnLChart.tsx
│   │   │   │   └── DrawdownChart.tsx
│   │   │   ├── bots/
│   │   │   │   ├── BotCard.tsx
│   │   │   │   ├── BotWizard.tsx
│   │   │   │   └── BotStatus.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── Stats.tsx
│   │   │   │   ├── PositionList.tsx
│   │   │   │   └── RecentTrades.tsx
│   │   │   └── layout/
│   │   │       ├── Navbar.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── Footer.tsx
│   │   │
│   │   ├── hooks/                    # Custom hooks
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useAuth.ts
│   │   │   ├── useBots.ts
│   │   │   └── usePositions.ts
│   │   │
│   │   ├── lib/                      # Utilities
│   │   │   ├── api.ts                # API client
│   │   │   ├── websocket.ts          # WebSocket client
│   │   │   ├── utils.ts
│   │   │   └── constants.ts
│   │   │
│   │   ├── store/                    # State management
│   │   │   ├── index.ts
│   │   │   ├── authSlice.ts
│   │   │   ├── botsSlice.ts
│   │   │   └── marketSlice.ts
│   │   │
│   │   └── types/                    # TypeScript types
│   │       ├── index.ts
│   │       ├── bot.ts
│   │       ├── order.ts
│   │       └── market.ts
│   │
│   ├── public/                       # Static assets
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── next.config.js
│   └── Dockerfile
│
├── infrastructure/                    # Infrastructure as Code
│   ├── docker/
│   │   ├── docker-compose.yml        # Dev environment
│   │   ├── docker-compose.prod.yml   # Production
│   │   └── .env.example
│   │
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── configmaps/
│   │   ├── secrets/
│   │   ├── deployments/
│   │   │   ├── backend.yaml
│   │   │   ├── strategy-engine.yaml
│   │   │   ├── risk-engine.yaml
│   │   │   ├── execution-engine.yaml
│   │   │   ├── frontend.yaml
│   │   │   └── ai-engine.yaml
│   │   ├── services/
│   │   ├── ingress/
│   │   └── hpa/                      # Auto-scaling
│   │
│   ├── helm/
│   │   └── xor-trading/
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       ├── values-prod.yaml
│   │       └── templates/
│   │
│   ├── terraform/                    # Cloud provisioning
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── modules/
│   │
│   └── monitoring/
│       ├── prometheus/
│       │   └── prometheus.yml
│       ├── grafana/
│       │   └── dashboards/
│       └── alertmanager/
│           └── alertmanager.yml
│
├── scripts/                           # Scripts utilitaires
│   ├── setup.sh                      # Setup développement
│   ├── deploy.sh                     # Déploiement
│   ├── backup.sh                     # Backup DB
│   └── migrate.sh                    # Migrations DB
│
├── .github/                           # CI/CD
│   └── workflows/
│       ├── ci.yml                    # Tests + Lint
│       ├── cd.yml                    # Déploiement
│       └── security.yml              # Security scan
│
├── .gitignore
├── README.md
├── LICENSE
└── CHANGELOG.md
```
