# Toobit Trading Bot

## Overview

This is a cryptocurrency trading bot designed for Toobit exchange USDT-M Futures trading. The bot operates through Telegram commands and provides automated trading capabilities with features like multiple take-profit levels, stop-loss management, break-even protection, and trailing stops. The system is built with Flask for web interface monitoring and uses webhooks for real-time Telegram integration.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask Web Application**: Provides HTTP endpoints for webhook handling and status monitoring
- **Asynchronous Operations**: Uses asyncio for non-blocking trade monitoring and exchange operations
- **Modular Design**: Separated concerns across multiple specialized modules

### Trading Engine
- **TradeBot**: Core trading logic handling order placement, monitoring, and execution
- **TradeConfig**: Centralized configuration management with JSON persistence
- **ExchangeManager**: Exchange connectivity using CCXT library with Binance as fallback
- **Position Management**: Tracks multiple take-profit levels (TP1, TP2, TP3) with percentage-based execution

### Communication Layer
- **Telegram Integration**: Bot commands and callback queries for user interaction
- **Webhook System**: Real-time message processing via Telegram webhooks
- **Interactive Keyboards**: Inline buttons for pair selection and configuration

### Risk Management
- **Dry Run Mode**: Default safe mode for testing strategies without real trades
- **Break-even Protection**: Automatic stop-loss adjustment after profit targets
- **Trailing Stops**: Dynamic stop-loss that follows profitable price movements
- **Leverage Control**: Configurable position sizing with leverage management

### Data Management
- **Configuration Persistence**: JSON-based storage for trade settings
- **State Tracking**: Real-time monitoring of order fills and position status
- **Order Management**: Centralized tracking of active orders and execution state

### Web Interface
- **Status Dashboard**: HTML interface showing bot health and trade status
- **Bootstrap Styling**: Responsive design with dark theme support
- **Real-time Updates**: Live monitoring of bot operations and trade progress

## External Dependencies

### Exchange Integration
- **CCXT Library**: Cryptocurrency exchange connectivity framework
- **Toobit Exchange**: Primary target exchange (with Binance fallback for testing)
- **API Credentials**: Environment-based configuration for secure access

### Communication Services
- **Telegram Bot API**: Message handling and webhook integration
- **HTTP Requests**: Direct API calls for Telegram communication

### Infrastructure
- **Replit Hosting**: Cloud-based deployment platform
- **Environment Variables**: Secure configuration management
- **Webhook URLs**: Dynamic URL configuration for Telegram integration

### Trading Features
- **Futures Trading**: USDT-M perpetual contracts support
- **Multiple Exchanges**: Extensible architecture for different trading platforms
- **Testnet Support**: Sandbox environment for safe development and testing