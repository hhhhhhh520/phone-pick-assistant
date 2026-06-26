# 数据库备份定时任务配置

## 快速配置

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨3点备份）
0 3 * * * /path/to/phone-pick-assistant/scripts/backup-db.sh >> /path/to/phone-pick-assistant/logs/backup.log 2>&1

# 每周日凌晨4点清理旧备份
0 4 * * 0 /path/to/phone-pick-assistant/scripts/cleanup-backups.sh >> /path/to/phone-pick-assistant/logs/backup.log 2>&1
```

## 定时任务说明

| 时间 | 任务 | 说明 |
|------|------|------|
| 每日 03:00 | backup-db.sh | 创建数据库备份 |
| 每周日 04:00 | cleanup-backups.sh | 清理超过7天的备份 |

## 环境变量

可以通过环境变量自定义备份行为：

```bash
# 设置保留天数（默认7天）
export BACKUP_RETENTION_DAYS=14
```

## Docker 环境配置

如果使用 Docker 部署，可以在 `docker-compose.prod.yml` 中添加备份服务：

```yaml
services:
  backup:
    image: alpine:latest
    container_name: phone-assistant-backup
    volumes:
      - backend-data:/app/backend/data
      - ./backups:/backups
      - ./scripts:/scripts
    environment:
      - BACKUP_RETENTION_DAYS=7
    command: sh -c "crond -f -l 2"
    entrypoint: |
      sh -c "
        echo '0 3 * * * /scripts/backup-db.sh' > /etc/crontabs/root
        echo '0 4 * * 0 /scripts/cleanup-backups.sh' >> /etc/crontabs/root
        crond -f -l 2
      "
```

## 手动操作

```bash
# 手动备份
./scripts/backup-db.sh

# 查看备份列表
ls -lt backups/

# 恢复数据库
./scripts/restore-db.sh backups/phones_20260503_030000.db.gz

# 手动清理
./scripts/cleanup-backups.sh
```

## 监控建议

1. **日志监控**: 定期检查 `logs/backup.log` 确保备份成功
2. **磁盘空间**: 监控 `backups/` 目录大小
3. **恢复测试**: 定期测试恢复流程确保备份有效