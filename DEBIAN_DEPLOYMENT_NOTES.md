# Debian 系统部署说明

## 🐧 Debian 特定配置

本项目已针对 Debian 11 (Bullseye) 和 Debian 12 (Bookworm) 进行优化。

### 与 Ubuntu 的主要区别

1. **Python 包管理**
   - Debian 可能需要 `python3-dev` 和 `build-essential`
   - 已在部署脚本中自动处理

2. **Certbot 安装**
   - Debian 11: 使用 `apt` 安装
   - Debian 12: 推荐使用 `snap` 安装
   - 部署脚本会自动检测并选择合适的方式

3. **系统服务**
   - Systemd 配置与 Ubuntu 完全相同
   - 无需额外修改

---

## 🚀 快速部署（Debian）

### 方法 1: 使用自动脚本（推荐）

```bash
# SSH 登录到你的 Debian 服务器
ssh user@your-debian-server

# 克隆项目
git clone https://github.com/yukunf/xmmcg-net.git
cd xmmcg-net

# 执行部署（自动适配 Debian）
sudo bash deploy.sh
```

### 方法 2: 手动部署

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装依赖
sudo apt install -y python3 python3-pip python3-venv python3-dev \
                     build-essential nginx git sqlite3 curl

# 3. 安装 Certbot (Debian 12 推荐使用 snap)
sudo apt install -y snapd
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# 4. 创建项目目录
sudo mkdir -p /opt/xmmcg
sudo mkdir -p /var/www/xmmcg/{static,media}
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/run/gunicorn

# 5. 克隆代码
sudo git clone https://github.com/yukunf/xmmcg-net.git /opt/xmmcg

# 6. 创建虚拟环境
sudo python3 -m venv /opt/xmmcg/venv
source /opt/xmmcg/venv/bin/activate

# 7. 安装 Python 依赖
pip install --upgrade pip
pip install -r /opt/xmmcg/backend/xmmcg/requirements.txt

# 8. 配置环境变量
sudo nano /opt/xmmcg/.env
# 参考 COMPUTE_ENGINE_DEPLOYMENT.md 中的配置

# 9. 数据库迁移
cd /opt/xmmcg/backend/xmmcg
python manage.py migrate
python manage.py collectstatic --noinput

# 10. 设置权限
sudo chown -R www-data:www-data /opt/xmmcg
sudo chown -R www-data:www-data /var/www/xmmcg
sudo chown -R www-data:www-data /var/log/gunicorn
sudo chown -R www-data:www-data /var/run/gunicorn

# 11. 配置 Gunicorn 服务
sudo cp /opt/xmmcg/backend/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn

# 12. 配置 Nginx
sudo cp /opt/xmmcg/backend/nginx.conf /etc/nginx/sites-available/xmmcg
sudo ln -s /etc/nginx/sites-available/xmmcg /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 13. 配置防火墙 (可选)
sudo apt install -y ufw
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw --force enable

# 14. 配置 SSL
sudo certbot --nginx -d your-domain.com
```

---

## 🔍 Debian 特定故障排查

### 问题 1: Python venv 创建失败

**错误**: `The virtual environment was not created successfully`

**解决**:
```bash
sudo apt install -y python3-venv python3-dev
```

### 问题 2: pip 安装包失败

**错误**: `error: externally-managed-environment`

这是 Debian 12 的新安全特性。**解决方案**:

```bash
# 方法 1: 使用虚拟环境（推荐）
python3 -m venv /opt/xmmcg/venv
source /opt/xmmcg/venv/bin/activate
pip install -r requirements.txt

# 方法 2: 移除限制（不推荐）
sudo rm /usr/lib/python3.*/EXTERNALLY-MANAGED
```

### 问题 3: Certbot 不可用

**Debian 12 上推荐使用 snap**:
```bash
sudo apt install snapd
sudo snap install core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### 问题 4: Nginx 配置测试失败

```bash
# 检查语法
sudo nginx -t

# 查看详细错误
sudo journalctl -xe

# 常见问题：端口被占用
sudo netstat -tlnp | grep :80
```

---

## 📊 Debian 版本对照

| Debian 版本 | 代号 | Python 版本 | 支持状态 |
|------------|------|------------|---------|
| Debian 11  | Bullseye | 3.9 | ✅ 完全支持 |
| Debian 12  | Bookworm | 3.11 | ✅ 推荐 |
| Debian 10  | Buster   | 3.7 | ⚠️ 需升级 Python |

---

## 🔐 Debian 安全加固

### 1. 自动安全更新

```bash
sudo apt install -y unattended-upgrades apt-listchanges
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 2. 配置 fail2ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. SSH 安全配置

```bash
sudo nano /etc/ssh/sshd_config
# 修改:
# PermitRootLogin no
# PasswordAuthentication no  # 仅使用密钥登录
# Port 2222  # 改变默认端口

sudo systemctl restart sshd
```

---

## 💡 性能优化（Debian）

### 1. 优化 Gunicorn Workers

根据 CPU 核心数调整:
```bash
# 查看 CPU 核心数
nproc

# 编辑 gunicorn.service
sudo nano /etc/systemd/system/gunicorn.service
# 设置 workers = (2 × CPU核心数) + 1
```

### 2. 启用 Nginx 缓存

```bash
# 编辑 Nginx 配置
sudo nano /etc/nginx/sites-available/xmmcg

# 在 http 块中添加:
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m inactive=60m;
proxy_cache_key "$scheme$request_method$host$request_uri";
```

### 3. 启用 Gzip 压缩

Nginx 默认配置通常已启用，检查:
```bash
grep -i gzip /etc/nginx/nginx.conf
```

---

## 📞 Debian 支持资源

- Debian 官方文档: https://www.debian.org/doc/
- Debian Wiki: https://wiki.debian.org/
- Python on Debian: https://wiki.debian.org/Python

---

## ✅ 部署后检查清单

- [ ] 服务运行正常: `sudo systemctl status gunicorn nginx`
- [ ] 防火墙配置: `sudo ufw status`
- [ ] SSL 证书: `sudo certbot certificates`
- [ ] 日志无错误: `sudo journalctl -u gunicorn -n 50`
- [ ] 可以访问网站: `curl http://localhost`
- [ ] 可以访问管理后台: `/admin`
- [ ] 文件上传功能正常
- [ ] 静态文件加载正常

完整部署文档请参考: [COMPUTE_ENGINE_DEPLOYMENT.md](COMPUTE_ENGINE_DEPLOYMENT.md)
