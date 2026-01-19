# Google Compute Engine 部署文档

## 🚀 快速部署

### 前置要求

1. **Google Cloud 账号** 并创建项目
2. **Compute Engine VM 实例**（推荐配置）:
   - 操作系统: Ubuntu 22.04 LTS
   - 机器类型: e2-small (2 vCPU, 2 GB 内存) 或更高
   - 启动磁盘: 20 GB 标准永久磁盘
   - 防火墙: 允许 HTTP (80) 和 HTTPS (443) 流量

3. **域名**（可选，用于 HTTPS）

---

## 📦 一键部署

SSH 连接到你的 Compute Engine 实例后，运行：

```bash
# 克隆项目
git clone https://github.com/yukunf/xmmcg-net.git
cd xmmcg-net

# 执行部署脚本
sudo bash deploy.sh
```

脚本会自动完成：
- ✅ 安装系统依赖（Python, Nginx, Certbot）
- ✅ 创建虚拟环境并安装 Python 包
- ✅ 生成环境变量文件
- ✅ 数据库迁移和静态文件收集
- ✅ 配置 Gunicorn 和 Nginx
- ✅ 启动服务

---

## ⚙️ 配置说明

### 1. 环境变量

编辑 `/opt/xmmcg/.env`:

```bash
sudo nano /opt/xmmcg/.env
```

重要配置项：
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=*

# 修改为你的域名
PRODUCTION_DOMAIN=your-domain.com

# Majdata.net 配置
MAJDATA_USERNAME=xmmcg5
MAJDATA_PASSWD_HASHED=your-password-hash
```

修改后重启服务：
```bash
sudo systemctl restart gunicorn
```

### 2. 防火墙配置

确保 GCP 防火墙规则允许：
```bash
# 在 GCP Console 中添加防火墙规则
# 或使用 gcloud 命令
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0
```

### 3. SSL 证书配置

使用 Let's Encrypt 免费证书：

```bash
# 替换为你的域名
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期（已自动配置）
sudo certbot renew --dry-run
```

---

## 👤 创建管理员账号

```bash
cd /opt/xmmcg/backend/xmmcg
source /opt/xmmcg/venv/bin/activate
python manage.py createsuperuser
```

---

## 🔍 服务管理

### Gunicorn（Django 应用）

```bash
# 查看状态
sudo systemctl status gunicorn

# 启动/停止/重启
sudo systemctl start gunicorn
sudo systemctl stop gunicorn
sudo systemctl restart gunicorn

# 查看日志
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/gunicorn/error.log
```

### Nginx（Web 服务器）

```bash
# 查看状态
sudo systemctl status nginx

# 重启
sudo systemctl restart nginx

# 测试配置
sudo nginx -t

# 查看日志
sudo tail -f /var/log/nginx/xmmcg_error.log
sudo tail -f /var/log/nginx/xmmcg_access.log
```

---

## 🔄 更新代码

```bash
# 拉取最新代码
cd /opt/xmmcg
sudo git pull

# 重启服务
sudo systemctl restart gunicorn
```

如果有数据库变更：
```bash
cd /opt/xmmcg/backend/xmmcg
source /opt/xmmcg/venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## 📊 监控和维护

### 磁盘使用

```bash
# 检查磁盘空间
df -h

# 清理日志（保留最近 7 天）
sudo journalctl --vacuum-time=7d
```

### 数据库备份

```bash
# 备份 SQLite 数据库
sudo cp /opt/xmmcg/backend/xmmcg/db.sqlite3 \
       /opt/xmmcg/backup_$(date +%Y%m%d_%H%M%S).sqlite3

# 定期备份（添加到 crontab）
sudo crontab -e
# 添加: 0 2 * * * cp /opt/xmmcg/backend/xmmcg/db.sqlite3 /opt/xmmcg/backup_$(date +\%Y\%m\%d).sqlite3
```

### 媒体文件备份

```bash
# 备份上传的文件
sudo tar -czf /opt/xmmcg/media_backup_$(date +%Y%m%d).tar.gz \
              /var/www/xmmcg/media/
```

---

## 🐛 故障排查

### 问题 1: 502 Bad Gateway

```bash
# 检查 Gunicorn 是否运行
sudo systemctl status gunicorn

# 检查 socket 文件权限
ls -l /var/run/gunicorn/xmmcg.sock

# 查看错误日志
sudo journalctl -u gunicorn -n 50
```

### 问题 2: 静态文件 404

```bash
# 重新收集静态文件
cd /opt/xmmcg/backend/xmmcg
source /opt/xmmcg/venv/bin/activate
python manage.py collectstatic --noinput

# 检查权限
sudo chown -R www-data:www-data /var/www/xmmcg/static/
```

### 问题 3: 文件上传失败

```bash
# 检查 media 目录权限
sudo chown -R www-data:www-data /var/www/xmmcg/media/
sudo chmod -R 755 /var/www/xmmcg/media/

# 检查 Nginx 上传大小限制
sudo nano /etc/nginx/sites-available/xmmcg
# 确保有: client_max_body_size 25M;
```

---

## 💰 成本优化

### 自动关机（开发/测试环境）

```bash
# 晚上自动关机（节省成本）
sudo crontab -e
# 添加: 0 22 * * * /sbin/shutdown -h now
```

### 使用抢占式实例

创建 VM 时选择"抢占式"选项，可节省 60-90% 成本（适合开发环境）

---

## 📞 技术支持

遇到问题请查看：
- 项目文档: `/doc/apidoc/`
- 实现报告: `/doc/Implementation Report/`
- GitHub Issues: https://github.com/yukunf/xmmcg-net/issues

---

## 🔐 安全建议

1. **定期更新系统**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **配置防火墙** (ufw)
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

3. **禁用 root SSH 登录**
   ```bash
   sudo nano /etc/ssh/sshd_config
   # 设置: PermitRootLogin no
   sudo systemctl restart sshd
   ```

4. **启用自动安全更新**
   ```bash
   sudo apt-get install unattended-upgrades
   sudo dpkg-reconfigure --priority=low unattended-upgrades
   ```
