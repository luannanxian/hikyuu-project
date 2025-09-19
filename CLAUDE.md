# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a quantitative trading project based on the Hikyuu framework for financial market analysis and factor mining. The project consists of two main systems:

1. **Factor Factory System** (`factor_factory/`) - A comprehensive factor mining and management system
2. **Quantitative Trading Strategy** (documented in `docs/`) - A multi-factor stock screening strategy

## Environment Setup

### Conda Virtual Environment
This project must run in a conda virtual environment:
- **Environment name**: `pybroker-313`
- **Activate environment**: `conda activate pybroker-313`
- Always activate this environment before running any commands

### Available MCP Tools
Two MCP (Model Context Protocol) tools are available:
1. **DeepWiki MCP** - For documentation and knowledge base access
   - Address: https://mcp.deepwiki.com/sse
2. **MySQL MCP** - For direct database operations and queries
   - Address: http://192.168.3.98:3000/mcp

To use MCP tools, mention them explicitly when needed:
- "使用MySQL MCP查询数据库" - Use MySQL MCP to query the database
- "使用DeepWiki MCP搜索文档" - Use DeepWiki MCP to search documentation

## Development Commands

### Environment Activation
- **Activate conda environment**: `conda activate pybroker-313`

### Testing
- **Run integration tests**: `python test_factor_factory.py`
- **Run unit test suite**: `python tests/run_tests.py`
- **Run specific unit tests**: `python tests/run_tests.py --module test_mysql_manager`
- **Test database connection**: `python -m factor_factory.mysql_manager`
- **Test factor registry**: `python -m factor_factory.factor_registry`
- **Test multi-factor engine**: `python -m factor_factory.multi_factor_engine`

### Examples
- **Quick start example**: `python examples/simple_factor_mining.py`
- **Complete factor mining**: `python examples/factor_mining_example.py`

### Factor Factory System
- **Initialize database**: Database tables are auto-created when running any factor factory module
- **Run full system test**: `python test_factor_factory.py`

## Architecture Overview

### Factor Factory System
The factor factory system provides complete factor lifecycle management:

- **MySQLManager** (`factor_factory/mysql_manager.py`) - Database connection pooling and operations
- **FactorRegistry** (`factor_factory/factor_registry.py`) - Factor registration, search, and management
- **MultiFactorEngine** (`factor_factory/multi_factor_engine.py`) - Batch factor evaluation using Hikyuu's MultiFactor framework
- **EvaluationPipeline** (`factor_factory/evaluation_pipeline.py`) - Automated evaluation and performance tracking

### Key Design Patterns
- **Singleton Pattern**: Each core component has a global instance accessed via `get_*()` functions
- **Factory Pattern**: Centralized creation and management of factors
- **Pipeline Pattern**: Automated evaluation workflow for factors

### Database Schema
The system uses MySQL with three main tables:
- `factors` - Factor definitions and metadata
- `factor_performance` - IC/ICIR evaluation results
- `backtest_results` - Backtest performance metrics

## Hikyuu Framework Integration

### Essential Context
- This project heavily relies on the Hikyuu quantitative framework
- **Always initialize Hikyuu first**: Call `load_hikyuu()` before using any Hikyuu functionality
- **Stock codes**: Use format like 'sh000001' (Shanghai) or 'sz000001' (Shenzhen)
- **Query objects**: Use `Query(-N)` for last N data points

### Factor Expression Safety
- Factor expressions use `eval()` with a restricted context for security
- Supported functions include: MA, EMA, RSI, MACD, CLOSE, OPEN, HIGH, LOW, VOL, etc.
- **Critical**: Always validate expressions before execution

### Data Access Patterns
- **StockManager**: Access via `StockManager.instance()` for stock data
- **A-Stock filtering**: Use `stock.type in (constant.STOCKTYPE_A, constant.STOCKTYPE_A_BJ)`
- **MultiFactor evaluation**: Create indicators and evaluate across stock universes

## Configuration

### Database Configuration
Database settings are in `factor_factory/config/database_config.py`:
- Host: 192.168.3.46
- Database: factor_factory
- Connection pooling enabled with 5 connections

### File Structure Conventions
- **Core system**: `factor_factory/` directory contains all core modules
- **Examples**: `examples/` directory contains usage examples and tutorials
- **Documentation**: `docs/` directory contains design documents
- **Unit tests**: `tests/` directory contains comprehensive test suite
- **Integration tests**: `test_factor_factory.py` at project root
- **Configuration**: `factor_factory/config/` with environment variable support

## Development Guidelines

### Working with Factors
1. Register new factors using `FactorRegistry.register_factor()`
2. Use `MultiFactorEngine.create_factor_indicator()` to create Hikyuu indicators
3. Evaluate factors with `evaluate_single_factor()` or `batch_evaluate_factors()`
4. Results are automatically saved to the database

### Error Handling
- All database operations include proper error handling and logging
- Factor evaluation failures are logged but don't stop batch processing
- Connection pooling handles database reconnection automatically

### Testing Approach
- Use the comprehensive test suite in `test_factor_factory.py`
- Test individual components using their `if __name__ == "__main__"` blocks
- Always test database connectivity before running factor operations

## Important Notes

### Dependencies
- Requires Hikyuu framework installation
- MySQL connector for database operations
- Standard Python scientific libraries (numpy, pandas implied by Hikyuu)

### Performance Considerations
- Database connection pooling is configured for optimal performance
- Factor evaluation can be CPU-intensive for large stock universes
- Use Query objects to limit data scope for testing

### Security
- **Enhanced expression validation**: Multi-layer security checks for factor expressions
- **Environment variables**: Database credentials loaded from `.env` files
- **Restricted eval context**: Factor expressions execute with disabled `__builtins__`
- **Input sanitization**: Comprehensive validation against injection attacks
- **No direct user input**: All expressions must pass security validation