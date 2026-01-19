# 确保域名已解析到服务器 IP
nslookup xmmcg.net

# 申请 SSL 证书（Certbot 会自动修改 nginx 配置）
sudo certbot --nginx -d xmmcg.net -d xmmcg.majdata.net

# 测试自动续期
sudo certbot renew --dry-run