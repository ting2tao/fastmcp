# Kimi AI MCP 集成使用文档

本文档总结了所有已创建的脚本和它们的用法，帮助您快速使用 Kimi AI 集成。

## 📋 脚本总览

### 1. **kimi_with_dotenv.py** ⭐⭐⭐⭐⭐ **最新推荐**
**功能**: 支持 .env 文件配置的 Kimi AI 集成服务器
**端口**: 8092
**状态**: ✅ 可正常使用

**使用方法**:
```bash
cd native_mcp
python kimi_with_dotenv.py
```

**访问地址**: http://localhost:8092

**配置方法**:
1. **方式一 (推荐)**: 创建 `.env` 文件
   ```
   KIMI_API_KEY=your_kimi_api_key
   KIMI_BASE_URL=https://api.moonshot.cn/v1
   ```

2. **方式二**: 设置环境变量
   ```bash
   export KIMI_API_KEY=your_kimi_api_key
   ```

**特点**:
- ✅ 支持 .env 文件配置
- ✅ 环境变量优先级更高
- ✅ 智能配置检测和显示
- ✅ 内置 .env 示例下载
- ✅ 真实 API + 演示模式
- ✅ 美观的配置状态显示

---

### 2. **simple_kimi_real.py** ⭐⭐⭐⭐
**功能**: 简单版真实 Kimi AI 集成服务器
**端口**: 8090
**状态**: ✅ 可正常使用

**使用方法**:
```bash
cd native_mcp
python simple_kimi_real.py
```

**访问地址**: http://localhost:8090

**特点**:
- 真正连接 Kimi AI API
- 支持环境变量 `KIMI_API_KEY`
- 无 API Key 时自动降级到演示模式
- 简洁清晰的 Web 界面
- 支持两个模型: kimi-k2-turbo-preview, ultrathink

---

### 3. **kimi_working_demo.py** ⭐⭐⭐
**功能**: 演示模式的 Kimi AI 集成（不调用真实 API）
**端口**: 8088
**状态**: ✅ 可正常使用

**使用方法**:
```bash
cd native_mcp
python kimi_working_demo.py
```

**访问地址**: http://localhost:8088

**特点**:
- 完全模拟的 Kimi AI 响应
- 不需要 API Key
- 展示集成效果和界面设计
- 用于演示和测试界面功能

---

### 4. **simple_working_chat.py** ⭐⭐
**功能**: 简单的 MCP 聊天服务器（通过 MCP 协议连接）
**端口**: 8085
**状态**: ⚠️ 需要 MCP 服务器运行在 3001 端口

**使用方法**:
```bash
cd native_mcp
python simple_working_chat.py
```

**访问地址**: http://localhost:8085

**特点**:
- 通过 MCP 协议连接到后端服务器
- 每次请求创建新连接避免连接问题
- 需要配合 MCP 服务器使用

---

### 5. **kimi_web_chat.py** ⭐⭐
**功能**: Kimi AI 专用的 Web 聊天界面
**端口**: 8087
**状态**: ⚠️ 需要 MCP 服务器运行在 3002 端口

**使用方法**:
```bash
cd native_mcp
python kimi_web_chat.py
```

**访问地址**: http://localhost:8087

**特点**:
- 专为 Kimi AI 设计的界面
- 模型选择功能
- 需要配合 kimi_demo_server.py 使用

---

### 6. **kimi_demo_server.py** ⭐
**功能**: Kimi MCP 服务器（后端）
**端口**: 3002
**状态**: ⚠️ 启动有问题，不推荐使用

**使用方法**:
```bash
cd native_mcp
python kimi_demo_server.py
```

**特点**:
- MCP 协议服务器
- 提供工具和资源接口
- 启动过程存在问题

---

### 7. **real_kimi_integration.py** ❌
**功能**: 复杂版本的真实 Kimi AI 集成
**端口**: 8091
**状态**: ❌ 有错误，不推荐使用

**问题**: AttributeError 错误

---

## 🚀 **推荐使用方案**

