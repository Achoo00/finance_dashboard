# 📋 Comprehensive Test Plan - Finance Dashboard

## Overview
This document outlines the complete test strategy for the Finance Dashboard application. Tests are organized by component and priority.

---

## Social Test Structure
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_database.py     # Database unit tests
│   ├── test_data_collector.py  # Data collection unit tests
│   ├── test_analysis.py     # Analysis unit tests
│   └── test_yaml_exporter.py   # YAML export unit tests
├── integration/
│   ├── test_data_pipeline.py    # End-to-end data flow
│   └── test_api_integration.py  # yfinance API integration
└── functional/
    └── test_portfolio_management.py  # Portfolio CRUD operations
```

---

## 1. Database Layer Tests (`test_database.py`)

### 1.1 Portfolio Management
- ✅ **Test 1.1.1**: Create portfolio with valid data - *Completed*
- ✅ **Test 1.1.2**: Create portfolio with duplicate name (should fail) - *Completed*
- ✅ **Test 1.1.3**: Create portfolio with invalid data (missing name) - *Completed*
- ✅ **Test 1.1.4**: Get portfolio by ID (existing) - *Completed*
- ✅ **Test 1.1.5**: Get portfolio by ID (non-existent) - *Completed*
- ✅ **Test 1.1.6**: Get all portfolios - *Completed*
- ✅ **Test 1.1.7**: Get default portfolio - *Completed*
- ✅ **Test 1.1.8**: Update portfolio (name, description, is_default) - *Completed*
- ✅ **Test 1.1.9**: Delete portfolio (with positions - should cascade) - *Completed*
- ✅ **Test 1.1.10**: Delete portfolio (without positions) - *Completed*
- ✅ **Test 1.1.11**: Set default portfolio (should unset previous default) - *Completed*

### 1.2 Position Management
- ✅ **Test 1.2.1**: Add position with valid data - *Completed*
- ✅ **Test 1.2.2**: Add position with invalid portfolio_id (should fail) - *Completed*
- ✅ **Test 1.2.3**: Get position by ID (existing) - *Completed*
- ✅ **Test 1.2.4**: Get position by ID (non-existent) - *Completed*
- ✅ **Test 1.2.5**: Get all positions - *Completed*
- ✅ **Test 1.2.6**: Get portfolio positions (specific portfolio) - *Completed*
- ✅ **Test 1.2.7**: Update position (entry_price, quantity, notes) - *Completed*
- ✅ **Test 1.2.8**: Delete position (should delete related market_data) - *Completed*
- ✅ **Test 1.2.9**: Delete position (non-existent - should handle gracefully) - *Completed*

### 1.3 Market Data Management
- ✅ **Test 1.3.1**: Update market data (new position - should create) - *Completed*
- ✅ **Test 1.3.2**: Update market data (existing position - should update) - *Completed*
- ✅ **Test 1.3.3**: Update market data with quarterly_revenue/net_income (JSON serialization) - *Completed*
- ✅ **Test 1.3.4**: Get market data by position_id (existing) - *Completed*
- ✅ **Test 1.3.5**: Get market data by position_id (non-existent) - *Completed*
- ✅ **Test 1.3.6**: Market data JSON serialization/deserialization - *Completed*
- ✅ **Test 1.3.7**: Update market data with technical indicators - *Completed*

### 1.4 Price History
- ✅ **Test 1.4.1**: Add price history for ticker - *Completed*
- ✅ **Test 1.4.2**: Get price history with date range - *Completed*
- ✅ **Test 1.4.3**: Get price history without date range (all data) - *Incomplete*

### 1.5 Database Transactions & Error Handling
- ❌ **Test 1.5.1**: Transaction rollback on error - *Incomplete: Test needs revision to properly test transaction rollback*
- ✅ **Test 1.5.2**: Database connection cleanup - *Completed*
- ❌ **Test 1.5.3**: Foreign key constraint violations - *Incomplete: Test needs revision to handle NOT NULL constraint for ticker field*

---

## 2. Data Collector Tests (`test_data_collector.py`)

### 2.1 Cache Management
- ✅ **Test 2.1.1**: Cache validation (fresh data - should use cache)
- ✅ **Test 2.1.2**: Cache validation (stale data - should fetch new)
- ✅ **Test 2.1.3**: Cache validation (missing data - should fetch new)
- ✅ **Test 2.1.4**: Force refresh bypasses cache
- ✅ **Test 2.1.5**: Cached data conversion to dict (with JSON fields)

### 2.2 Stock Data Fetching
- ✅ **Test 2.2.1**: Fetch stock data successfully (basic info)
- ✅ **Test 2.2.2**: Fetch stock data with financials (quarterly_revenue, net_income)
- ✅ **Test 2.2.3**: Fetch stock data with invalid ticker (should handle gracefully)
- ✅ **Test 2.2.4**: Fetch stock data with network error (should retry)
- ✅ **Test 2.2.5**: Fetch stock data rate limiting (should wait)
- ✅ **Test 2.2.6**: Fetch stock data with missing fields (should use None)
- ✅ **Test 2.2.7**: Fetch stock data fallback to cached on error
- ✅ **Test 2.2.8**: Fetch stock data timestamp conversion

### 2.3 Historical Data Fetching
- ✅ **Test 2.3.1**: Fetch historical prices (1y period)
- ✅ **Test 2.3.2**: Fetch historical prices (5y period)
- ✅ **Test 2.3.3**: Fetch historical prices with invalid period (should handle gracefully)
- ✅ **Test 2.3.4**: Fetch historical prices with empty result

### 2.4 Technical Indicators
- ✅ **Test 2.4.1**: Calculate technical indicators (RSI, MACD, SMA)
- ✅ **Test 2.4.2**: Calculate technical indicators with insufficient data
- ✅ **Test 2.4.3**: Technical indicators caching
- ✅ **Test 2.4.4**: Technical indicators boolean flags (overbought, oversold, crossover)

### 2.5 Error Handling & Retry Logic
- ✅ **Test 2.5.1**: Retry on rate limit (429 error)
- ✅ **Test 2.5.2**: Retry on network timeout
- ✅ **Test 2.5.3**: Max retries exceeded (should return None)
- ✅ **Test 2.5.4**: Exponential backoff delay calculation

---

## 3. Analysis Tests (`test_analysis.py`)

### 3.1 Portfolio Composition Chart
- ✅ **Test 3.1.1**: Create composition chart with valid data
- ✅ **Test 3.1.2**: Create composition chart with empty DataFrame (should return None)
- ✅ **Test 3.1.3**: Create composition chart with missing columns (should handle gracefully)
- ✅ **Test 3.1.4**: Create composition chart with 'Ticker' column (capitalized)
- ✅ **Test 3.1.5**: Create composition chart with 'ticker' column (lowercase)

### 3.2 Portfolio Performance Chart
- ✅ **Test 3.2.1**: Create performance chart with 'Return %' column
- ✅ **Test 3.2.2**: Create performance chart with 'Gain/Loss' column
- ✅ **Test 3.2.3**: Create performance chart with 'gain_loss_pct' column
- ✅ **Test 3.2.4**: Create performance chart with empty DataFrame
- ✅ **Test 3.2.5**: Performance chart color coding (green for positive, red for negative)

### 3.3 Technical Chart
- ✅ **Test 3.3.1**: Create technical chart with candlesticks
- ✅ **Test 战斗.3.2**: Create technical chart with line chart
- ✅ **Test 3.3.3**: Create technical chart with Bollinger Bands
- ✅ **Test 3.3.4**: Create technical chart with SMA indicators
- ✅ **Test 3.3.5**: Create technical chart with RSI subplot
- ✅ **Test 3.3.6**: Create technical chart with volume subplot
- ✅ **Test 3.3.7**: Create technical chart with time range filtering

---

## 4. YAML Exporter Tests (`test_yaml_exporter.py`)

### 4.1 Export Functionality
- ✅ **Test 4.1.1**: Export portfolio to YAML (complete data)
- ✅ **Test 4.1.2**: Export portfolio to YAML (missing market data)
- ✅ **Test 4.1.3**: Export stock analysis to YAML
- ✅ **Test 4.1.4**: YAML structure validation
- ✅ **Test 4.1.5**: YAML data type validation (numbers, strings, dates)
- ✅ **Test 4.1.6**: YAML with None/null values (should handle gracefully)

### 4.2 Data Mapping
- ✅ **Test 4.2.1**: Map position data correctly
- ✅ **Test 4.2.2**: Map market data correctly
- ✅ **Test 4.2.3**: Map technical indicators correctly
- ✅ **Test 4.2.4**: Map financial data correctly (quarterly_revenue, net_income)

---

## 5. Integration Tests (`test_data_pipeline.py`)

### 5.1 End-to-End Data Flow
- ✅ **Test 5.1.1**: Complete flow: Add position → Fetch data → Store → Retrieve
- ✅ **Test 5.1.2**: Complete flow: Refresh market data → Update database → Verify update
- ✅ **Test 5.1.3**: Complete flow: Calculate indicators → Store → Retrieve
- ✅ **Test 5.1.4**: Complete flow: Portfolio creation → Position addition → Market data fetch → Analysis

### 5.2 API Integration
- ✅ **Test 5.2.1**: yfinance API response validation
- ✅ **Test 5.2.2**: Handle yfinance API rate limiting
- ✅ **Test 5.2.3**: Handle yfinance API errors (invalid ticker)
- ✅ **Test 5.2.4**: Handle yfinance API timeouts

---

## 6. Functional Tests (`test_portfolio_management.py`)

### 6.1 Portfolio CRUD Operations
- ✅ **Test 6.1.1**: Create portfolio through workflow
- ✅ **Test 6.1.2**: Add multiple positions to portfolio
- ✅ **Test 6.1.3**: Update position quantities and prices
- ✅ **Test 6.1.4**: Delete position (should update portfolio metrics)
- ✅ **Test 6.1.5**: Delete portfolio (should cascade delete positions)

### 6.2 Portfolio Metrics
- ✅ **Test 6.2.1**: Calculate total portfolio value correctly
- ✅ **Test 6.2.2**: Calculate total P/L correctly
- ✅ **Test 6.2.3**: Calculate total P/L percentage correctly
- ✅ **Test 6.2.4**: Handle division by zero (zero cost basis)
- ✅ **Test 6.2.5**: Portfolio metrics with missing market data

---

## 7. Edge Cases & Error Handling

### 7.1 Data Validation
- ✅ **Test 7.1.1**: Invalid ticker symbols
- ✅ **Test 7.1.2**: Negative quantities (should reject)
- ✅ **Test 7.1.3**: Negative prices (should reject)
- ✅ **Test 7.1.4**: Future dates (should handle appropriately)
- ✅ **Test 7.1.5**: Very large numbers (market cap, prices)

### 7.2 Database Edge Cases
- ✅ **Test 7.2.1**: Concurrent database access
- ✅ **Test 7.2.2**: Database file locked
- ✅ **Test 7.2.3**: Corrupted database file
- ✅ **Test 7.2.4**: Missing database file (should create)

### 7.3 Network & API Edge Cases
- ✅ **Test 7.3.1**: No internet connection
- ✅ **Test 7.3.2**: API timeout
- ✅ **Test 7.3.3**: Partial API response (missing fields)
- ✅ **Test 7.3.4**: API returns empty data

---

## 8. Performance Tests

### 8.1 Database Performance
- ✅ **Test 8.1.1**: Bulk insert positions (performance)
- ✅ **Test 8.1.2**: Query performance with large dataset
- ✅ **Test 8.1.3**: Database cleanup performance

### 8.2 Data Collection Performance
- ✅ **Test 8.2.1**: Batch fetch multiple stocks (should respect rate limits)
- ✅ **Test 8.2.2**: Cache hit performance vs. API call
- ✅ **Test 8.2.3**: Historical data fetch performance (large date ranges)

---

## Implementation Priority

### Phase 1 (Critical - Week 1)
1. ✅ Database CRUD operations (Test Suite 1)
2. ✅ Cache and fallback logic (Test Suite 2.1, 2.2)
3. ✅ Data collector error handling (Test Suite 2.5)

### Phase 2 (Important - Week 2)
4. ✅ Technical indicators calculation (Test Suite 2.4)
5. ✅ Chart generation (Test Suite 3)
6. ✅ YAML export validation (Test Suite 4)

### Phase 3 (Enhancement - Week 3)
7. ✅ Integration tests (Test Suite 5)
8. ✅ Functional tests (Test Suite 6)
9. ✅ Edge cases and error handling (Test Suite 7)

### Phase 4 (Optimization - Week 4)
10. ✅ Performance tests (Test Suite 8)

---

## Test Framework Setup

### Dependencies
```txt
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-asyncio==0.21.1
faker==20.1.0  # For generating test data
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_database.py

# Run specific test
pytest tests/unit/test_database.py::test_create_portfolio_valid
```

---

## Test Data Management

### Fixtures
- In-memory SQLite database for testing
- Mock yfinance responses
- Sample portfolio data
- Sample market data
- Sample technical indicator data

### Test Isolation
- Each test uses a fresh database instance
- Tests clean up after themselves
- No external dependencies (API calls mocked)

---

## Coverage Goals

- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: Critical paths 100%
- **Functional Tests**: All user workflows covered

---

## Notes

- Tests should be independent and can run in any order
- Use fixtures for common setup/teardown
- Mock external API calls (yfinance) for unit tests
- Use real API calls only in integration tests (marked accordingly)
- All tests should be deterministic (no random failures)

Next steps
To continue, implement the remaining tests from TEST_PLAN.md in priority order:
Complete database tests (Test Suite 1)
Data collector tests (Test Suite 2)
Analysis tests (Test Suite 3)
Continue through remaining suites
Running the first test