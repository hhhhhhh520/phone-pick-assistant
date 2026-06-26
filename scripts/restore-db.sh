#!/bin/bash
# 手机选购助手 - 数据库恢复脚本
# 从备份文件恢复数据库

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DB_PATH="$PROJECT_DIR/backend/data/phones.db"
BACKUP_DIR="$PROJECT_DIR/backups"

# 检查参数
if [ -z "$1" ]; then
    echo "用法: $0 <备份文件路径>"
    echo ""
    echo "可用备份:"
    ls -lt "$BACKUP_DIR"/phones_*.db.gz 2>/dev/null | head -10
    exit 1
fi

BACKUP_FILE="$1"

echo "=========================================="
echo "数据库恢复脚本"
echo "=========================================="
echo "备份文件: $BACKUP_FILE"
echo "目标位置: $DB_PATH"
echo ""

# 检查备份文件
if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 确认恢复
read -p "确认恢复数据库? 这将覆盖当前数据库! (输入 'yes' 确认): " confirm
if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 0
fi

# 备份当前数据库
if [ -f "$DB_PATH" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    PRE_BACKUP="$BACKUP_DIR/pre_restore_$TIMESTAMP.db"
    echo "正在备份当前数据库到: $PRE_BACKUP"
    cp "$DB_PATH" "$PRE_BACKUP"
fi

# 解压并恢复
echo "正在恢复数据库..."
gunzip -c "$BACKUP_FILE" > "$DB_PATH"

# 验证恢复
if [ -f "$DB_PATH" ]; then
    SIZE=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH")
    echo "恢复后大小: $((SIZE / 1024)) KB"
    echo ""
    echo "✅ 恢复成功!"
else
    echo "❌ 恢复失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "恢复完成!"
echo "=========================================="