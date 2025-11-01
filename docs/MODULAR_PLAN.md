# Finance Dashboard - Modularization Plan

## 1. Directory Structure

```
finance_dashboard/
├── app/                      # Main application package
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Main entry point
│   │
│   ├── config/               # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py       # App settings and feature flags
│   │   ├── logging_config.py # Logging configuration
│   │   └── constants.py      # App-wide constants
│   │
│   ├── database/             # Database layer
│   │   ├── __init__.py
│   │   ├── models/           # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py       # Base model
│   │   │   ├── portfolio.py
│   │   │   └── market_data.py
│   │   ├── repositories/     # Database operations
│   │   │   ├── __init__.py
│   │   │   ├── base.py       # Base repository
│   │   │   └── portfolio_repo.py
│   │   └── session.py        # Session management
│   │
│   ├── domain/               # Business logic and domain models
│   │   ├── __init__.py
│   │   ├── entities/         # Business entities
│   │   └── services/         # Domain services
│   │
│   ├── api/                  # External services and APIs
│   │   ├── __init__.py
│   │   ├── clients/          # API clients
│   │   │   └── yfinance_client.py
│   │   └── schemas/          # Request/response schemas
│   │
│   ├── ui/                   # Presentation layer
│   │   ├── __init__.py
│   │   ├── components/       # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── layout/       # Layout components
│   │   │   ├── charts/       # Chart components
│   │   │   └── forms/        # Form components
│   │   └── pages/            # Streamlit pages
│   │       ├── __init__.py
│   │       ├── dashboard/
│   │       ├── portfolio/
│   │       └── settings/
│   │
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── decorators.py     # Common decorators
│       ├── validators.py     # Data validation
│       └── helpers.py        # Helper functions
│
├── tests/                    # Test suite
│   ├── unit/
│   │   ├── test_models/
│   │   ├── test_services/
│   │   └── test_components/
│   └── integration/
│
├── scripts/                  # Utility scripts
├── .env.example              # Environment template
├── requirements/             # Dependency management
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── README.md
```

## 2. Migration Strategy

### Phase 1: Foundation (COMPLETED) ✅
1. **Set up package structure**
   - ✅ Create directory structure
   - ✅ Set up `pyproject.toml` for modern packaging
   - ✅ Configure logging and settings management

2. **Database Layer**
   - ✅ Move models to `app/database/models/`
   - ✅ Implement base repository pattern
   - ✅ Set up database migrations (Alembic)

### Phase 2: Core Services (COMPLETED) ✅
1. **Domain Layer**
   - ✅ Define business entities (Portfolio, Position, Transaction)
   - ✅ Implement domain services (PortfolioService)
   - ✅ Add validation logic (Pydantic models)

2. **API Layer**
   - ✅ Create API clients (structure ready)
   - ✅ Implement data transformation
   - ✅ Add error handling and retries

### Phase 3: UI Components (IN PROGRESS) 🚧

1. **Core UI Components** (1-2 days)
   - [x] Base components (Card, Button, etc.)
   - [x] Chart components (Line, Bar, Pie, Candlestick)
   - [ ] Form components (FormField, Form, FilterBar) - IN PROGRESS
   - [ ] Layout system (Grid, Sidebar, Tabs)
   - [ ] Theming and styling system

2. **Page Components** (2-3 days)
   - [ ] Dashboard Page
     - Portfolio summary cards
     - Performance charts
     - Recent activity feed
   - [ ] Portfolio Management
     - Portfolio list view
     - Create/edit portfolio form
     - Position management
   - [ ] Stock Analysis
     - Individual stock view
     - Technical indicators
     - Historical data visualization
   - [ ] Technical Alerts
     - Alert notifications
     - Alert configuration
     - Alert history

3. **State Management** (1 day)
   - [ ] Session state management
   - [ ] Form state handling
   - [ ] Data caching
   - [ ] User preferences

### Phase 4: Data Layer Integration (2 days)
1. **Database Integration**
   - [ ] Implement portfolio repository
   - [ ] Add position management
   - [ ] Set up market data caching
   - [ ] Add test data initialization

