import mysql.connector
from mysql.connector import Error, pooling
from typing import List, Tuple, Optional, Dict, Any
import logging
from .config.database_config import DATABASE_CONFIG, CREATE_TABLES_SQL

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MySQLManager:
    """MySQL数据库管理类"""
    
    def __init__(self):
        self.connection_pool = None
        self.initialize_pool()
        self.initialize_tables()
    
    def ensure_database(self):
        """确保数据库存在，如果不存在则创建"""
        try:
            # 先连接而不指定数据库
            config_without_db = {k: v for k, v in DATABASE_CONFIG.items() if k != 'database'}
            connection = mysql.connector.connect(**config_without_db)
            cursor = connection.cursor()
            
            # 检查数据库是否存在
            cursor.execute(f"SHOW DATABASES LIKE '{DATABASE_CONFIG['database']}'")
            result = cursor.fetchone()
            
            if not result:
                # 创建数据库
                cursor.execute(f"CREATE DATABASE {DATABASE_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                logger.info(f"数据库 {DATABASE_CONFIG['database']} 创建成功")
            else:
                logger.info(f"数据库 {DATABASE_CONFIG['database']} 已存在")
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
            
        except Error as e:
            logger.error(f"确保数据库存在失败: {e}")
            # 如果失败，可能用户没有创建数据库权限，继续尝试连接原有数据库
            return False

    def initialize_pool(self):
        """初始化数据库连接池"""
        try:
            # 首先确保数据库存在
            self.ensure_database()
            
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name=DATABASE_CONFIG['pool_name'],
                pool_size=DATABASE_CONFIG['pool_size'],
                **{k: v for k, v in DATABASE_CONFIG.items() 
                   if k not in ['pool_size', 'pool_name']}
            )
            logger.info("数据库连接池初始化成功")
        except Error as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    def get_connection(self):
        """从连接池获取连接"""
        try:
            return self.connection_pool.get_connection()
        except Error as e:
            logger.error(f"获取数据库连接失败: {e}")
            raise
    
    def initialize_tables(self):
        """初始化数据库表结构"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            for table_name, create_sql in CREATE_TABLES_SQL.items():
                try:
                    cursor.execute(create_sql)
                    logger.info(f"表 {table_name} 初始化成功")
                except Error as e:
                    logger.error(f"表 {table_name} 初始化失败: {e}")
            
            connection.commit()
            cursor.close()
            connection.close()
            
        except Error as e:
            logger.error(f"数据库表初始化失败: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """执行查询语句"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            
            return result
            
        except Error as e:
            logger.error(f"查询执行失败: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行插入语句，返回插入的ID"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute(query, params or ())
            connection.commit()
            
            return cursor.lastrowid
            
        except Error as e:
            logger.error(f"插入执行失败: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行更新语句，返回影响的行数"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute(query, params or ())
            connection.commit()
            
            return cursor.rowcount
            
        except Error as e:
            logger.error(f"更新执行失败: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """批量执行插入或更新"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.executemany(query, params_list)
            connection.commit()
            
            return cursor.rowcount
            
        except Error as e:
            logger.error(f"批量执行失败: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def check_connection(self) -> bool:
        """检查数据库连接是否正常"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return result[0] == 1
        except Error:
            return False
    
    def get_factor_count(self) -> int:
        """获取因子数量"""
        query = "SELECT COUNT(*) FROM factors"
        result = self.execute_query(query)
        return result[0][0] if result else 0
    
    def get_factor_performance_stats(self, factor_id: int) -> Dict[str, Any]:
        """获取因子绩效统计"""
        query = """
        SELECT 
            AVG(ic_value) as avg_ic,
            AVG(icir_value) as avg_icir,
            AVG(annual_return) as avg_annual_return,
            AVG(sharpe_ratio) as avg_sharpe_ratio,
            COUNT(*) as evaluation_count
        FROM factor_performance 
        WHERE factor_id = %s
        """
        result = self.execute_query(query, (factor_id,))
        
        if result and result[0]:
            return {
                'avg_ic': result[0][0],
                'avg_icir': result[0][1],
                'avg_annual_return': result[0][2],
                'avg_sharpe_ratio': result[0][3],
                'evaluation_count': result[0][4]
            }
        return {}


# 全局数据库管理器实例
db_manager = None

def get_db_manager() -> MySQLManager:
    """获取全局数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = MySQLManager()
    return db_manager


if __name__ == "__main__":
    # 测试数据库连接
    manager = get_db_manager()
    if manager.check_connection():
        print("数据库连接测试成功")
        print(f"当前因子数量: {manager.get_factor_count()}")
    else:
        print("数据库连接测试失败")
