# 单元测试套件

这个目录包含因子工厂系统的单元测试。

## 测试文件说明

### 核心测试模块

- `test_mysql_manager.py` - MySQL管理器测试
- `test_factor_registry.py` - 因子注册器测试
- `test_multi_factor_engine.py` - MultiFactorEngine测试

### 安全性测试

- `TestExpressionSecurity` - 表达式安全性专项测试，包括：
  - SQL注入防护测试
  - 脚本注入防护测试
  - 系统访问防护测试

## 运行测试

### 运行所有测试
```bash
cd tests
python run_tests.py
```

### 运行特定测试模块
```bash
cd tests
python run_tests.py --module test_mysql_manager
python run_tests.py --module test_factor_registry
python run_tests.py --module test_multi_factor_engine
```

### 安静模式运行（减少日志输出）
```bash
cd tests
python run_tests.py --quiet
```

### 使用pytest运行（如果已安装）
```bash
cd tests
pytest -v
pytest test_mysql_manager.py -v
```

## 测试覆盖范围

### MySQL管理器测试
- ✅ 数据库配置加载
- ✅ 数据库连接和创建
- ✅ 连接池初始化
- ✅ 异常处理
- ✅ 单例模式

### 因子注册器测试
- ✅ 因子注册和查询
- ✅ 因子更新和删除
- ✅ 搜索功能
- ✅ 绩效数据保存
- ✅ 数据格式化

### MultiFactorEngine测试
- ✅ 表达式安全验证
- ✅ 因子指标创建
- ✅ A股列表获取
- ✅ 统计计算功能

### 安全性测试
- ✅ 危险关键词检测
- ✅ 恶意代码模式识别
- ✅ 输入长度限制
- ✅ 字符集验证

## 测试最佳实践

### 1. Mock使用
测试中大量使用Mock对象避免实际的数据库连接：
```python
@patch('factor_factory.factor_registry.get_db_manager')
def test_register_factor(self, mock_get_db):
    mock_get_db.return_value = Mock()
```

### 2. 异常测试
确保异常情况得到正确处理：
```python
with self.assertRaises(ValueError):
    engine._validate_expression("import os")
```

### 3. 边界条件测试
测试各种边界条件和极端情况：
```python
# 空输入、None值、过长输入等
```

## 添加新测试

### 1. 创建新的测试文件
```python
# tests/test_new_module.py
import unittest
from unittest.mock import Mock, patch

class TestNewModule(unittest.TestCase):
    def test_function(self):
        self.assertEqual(1, 1)
```

### 2. 在run_tests.py中会自动发现新测试

### 3. 遵循命名约定
- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试方法：`test_*`

## 持续集成

测试套件设计为可以集成到CI/CD流水线中：

```bash
# 在CI中运行
python tests/run_tests.py --quiet
echo $? # 检查退出代码
```

## 依赖说明

测试运行需要的依赖：
- unittest（Python标准库）
- unittest.mock（Python标准库）
- pytest（可选，用于更好的测试体验）

测试不需要实际的数据库连接或Hikyuu环境，所有外部依赖都通过Mock模拟。