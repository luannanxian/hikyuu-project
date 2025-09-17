# MySQL MCP 服务器文档

## 概述

MySQL MCP服务器提供与MySQL数据库的直接交互功能，支持执行SQL查询和数据库操作。该服务器支持多数据库模式，并具有模式特定的权限控制。

## 基本信息

- **服务器名称**: `mysql`
- **版本**: vundefined
- **模式**: 多数据库模式已启用
- **权限控制**: 模式特定权限已启用

## 可用工具

### mysql_query

执行SQL查询的核心工具，支持多种数据库操作。

#### 功能描述
- 执行INSERT、UPDATE、DDL和READ操作
- 支持复杂的SQL查询语句
- 具有模式特定的权限控制

#### 输入参数

| 参数名 | 类型 | 必需 | 描述 |
|-------|------|------|------|
| `sql` | string | ✓ | 要执行的SQL查询语句 |

#### 使用示例

##### 1. 查询数据
```sql
-- 查询用户表中的所有记录
SELECT * FROM users;

-- 按条件查询
SELECT id, name, email FROM users WHERE status = 'active';

-- 联表查询
SELECT u.name, p.title 
FROM users u 
JOIN posts p ON u.id = p.user_id 
WHERE u.created_at > '2024-01-01';
```

##### 2. 插入数据
```sql
-- 插入单条记录
INSERT INTO users (name, email, status) 
VALUES ('张三', 'zhangsan@example.com', 'active');

-- 批量插入
INSERT INTO products (name, price, category_id) VALUES
('iPhone 15', 7999.00, 1),
('MacBook Pro', 15999.00, 2),
('iPad Air', 4599.00, 3);
```

##### 3. 更新数据
```sql
-- 更新单条记录
UPDATE users 
SET last_login = NOW() 
WHERE id = 1;

-- 批量更新
UPDATE products 
SET price = price * 0.9 
WHERE category_id = 1 AND created_at < '2024-01-01';
```

##### 4. 数据定义语言 (DDL)
```sql
-- 创建表
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 修改表结构
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 创建索引
CREATE INDEX idx_user_email ON users(email);
```

## 最佳实践

### 1. 安全性考虑

#### SQL注入防护
- 始终使用参数化查询
- 避免动态拼接SQL语句
- 验证输入数据的格式和类型

#### 权限管理
- 使用最小权限原则
- 定期审查数据库用户权限
- 区分读写权限

### 2. 性能优化

#### 查询优化
```sql
-- 使用EXPLAIN分析查询计划
EXPLAIN SELECT * FROM users WHERE email = 'example@test.com';

-- 合理使用索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at);

-- 限制返回结果数量
SELECT * FROM large_table LIMIT 100;
```

#### 连接管理
- 避免长时间占用连接
- 合理设置查询超时时间
- 使用连接池优化资源使用

### 3. 数据操作建议

#### 事务处理
```sql
-- 使用事务确保数据一致性
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

#### 批量操作
```sql
-- 批量插入优于单条插入
INSERT INTO logs (message, level, created_at) VALUES
('Info message 1', 'INFO', NOW()),
('Error message', 'ERROR', NOW()),
('Debug message', 'DEBUG', NOW());
```

## 常见使用场景

### 1. 数据分析查询
```sql
-- 用户注册趋势分析
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_users
FROM users 
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY date;

-- 产品销售统计
SELECT 
    p.name,
    SUM(oi.quantity) as total_sold,
    SUM(oi.quantity * oi.price) as revenue
FROM products p
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'completed'
GROUP BY p.id, p.name
ORDER BY revenue DESC;
```

### 2. 数据维护操作
```sql
-- 清理过期数据
DELETE FROM sessions WHERE expires_at < NOW();

-- 更新统计信息
UPDATE posts p 
SET comment_count = (
    SELECT COUNT(*) 
    FROM comments c 
    WHERE c.post_id = p.id
);

-- 数据归档
INSERT INTO archived_logs 
SELECT * FROM logs 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
```

### 3. 系统监控查询
```sql
-- 检查表大小
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size in MB'
FROM information_schema.tables 
WHERE table_schema = DATABASE()
ORDER BY (data_length + index_length) DESC;

-- 活跃连接监控
SHOW PROCESSLIST;

-- 慢查询分析
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;
```

## 故障排除

### 常见错误及解决方案

#### 1. 连接错误
```
Error: Can't connect to MySQL server
```
**解决方案**:
- 检查MySQL服务状态
- 验证连接参数（主机、端口、用户名、密码）
- 确认网络连接

#### 2. 权限错误
```
Error: Access denied for user 'username'@'host'
```
**解决方案**:
- 检查用户权限设置
- 验证数据库和表的访问权限
- 确认用户的主机访问权限

#### 3. 语法错误
```
Error: You have an error in your SQL syntax
```
**解决方案**:
- 仔细检查SQL语法
- 验证表名和字段名的正确性
- 使用SQL验证工具

#### 4. 性能问题
**症状**: 查询执行缓慢
**解决方案**:
- 使用EXPLAIN分析查询计划
- 添加适当的索引
- 优化WHERE条件
- 考虑查询结果分页

## 配置说明

### 多数据库模式
当前服务器启用了多数据库模式，这意味着：
- 可以同时访问多个数据库
- 需要在查询中指定数据库名（如需要）
- 权限按数据库级别进行控制

### 模式特定权限
启用了模式特定权限控制：
- 不同操作类型有不同的权限要求
- INSERT、UPDATE、DDL操作需要写权限
- SELECT操作需要读权限

## 相关资源

- [MySQL官方文档](https://dev.mysql.com/doc/)
- [SQL语法参考](https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html)
- [MySQL性能优化指南](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)

---

*最后更新: 2025年8月25日*
