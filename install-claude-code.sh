#!/usr/bin/env bash
set -euo pipefail

# ========================
#       常量定义
# ========================
SCRIPT_NAME=$(basename "$0")
NODE_MIN_VERSION=18
NODE_INSTALL_VERSION=22
CLAUDE_PACKAGE="@anthropic-ai/claude-code"
CONFIG_DIR="$HOME/.claude"
CONFIG_FILE="$CONFIG_DIR/settings.json"
API_BASE_URL="https://open.bigmodel.cn/api/anthropic"
API_KEY_URL="https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys"
API_TIMEOUT_MS=3000000

# ========================
#       工具函数
# ========================
log_info()    { echo "🔹 $*"; }
log_success() { echo "✅ $*"; }
log_error()   { echo "❌ $*" >&2; }

ensure_dir_exists() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
    fi
}

# ========================
#     Node.js 检查
# ========================
check_nodejs() {
    if command -v node >/dev/null 2>&1; then
        current_version=$(node -v | sed 's/v//')
        major_version=$(echo "$current_version" | cut -d. -f1)
        if [ "$major_version" -ge "$NODE_MIN_VERSION" ]; then
            log_success "Node.js 已安装: v$current_version"
            return 0
        else
            log_info "Node.js 版本过低 (v$current_version)，请升级到 v$NODE_INSTALL_VERSION+"
            log_info "👉 下载地址: https://nodejs.org/en/download/prebuilt-installer"
            exit 1
        fi
    else
        log_error "未检测到 Node.js，请先安装 Node.js $NODE_INSTALL_VERSION+"
        log_info "👉 下载地址: https://nodejs.org/en/download/prebuilt-installer"
        exit 1
    fi
}

# ========================
#     Claude Code 安装
# ========================
install_claude_code() {
    if command -v claude >/dev/null 2>&1; then
        log_success "Claude Code 已安装: $(claude --version)"
    else
        log_info "正在安装 Claude Code..."
        npm install -g "$CLAUDE_PACKAGE" || {
            log_error "Claude Code 安装失败"
            exit 1
        }
        log_success "Claude Code 安装成功"
    fi
}

# ========================
#     配置 claude.json
# ========================
configure_claude_json() {
    node --eval '
        const os = require("os");
        const fs = require("fs");
        const path = require("path");

        const filePath = path.join(os.homedir(), ".claude.json");
        let content = {};
        if (fs.existsSync(filePath)) {
            content = JSON.parse(fs.readFileSync(filePath, "utf-8"));
        }
        content.hasCompletedOnboarding = true;
        fs.writeFileSync(filePath, JSON.stringify(content, null, 2), "utf-8");
    '
}

# ========================
#     API Key 配置
# ========================
configure_claude() {
    log_info "配置 Claude Code..."
    echo "👉 获取 API Key: $API_KEY_URL"
    read -r -p "🔑 请输入你的 ZHIPU API Key: " api_key

    if [ -z "$api_key" ]; then
        log_error "API Key 不能为空"
        exit 1
    fi

    ensure_dir_exists "$CONFIG_DIR"

    node --eval "
        const os = require('os');
        const fs = require('fs');
        const path = require('path');

        const filePath = path.join(os.homedir(), '.claude', 'settings.json');
        const apiKey = '$api_key';

        let content = {};
        if (fs.existsSync(filePath)) {
            content = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
        }

        content.env = {
            ANTHROPIC_AUTH_TOKEN: apiKey,
            ANTHROPIC_BASE_URL: '$API_BASE_URL',
            API_TIMEOUT_MS: '$API_TIMEOUT_MS'
        };

        fs.writeFileSync(filePath, JSON.stringify(content, null, 2), 'utf-8');
    " || {
        log_error "写入 settings.json 失败"
        exit 1
    }

    log_success "Claude Code 配置完成"
}

# ========================
#        主流程
# ========================
main() {
    echo "🚀 开始执行 $SCRIPT_NAME"

    check_nodejs
    install_claude_code
    configure_claude_json
    configure_claude

    echo ""
    log_success "🎉 安装和配置完成!"
    echo ""
    echo "🚀 现在可以运行: claude"
}

main "$@"
