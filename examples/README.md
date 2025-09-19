# 因子工厂示例

这个目录包含了因子工厂系统的各种使用示例。

## 示例文件说明

### 1. `simple_factor_mining.py` - 快速入门示例 ⭐
**推荐新手从这里开始**

```bash
cd examples
python simple_factor_mining.py
```

包含功能：
- 快速开始示例
- 批量因子挖掘
- 查看因子库状态
- 创建自定义因子

### 2. `factor_mining_example.py` - 完整流程示例
完整的因子挖掘和评估流程

```bash
cd examples
python factor_mining_example.py
```

包含功能：
- 创建因子候选池
- 注册因子到数据库
- 快速评估因子
- 筛选有效因子
- 生成因子挖掘报告
- 创建因子组合建议

## 运行前准备

1. **激活conda环境**：
   ```bash
   conda activate pybroker-313
   ```

2. **配置环境变量**：
   复制项目根目录的 `.env.example` 为 `.env` 并配置数据库信息

3. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

## 使用建议

1. **新手用户**：从 `simple_factor_mining.py` 开始，选择选项1（快速开始示例）
2. **进阶用户**：运行 `factor_mining_example.py` 体验完整流程
3. **自定义开发**：参考示例代码创建自己的因子挖掘策略

## 常见问题

### Q: 示例运行失败怎么办？
A: 请检查：
1. 是否激活了正确的conda环境
2. 数据库连接是否正常
3. Hikyuu框架是否正确初始化

### Q: 如何添加新的因子？
A: 参考 `simple_factor_mining.py` 中的 `create_custom_factor()` 函数

### Q: 如何查看因子评估结果？
A: 使用 `simple_factor_mining.py` 选项3查看因子库状态