2. **API Integration**
   - [ ] YFinance client implementation
   - [ ] Data fetching services
   - [ ] Error handling and retries
   - [ ] Rate limiting

### Phase 5: Feature Parity (2-3 days)
1. **Core Features**
   - [ ] Portfolio creation and management
   - [ ] Position tracking
   - [ ] Real-time market data
   - [ ] Technical analysis tools
   - [ ] Alert system

2. **User Experience**
   - [ ] Form validation
   - [ ] Loading states
   - [ ] Error handling
   - [ ] Responsive design

### Phase 6: Testing & Optimization (2 days)
1. **Testing**
   - [ ] Unit tests for core logic
   - [ ] Integration tests
   - [ ] UI component tests
   - [ ] End-to-end tests

2. **Performance**
   - [ ] Data caching
   - [ ] Lazy loading
   - [ ] Bundle optimization
   - [ ] Performance monitoring

## 3. Key Improvements

1. **Better Separation of Concerns**
   - Clear distinction between layers
   - Single responsibility principle
   - Dependency inversion

2. **Testability**
   - Isolated components
   - Mockable dependencies
   - Test utilities

3. **Scalability**
   - Modular architecture
   - Easy to extend
   - Feature flags

4. **Maintainability**
   - Consistent patterns
   - Documentation
   - Type hints

## 4. Implementation Guidelines

1. **Dependencies**
   - Use dependency injection for services and repositories
   - Avoid circular imports by following the dependency flow: models → repositories → services → API → UI
   - Document dependencies in module docstrings
   - Use type hints consistently
   - Manage external dependencies through requirements/

2. **Error Handling**
   - Centralized error handling in `app/utils/error_handlers.py`
   - Custom exceptions in `app/utils/exceptions.py`
   - User-friendly error messages in the UI
   - Log all errors with appropriate context
   - Implement retry mechanisms for API calls

3. **Logging & Monitoring**
   - Structured logging with JSON formatting
   - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Redact sensitive information
   - Performance metrics collection
   - Request/response logging for API calls

4. **Configuration**
   - Environment variables via `.env`
   - Type-safe settings with Pydantic
   - Feature flags for experimental features
   - Environment-specific configurations (dev/staging/prod)
   - Secret management

## 5. Next Steps

1. **Immediate Actions**
   - [x] Set up project structure
   - [x] Configure tooling and dependencies
   - [x] Create base classes and models
   - [x] Set up database and migrations

2. **Current Focus**
   - [ ] Complete form components implementation
   - [ ] Implement portfolio management UI
   - [ ] Set up data fetching services
   - [ ] Add error handling and loading states

3. **Quick Wins**
   - [ ] Implement basic dashboard layout
   - [ ] Add sample data visualization
   - [ ] Set up basic navigation
   - [ ] Add user feedback (toasts, loading spinners)

3. **Future Considerations**
   - [ ] Add monitoring
   - [ ] Implement caching
   - [ ] Performance optimization

## 6. Example Implementation

### app/main.py
```python
import streamlit as st
from app.config.settings import get_settings
from app.database.init_db import init_database
from app.ui.app import create_app

def main():
    # Initialize configuration
    settings = get_settings()
    
    # Initialize database
    init_database()
    
    # Create and run the app
    app = create_app(settings)
    app.run()

if __name__ == "__main__":
    main()
```

### app/database/models/base.py
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func

class BaseModel:
    """Base model class that includes common fields and methods."""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

# Create declarative base
Base = declarative_base(cls=BaseModel)
```

### app/domain/services/portfolio_service.py
```python
from typing import List, Optional
from app.domain.entities.portfolio import Portfolio
from app.database.repositories.portfolio_repo import PortfolioRepository

class PortfolioService:
    """Service for portfolio-related business logic."""
    
    def __init__(self, portfolio_repo: PortfolioRepository):
        self.portfolio_repo = portfolio_repo
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get a portfolio by ID."""
        return self.portfolio_repo.get_by_id(portfolio_id)
    
    def list_portfolios(self) -> List[Portfolio]:
        """List all portfolios."""
        return self.portfolio_repo.list_all()
    
    # Add other business logic methods...