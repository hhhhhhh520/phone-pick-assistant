#!/bin/bash
# 手机选购助手 - 数据库备份脚本
# 创建带时间戳的数据库备份并压缩

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DB_PATH="$PROJECT_DIR/backend/data/phones.db"
BACKUP_DIR="$PROJECT_DIR/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/phones_$TIMESTAMP.db.gz"

echo "=========================================="
echo "数据库备份脚本"
echo "=========================================="
echo "数据库: $DB_PATH"
echo "备份到: $BACKUP_FILE"
echo "保留天数: $RETENTION_DAYS"
echo ""

# 检查数据库文件
if [ ! -f "$DB_PATH" ]; then
    echo "错误: 数据库文件不存在: $DB_PATH"
    exit 1
fi

# 获取备份前大小
BEFORE_SIZE=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH")
echo "数据库大小: $((BEFORE_SIZE / 1024)) KB"

# 创建备份
echo "正在创建备份..."
cp "$DB_PATH" "$BACKUP_DIR/phones_$TIMESTAMP.db"
gzip "$BACKUP_DIR/phones_$TIMESTAMP.db"

# 验证备份
if [ -f "$BACKUP_FILE" ]; then
    AFTER_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE")
    echo "备份大小: $((AFTER_SIZE / 1024)) KB"
    echo "压缩率: $((100 - (AFTER_SIZE * 100 / BEFORE_SIZE)))%"
    echo ""
    echo "✅ 备份成功: $BACKUP_FILE"
else
    echo "❌ 备份失败"
    exit 1
fi

# 清理旧备份
echo ""
echo "正在清理超过 $RETENTION_DAYS 天的旧备份..."
find "$BACKUP_DIR" -name "phones_*.db.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING=$(ls -1 "$BACKUP_DIR"/phones_*.db.gz 2>/dev/null | wc -l)
echo "当前备份数量: $REMAINING"

echo ""
echo "=========================================="
echo "备份完成!"
echo "=========================================="