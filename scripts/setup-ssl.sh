#!/bin/bash
# 手机选购助手 - SSL 证书配置脚本
# 使用 Let's Encrypt 获取免费 SSL 证书

set -e

# 配置
DOMAIN=${1:-"your-domain.com"}
EMAIL=${2:-"admin@your-domain.com"}
NGINX_SSL_DIR="./nginx/ssl"

echo "=========================================="
echo "SSL 证书配置脚本"
echo "=========================================="
echo "域名: $DOMAIN"
echo "邮箱: $EMAIL"
echo ""

# 检查 certbot 是否安装
if ! command -v certbot &> /dev/null; then
    echo "正在安装 certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot
fi

# 创建 SSL 目录
mkdir -p "$NGINX_SSL_DIR"

# 获取证书（standalone 模式）
echo "正在获取 SSL 证书..."
sudo certbot certonly --standalone \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email

# 复制证书到 Nginx 目录
echo "正在复制证书..."
sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$NGINX_SSL_DIR/"
sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$NGINX_SSL_DIR/"

# 设置权限
sudo chmod 644 "$NGINX_SSL_DIR/fullchain.pem"
sudo chmod 600 "$NGINX_SSL_DIR/privkey.pem"

# 设置自动续期
echo "正在配置自动续期..."
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx") | crontab -

echo ""
echo "=========================================="
echo "SSL 证书配置完成!"
echo "=========================================="
echo "证书位置: $NGINX_SSL_DIR"
echo "自动续期: 每日凌晨3点"
echo ""
echo "请确保更新 .env.production 中的 CORS_ORIGINS"