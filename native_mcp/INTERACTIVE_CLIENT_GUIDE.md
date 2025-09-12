# MCP Interactive Client

一个功能完整的命令行交互式MCP（Model Context Protocol）客户端，支持与MCP服务器进行实时对话式交互。

## 功能特性

✅ **完整的MCP协议支持**
- 工具调用（Tools）
- 资源读取（Resources）  
- 提示获取（Prompts）
- 流式传输支持

✅ **友好的命令行界面**
- 直观的命令语法
- 自动命令解析
- 参数类型自动转换
- 内置帮助系统

✅ **灵活的参数格式**
- 简单参数：`name=value`
- JSON格式：`data='{"key": "value"}'`
- 布尔值：`enabled=true`
- 数组：`items='[1,2,3]'`

## 使用方法

### 启动客户端

```bash
# 连接到本地服务器（默认端口3000）
python interactive_client.py

# 连接到指定服务器
python interactive_client.py localhost 3001

# 或者运行演示
python demo_interactive.py
```

### 基本命令

#### 1. 服务器管理
```bash
mcp> status                    # 显示连接状态和服务器信息
mcp> ping                      # 测试服务器连接
mcp> refresh                   # 刷新服务器能力列表
```

#### 2. 工具操作
```bash
mcp> tool                      # 列出所有可用工具
mcp> tool help add             # 查看工具帮助
mcp> tool call add a=5 b=10    # 调用工具
mcp> add a=5 b=10              # 直接调用（快捷方式）
mcp> tool stream countdown start=5  # 流式工具调用
```

#### 3. 资源操作
```bash
mcp> resource                  # 列出所有资源
mcp> resource help info://server  # 查看资源帮助
mcp> resource read info://server   # 读取资源
mcp> info://server             # 直接读取（快捷方式）
```

#### 4. 提示操作
```bash
mcp> prompt                    # 列出所有提示
mcp> prompt help greeting      # 查看提示帮助
mcp> prompt get greeting name=Alice language=English
```

#### 5. 帮助和退出
```bash
mcp> help                      # 显示所有命令帮助
mcp> quit                      # 退出客户端
```

### 参数格式示例

```bash
# 字符串参数
mcp> greet name="Alice" message='Hello World'

# 数字参数
mcp> calculate a=15 b=27 operation=add

# 布尔参数
mcp> toggle_feature enabled=true debug=false

# JSON对象参数
mcp> complex_tool data='{"name": "test", "count": 5, "tags": ["a", "b"]}'

# 混合参数
mcp> advanced_call text="Hello" count=3 options='{"mode": "fast"}'
```

## 交互式演示

### 运行完整演示
```bash
python demo_interactive.py
```

选择选项：
1. **自动演示** - 展示所有功能
2. **使用示例** - 显示命令示例
3. **交互式体验** - 启动完整的交互式会话

### 快速测试
```bash
python test_interactive.py
```

## 高级功能

### 1. 命令快捷方式
- 直接使用工具名：`add a=5 b=10` 代替 `tool call add a=5 b=10`
- 直接使用URI：`info://server` 代替 `resource read info://server`

### 2. 流式工具调用
支持实时流式输出的工具：
```bash
mcp> tool stream fibonacci count=10
mcp> tool stream countdown start=5
```

### 3. 批量操作
可以通过脚本批量执行命令：
```bash
echo -e "status\ntool\nresource\nquit" | python interactive_client.py
```

### 4. 错误处理
- 自动检测连接状态
- 友好的错误信息显示
- 参数验证和类型转换

## 架构设计

### 核心组件
- **MCPInteractiveClient**: 主要的交互式客户端类
- **命令解析器**: 智能解析用户输入
- **参数处理器**: 自动类型转换和JSON解析
- **帮助系统**: 动态生成帮助信息

### 命令处理流程
1. 用户输入 → 命令解析 → 参数提取
2. 命令分发 → 相应处理器
3. MCP协议调用 → 结果格式化
4. 输出显示

## 扩展开发

### 添加新命令
```python
async def _handle_custom_command(self, args, kwargs):
    # 自定义命令处理逻辑
    pass

# 在 _handle_command 方法中添加
elif command == "custom":
    return await self._handle_custom_command(args, kwargs)
```

### 自定义参数解析
```python
def _parse_special_parameter(self, value):
    # 特殊参数解析逻辑
    return parsed_value
```

## 错误排除

### 常见问题
1. **连接失败**: 确保MCP服务器在指定端口运行
2. **编码错误**: Windows下可能需要设置UTF-8编码
3. **参数解析**: 复杂JSON参数需要用引号包围

### 调试技巧
```bash
# 显示详细状态
mcp> status

# 测试连接
mcp> ping

# 刷新能力
mcp> refresh
```

## 示例会话

```
$ python interactive_client.py
Connecting to MCP server at localhost:3000...
[OK] Connected to Demo Server v1.0.0

MCP Interactive Client
=====================
Type 'help' for available commands, 'quit' to exit

mcp> status
[OK] Connected to server
Server: Demo Server v1.0.0
Tools: 3
Resources: 2
Prompts: 1
[OK] Server responding to ping

mcp> tool
Available tools (3):
  add - Add two numbers
  greet - Greet someone
  countdown - Count down with streaming

mcp> add a=15 b=27
Result from add:
The sum of 15 and 27 is 42

mcp> resource read info://server
Resource: info://server
MIME Type: application/json
Content:
{
  "name": "Demo Server",
  "version": "1.0.0",
  "status": "running"
}

mcp> quit
Goodbye!
```

这个交互式客户端提供了完整的MCP协议支持，让用户能够通过简洁的命令行界面与MCP服务器进行高效交互！