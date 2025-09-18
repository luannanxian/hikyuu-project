# 数据库配置
DATABASE_CONFIG = {
    'host': '192.168.3.46',
    'database': 'factor_factory',
    'user': 'remote',
    'password': 'remote123456',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': True,
    'pool_size': 5,
    'pool_name': 'factor_factory_pool'
}

# 表结构定义
CREATE_TABLES_SQL = {
    'factors': """
        CREATE TABLE IF NOT EXISTS factors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            expression TEXT NOT NULL,
            category VARCHAR(50),
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            status ENUM('active', 'testing', 'inactive') DEFAULT 'testing',
            description TEXT,
            INDEX idx_status (status),
            INDEX idx_category (category)
        )
    """,
    'factor_performance': """
        CREATE TABLE IF NOT EXISTS factor_performance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            factor_id INT NOT NULL,
            evaluation_date DATE NOT NULL,
            ic_value FLOAT,
            icir_value FLOAT,
            annual_return FLOAT,
            sharpe_ratio FLOAT,
            max_drawdown FLOAT,
            information_ratio FLOAT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (factor_id) REFERENCES factors(id) ON DELETE CASCADE,
            INDEX idx_factor_date (factor_id, evaluation_date),
            INDEX idx_evaluation_date (evaluation_date)
        )
    """,
    'backtest_results': """
        CREATE TABLE IF NOT EXISTS backtest_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            factor_id INT NOT NULL,
            backtest_date DATE NOT NULL,
            total_return FLOAT,
            annual_return FLOAT,
            volatility FLOAT,
            sharpe_ratio FLOAT,
            max_drawdown FLOAT,
            trade_count INT,
            win_rate FLOAT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (factor_id) REFERENCES factors(id) ON DELETE CASCADE,
            INDEX idx_factor_backtest (factor_id, backtest_date)
        )
    """
}
