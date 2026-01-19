# 域名配置指南

## 📋 域名配置完整流程

### 步骤 1: 购买域名

在任意域名注册商购买域名，推荐：
- **Namecheap** (https://www.namecheap.com)
- **GoDaddy** (https://www.godaddy.com)
- **Google Domains** (https://domains.google)
- **Cloudflare** (https://www.cloudflare.com/zh-cn/products/registrar/)
- **阿里云** (https://wanwang.aliyun.com) - 中国用户

---

### 步骤 2: 配置 DNS 解析

#### 2.1 获取服务器 IP 地址

```bash
# 在 GCP Compute Engine 控制台查看外部 IP
# 或在服务器上运行：
curl ifconfig.me
```

#### 2.2 添加 DNS 记录

在域名注册商的 DNS 管理界面添加以下记录：

| 类型 | 名称 | 值 | TTL |
|------|------|-----|-----|
| A | @ | 你的服务器IP | 3600 |
| A | www | 你的服务器IP | 3600 |

**示例**：
```
类型: A
主机: @
值: 34.123.45.67  (你的服务器IP)
TTL: 3600

类型: A
主机: www
值: 34.123.45.67  (你的服务器IP)
TTL: 3600
```

**验证 DNS 解析**（需等待 5-30 分钟生效）：
```bash
# 检查域名解析
nslookup your-domain.com
dig your-domain.com

# 检查是否指向正确的IP
ping your-domain.com
```

---

### 步骤 3: 修改 Nginx 配置

#### 3.1 编辑 Nginx 配置文件

```bash
sudo nano /etc/nginx/sites-available/xmmcg
```

#### 3.2 修改域名

将以下两处的 `your-domain.com` 替换为你的实际域名：

```nginx
server {
    listen 80;
    server_name example.com www.example.com;  # ← 修改这里
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;  # ← 修改这里
    
    # ... 其他配置
}
```

#### 3.3 测试并重启 Nginx

```bash
# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

### 步骤 4: 配置 Django 设置

#### 4.1 编辑环境变量

```bash
sudo nano /opt/xmmcg/.env
```

#### 4.2 设置域名

```env
# 生产域名（不带 http:// 或 https://）
PRODUCTION_DOMAIN=example.com

# 允许的主机（可以用 * 或具体域名）
ALLOWED_HOSTS=example.com,www.example.com

# Django 安全设置（生产环境必须）
DEBUG=False
SECRET_KEY=your-secret-key-here
```

#### 4.3 重启 Gunicorn

```bash
sudo systemctl restart gunicorn
```

---

### 步骤 5: 配置 SSL 证书（HTTPS）

#### 5.1 使用 Certbot 自动配置

```bash
# 为你的域名申请免费 SSL 证书
sudo certbot --nginx -d example.com -d www.example.com
```

**交互式问题回答**：
1. 输入邮箱地址（用于证书过期提醒）
2. 同意服务条款：`Y`
3. 是否订阅邮件：`N`（可选）
4. 重定向 HTTP 到 HTTPS：选择 `2`（推荐）

#### 5.2 验证 SSL 证书

```bash
# 查看已安装的证书
sudo certbot certificates

# 测试自动续期
sudo certbot renew --dry-run
```

#### 5.3 证书自动续期

Certbot 会自动配置 cron 任务，每天检查并更新证书。检查：

```bash
# 查看续期定时任务
sudo systemctl list-timers | grep certbot
```

---

### 步骤 6: 配置防火墙（GCP）

#### 6.1 在 GCP 控制台配置防火墙规则

1. 进入 **VPC 网络 > 防火墙**
2. 创建防火墙规则：

**允许 HTTP (80)**
```
名称: allow-http
目标: 网络中的所有实例
来源 IP 范围: 0.0.0.0/0
协议和端口: tcp:80
```

**允许 HTTPS (443)**
```
名称: allow-https
目标: 网络中的所有实例
来源 IP 范围: 0.0.0.0/0
协议和端口: tcp:443
```

#### 6.2 或使用 gcloud 命令

```bash
# 允许 HTTP
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0

# 允许 HTTPS
gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0
```

---

### 步骤 7: 验证配置

#### 7.1 测试 HTTP 访问

```bash
curl http://your-domain.com
```

#### 7.2 测试 HTTPS 访问

```bash
curl https://your-domain.com
```

#### 7.3 浏览器访问

打开浏览器访问：
- `https://your-domain.com`
- `https://your-domain.com/admin`

检查：
- ✅ 显示绿色锁标志（SSL 有效）
- ✅ 网站正常加载
- ✅ 静态文件和媒体文件正常显示

---

## 🔧 常见问题排查

### 问题 1: DNS 解析不生效

**现象**: `ping your-domain.com` 找不到主机

**解决**:
```bash
# 检查 DNS 传播状态
# 使用在线工具: https://dnschecker.org/

# 清除本地 DNS 缓存（Windows）
ipconfig /flushdns

# 等待 DNS 传播（通常 5-30 分钟，最长 48 小时）
```

### 问题 2: 502 Bad Gateway

**现象**: 访问域名显示 502 错误

**解决**:
```bash
# 检查 Gunicorn 状态
sudo systemctl status gunicorn

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/xmmcg_error.log

# 重启服务
sudo systemctl restart gunicorn nginx
```

### 问题 3: SSL 证书申请失败

**现象**: Certbot 报错 "Failed authorization"

**解决**:
```bash
# 确保域名已正确解析
nslookup your-domain.com

# 确保端口 80 开放
sudo netstat -tlnp | grep :80

# 检查 Nginx 配置
sudo nginx -t

# 临时关闭防火墙（申请证书后重新开启）
sudo ufw disable
sudo certbot --nginx -d your-domain.com
sudo ufw enable
```

### 问题 4: CSRF 验证失败

**现象**: 前端请求报 403 CSRF token missing

**解决**:
```bash
# 编辑 .env 文件
sudo nano /opt/xmmcg/.env

# 确保设置了正确的域名
PRODUCTION_DOMAIN=your-domain.com

# 重启 Gunicorn
sudo systemctl restart gunicorn
```

### 问题 5: 静态文件 404

**现象**: CSS/JS 文件无法加载

**解决**:
```bash
# 重新收集静态文件
cd /opt/xmmcg/backend/xmmcg
source /opt/xmmcg/venv/bin/activate
python manage.py collectstatic --noinput

# 检查权限
sudo chown -R www-data:www-data /var/www/xmmcg/static/

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 🌐 多域名配置

如果需要配置多个域名（例如 API 和前端分离）：

### Nginx 多域名配置

```nginx
# API 域名
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    
    location / {
        proxy_pass http://django_app;
        # ... 其他配置
    }
}

# 前端域名
server {
    listen 443 ssl http2;
    server_name www.example.com;
    
    ssl_certificate /etc/letsencrypt/live/www.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.example.com/privkey.pem;
    
    location / {
        root /var/www/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

### 为多个域名申请证书

```bash
sudo certbot --nginx \
    -d example.com \
    -d www.example.com \
    -d api.example.com
```

---

## 🔐 安全最佳实践

### 1. 强制 HTTPS

Nginx 配置已包含自动重定向：
```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$server_name$request_uri;
}
```

### 2. 启用 HSTS

编辑 Nginx 配置，在 HTTPS server 块中添加：
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 3. 配置 Security Headers

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

---

## 📊 域名配置检查清单

- [ ] DNS A 记录已添加并生效
- [ ] Nginx 配置中域名已修改
- [ ] Django `.env` 文件中 `PRODUCTION_DOMAIN` 已设置
- [ ] GCP 防火墙允许 80 和 443 端口
- [ ] SSL 证书已成功申请
- [ ] HTTP 自动重定向到 HTTPS
- [ ] 浏览器显示绿色锁标志
- [ ] CORS 配置包含生产域名
- [ ] CSRF 信任域名包含生产域名
- [ ] 管理后台可以正常访问
- [ ] 静态文件和媒体文件正常加载

---

## 🎯 快速配置命令总结

```bash
# 1. 修改 Nginx 域名
sudo nano /etc/nginx/sites-available/xmmcg
# 将 your-domain.com 替换为实际域名

# 2. 测试并重启 Nginx
sudo nginx -t
sudo systemctl restart nginx

# 3. 配置 Django 环境变量
sudo nano /opt/xmmcg/.env
# 设置 PRODUCTION_DOMAIN=your-domain.com

# 4. 重启 Gunicorn
sudo systemctl restart gunicorn

# 5. 申请 SSL 证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 6. 验证配置
curl https://your-domain.com
```

完成以上步骤后，你的网站就可以通过域名 HTTPS 访问了！
