#!/bin/bash
# 手机选购助手 - 备份清理脚本
# 删除超过保留天数的备份文件

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

echo "=========================================="
echo "备份清理脚本"
echo "=========================================="
echo "备份目录: $BACKUP_DIR"
echo "保留天数: $RETENTION_DAYS"
echo ""

# 统计清理前
BEFORE_COUNT=$(ls -1 "$BACKUP_DIR"/phones_*.db.gz 2>/dev/null | wc -l)
echo "清理前备份数量: $BEFORE_COUNT"

# 清理旧备份
echo "正在清理..."
find "$BACKUP_DIR" -name "phones_*.db.gz" -type f -mtime +$RETENTION_DAYS -print -delete

# 统计清理后
AFTER_COUNT=$(ls -1 "$BACKUP_DIR"/phones_*.db.gz 2>/dev/null | wc -l)
echo ""
echo "清理后备份数量: $AFTER_COUNT"
echo "已删除: $((BEFORE_COUNT - AFTER_COUNT)) 个备份"

echo ""
echo "=========================================="
echo "清理完成!"
echo "=========================================="