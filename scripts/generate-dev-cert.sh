#!/bin/bash
# 手机选购助手 - 开发环境自签名证书生成脚本
# 用于本地 HTTPS 测试

set -e

SSL_DIR="./nginx/ssl"

echo "=========================================="
echo "生成开发环境自签名证书"
echo "=========================================="

# 创建 SSL 目录
mkdir -p "$SSL_DIR"

# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/localhost.key" \
    -out "$SSL_DIR/localhost.crt" \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=PhoneAssistant/OU=Dev/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# 设置权限
chmod 644 "$SSL_DIR/localhost.crt"
chmod 600 "$SSL_DIR/localhost.key"

echo ""
echo "=========================================="
echo "自签名证书生成完成!"
echo "=========================================="
echo "证书位置: $SSL_DIR"
echo ""
echo "注意: 自签名证书仅用于开发测试"
echo "浏览器会显示不安全警告，这是正常的"
echo ""
echo "Chrome 信任证书方法:"
echo "1. 访问 chrome://settings/certificates"
echo "2. 选择 'Authorities' 标签"
echo "3. 导入 $SSL_DIR/localhost.crt"
echo "4. 勾选 'Trust this certificate for identifying websites'"