### 方案一: .env 文件配置 ⭐⭐⭐⭐⭐ **最佳选择**
```bash
cd native_mcp

# 1. 启动服务器
python kimi_with_dotenv.py

# 2. 创建 .env 文件 (可选，有 API Key 时)
cat > .env << EOF
KIMI_API_KEY=your_kimi_api_key
KIMI_BASE_URL=https://api.moonshot.cn/v1
EOF

# 3. 重启服务器使配置生效 (如果添加了 .env)
# Ctrl+C 停止，然后重新运行 python kimi_with_dotenv.py
```
- 访问: http://localhost:8092
- 支持 .env 文件和环境变量
- 界面显示配置状态
- 无配置时自动使用演示模式

### 方案二: 环境变量配置 ⭐⭐⭐⭐
```bash
cd native_mcp

# 设置环境变量 (可选)
export KIMI_API_KEY=your_kimi_api_key
export KIMI_BASE_URL=https://api.moonshot.cn/v1

# 启动服务器
python simple_kimi_real.py
```
- 访问: http://localhost:8090
- 简洁版本，专注核心功能

### 方案三: 纯演示模式 ⭐⭐⭐
```bash
cd native_mcp
python kimi_working_demo.py
```
- 访问: http://localhost:8088
- 不需要任何配置
- 完全模拟响应

## ⚙️ **配置文件说明**

### .env 文件配置 (推荐)

创建 `.env` 文件:
```bash
# 必需配置
KIMI_API_KEY=your_actual_api_key_here

# 可选配置
KIMI_BASE_URL=https://api.moonshot.cn/v1
```

### 环境变量配置

```bash
# Windows
set KIMI_API_KEY=your_kimi_api_key
set KIMI_BASE_URL=https://api.moonshot.cn/v1

# Linux/Mac
export KIMI_API_KEY=your_kimi_api_key
export KIMI_BASE_URL=https://api.moonshot.cn/v1
```

### 配置优先级
1. 环境变量 (最高优先级)
2. .env 文件
3. 默认值/演示模式

## 📝 **脚本状态总结**

| 脚本名称 | 端口 | 状态 | 推荐度 | 功能 | 配置支持 |
|---------|------|------|--------|------|----------|
| `kimi_with_dotenv.py` | 8092 | ✅ 正常 | ⭐⭐⭐⭐⭐ | .env + 真实 API | .env + 环境变量 |
| `simple_kimi_real.py` | 8090 | ✅ 正常 | ⭐⭐⭐⭐ | 真实 API 集成 | 仅环境变量 |
| `kimi_working_demo.py` | 8088 | ✅ 正常 | ⭐⭐⭐ | 演示模式 | 无需配置 |
| `simple_working_chat.py` | 8085 | ⚠️ 依赖 | ⭐⭐ | MCP 聊天 | 依赖后端 |
| `kimi_web_chat.py` | 8087 | ⚠️ 依赖 | ⭐⭐ | Kimi 界面 | 依赖后端 |
| `kimi_demo_server.py` | 3002 | ⚠️ 问题 | ⭐ | MCP 服务器 | 有问题 |
| `real_kimi_integration.py` | 8091 | ❌ 错误 | ❌ | 复杂集成 | 代码错误 |

## 🔧 **故障排除**

### 端口被占用
```bash
# 检查端口占用
netstat -an | findstr :8092

# 如果被占用，可以修改脚本中的 PORT 变量
```

### .env 文件问题
1. 确保 .env 文件在运行目录中
2. 检查文件格式: `KEY=value` (没有空格)
3. 不要用引号包围值 (除非值本身包含空格)
4. 重启服务器使配置生效

### API Key 问题
1. 确保设置了正确的 API Key
2. 检查 API Key 格式
3. 验证网络连接到 Kimi AI 服务

### 启动失败
1. 检查 Python 环境
2. 确认脚本路径正确
3. 查看错误信息

## 🎯 **快速开始**

**最推荐的使用方式**:
1. 下载 `kimi_with_dotenv.py`
2. 运行: `python kimi_with_dotenv.py`
3. 打开: http://localhost:8092
4. 开始聊天（演示模式）
5. 可选：创建 `.env` 文件配置真实 API Key

这是目前功能最完整、最用户友好的版本！支持 .env 文件配置，界面美观，功能完善。