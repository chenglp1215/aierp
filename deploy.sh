#!/bin/bash
# CI/CD Deploy Script
# 自动打包并部署到远程服务器

set -e

# 配置
REMOTE_HOST="132.232.212.151"
REMOTE_USER="root"
REMOTE_PATH="/root/aierp"
SSH_KEY=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 初始化
init() {
    log_info "开始部署..."

    # 检查必要命令
    check_command ssh
    check_command scp
    check_command npm

    # 获取项目根目录
    PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
    cd "$PROJECT_ROOT"

    log_info "项目目录: $PROJECT_ROOT"
}

# 构建前端
build_frontend() {
    log_info "构建前端..."

    cd "$PROJECT_ROOT/web"

    # 检查并安装依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi

    # 构建
    npm run build

    if [ ! -d "dist" ]; then
        log_error "前端构建失败，dist 目录不存在"
        exit 1
    fi

    log_info "前端构建完成"
}

# 传输文件
transfer_files() {
    log_info "传输文件到远程服务器..."

    # 创建远程目录（如果不存在）
    ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_PATH/backend $REMOTE_PATH/dist"

    # 准备后端打包目录
    log_info "准备后端文件..."
    TEMP_BACKEND=$(mktemp -d)
    cp -r "$PROJECT_ROOT/backend/" "$TEMP_BACKEND/backend_temp/"
    
    # 将 settings-pro.py 复制为 settings.py
    if [ -f "$TEMP_BACKEND/backend_temp/config/settings-pro.py" ]; then
        cp "$TEMP_BACKEND/backend_temp/config/settings-pro.py" "$TEMP_BACKEND/backend_temp/config/settings.py"
        log_info "已复制 settings-pro.py 为 settings.py"
    fi

    # 传输后端（排除 __pycache__ 和 .pyc 文件）
    log_info "传输后端文件..."
    rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' --exclude='venv' --exclude='.venv' \
        "$TEMP_BACKEND/backend_temp/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/backend/"

    # 清理临时目录
    rm -rf "$TEMP_BACKEND"

    # 传输前端
    log_info "传输前端文件..."
    scp -r "$PROJECT_ROOT/web/dist/"* "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/dist/"

    log_info "文件传输完成"
}

# 重启服务
restart_service() {
    log_info "重启远程服务..."

    ssh "$REMOTE_USER@$REMOTE_HOST" "bash $REMOTE_PATH/restart.sh"

    log_info "服务重启完成"
}

# 主流程
main() {
    init
    build_frontend
    transfer_files
    restart_service

    log_info "部署完成!"
}

main "$@"
