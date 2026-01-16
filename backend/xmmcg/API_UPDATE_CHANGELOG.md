# API 更新说明

## 变更摘要

### ✅ 密码安全审计结果
**现有代码不存在前端明文传回密码的问题** - 所有密码相关操作都正确处理。

### 📝 API 变更

#### 移除的字段
- ❌ `first_name` - 从注册和用户信息中移除
- ❌ `last_name` - 从注册和用户信息中移除

#### 新增的字段
- ✅ `token` - 用户虚拟货币余额（只读，通过专门的 API 修改）

#### 新增的 API 端点（3 个）

**1. 获取用户 token 余额**
```
GET /api/users/token/
权限: IsAuthenticated
```

请求: 无
```json
{}
```

响应:
```json
{
    "success": true,
    "user_id": 1,
    "username": "john_doe",
    "token": 100
}
```

---

**2. 设置用户 token 值**
```
POST /api/users/token/update/
权限: IsAuthenticated
```

请求:
```json
{
    "token": 500
}
```

响应:
```json
{
    "success": true,
    "message": "Token 已更新",
    "user_id": 1,
    "username": "john_doe",
    "old_token": 100,
    "new_token": 500
}
```

---

**3. 增加或扣除用户 token（增量操作）**
```
POST /api/users/token/add/
权限: IsAuthenticated
```

请求 - 增加 100 token:
```json
{
    "amount": 100
}
```

请求 - 扣除 50 token:
```json
{
    "amount": -50
}
```

响应:
```json
{
    "success": true,
    "message": "Token 已增加 100",
    "user_id": 1,
    "username": "john_doe",
    "old_token": 500,
    "new_token": 600,
    "amount_changed": 100
}
```

错误响应 - token 不足:
```json
{
    "success": false,
    "message": "Token 余额不足。当前余额: 50，无法扣除 100"
}
```

---

### 修改的 API 端点

#### 注册 API
**变更**: 移除了 `first_name` 和 `last_name` 字段

旧请求:
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

新请求:
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
}
```

新响应:
```json
{
    "success": true,
    "message": "注册成功",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "is_active": true,
        "date_joined": "2024-01-16T10:00:00Z",
        "token": 0
    }
}
```

---

#### 获取用户信息 API (`/me/`)
**变更**: 添加了 `token` 字段，移除了 `first_name` 和 `last_name`

响应:
```json
{
    "success": true,
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "is_active": true,
        "date_joined": "2024-01-16T10:00:00Z",
        "token": 0
    }
}
```

---

#### 更新用户信息 API (`/profile/`)
**变更**: 现在只支持修改 `email` 字段

请求:
```json
{
    "email": "newemail@example.com"
}
```

响应:
```json
{
    "success": true,
    "message": "个人信息已更新",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "newemail@example.com",
        "is_active": true,
        "date_joined": "2024-01-16T10:00:00Z",
        "token": 100
    }
}
```

尝试修改不允许的字段:
```json
{
    "first_name": "John"
}
```

错误响应:
```json
{
    "success": false,
    "message": "不允许修改字段: first_name"
}
```

---

## 数据库变更

### 新表: `users_userprofile`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Foreign Key | 关联到 User 表 (一对一关系) |
| token | Integer | 虚拟货币余额，默认为 0 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 最后更新时间 |

---

## 使用场景示例

### 场景 1: 用户获得奖励
```bash
curl -X POST http://localhost:8000/api/users/token/add/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "amount": 100
  }'
```

### 场景 2: 用户消费虚拟货币
```bash
curl -X POST http://localhost:8000/api/users/token/add/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "amount": -50
  }'
```

### 场景 3: 管理员直接设置用户余额
```bash
curl -X POST http://localhost:8000/api/users/token/update/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "token": 1000
  }'
```

### 场景 4: 查看用户余额
```bash
curl -X GET http://localhost:8000/api/users/token/ \
  -b cookies.txt
```

---

## 安全考虑

### Token 相关 API 的权限
- ✅ 用户**可以**查看自己的 token
- ✅ 用户**可以**修改自己的 token（通过 `/token/update/` 或 `/token/add/`）
- ⚠️ 前端应该**谨慎**调用修改 token 的 API

### 建议的后端实现方式
在生产环境中，你应该：
1. 限制前端对 token 的直接修改权限
2. 在后端逻辑中处理大部分 token 的增减
3. 通过 Django Admin 或后台管理系统进行管理员操作

例如，添加权限检查：
```python
# 在 views.py 中
if not request.user.is_staff:
    return Response({'error': '权限不足'}, status=403)
```

---

## 迁移指南

### 如果你已经有现有用户

已有的用户会自动创建对应的 `UserProfile`，初始 token 为 0。

### 对前端的影响

#### 注册表单
```javascript
// 旧代码
const data = {
    username,
    email,
    password,
    password_confirm,
    first_name,
    last_name
};

// 新代码
const data = {
    username,
    email,
    password,
    password_confirm
    // 移除 first_name 和 last_name
};
```

#### 用户信息显示
```javascript
// 旧代码
<div>
    <p>名字: {{user.first_name}} {{user.last_name}}</p>
</div>

// 新代码
<div>
    <p>虚拟货币: {{user.token}}</p>
</div>
```

#### 修改个人信息
```javascript
// 旧代码
await api.put('/profile/', {
    email: newEmail,
    first_name: newFirstName,
    last_name: newLastName
});

// 新代码
await api.put('/profile/', {
    email: newEmail
    // 只允许修改 email
});
```

---

## API 端点总结

| 方法 | 端点 | 说明 | 认证 | 新增 |
|------|------|------|------|------|
| GET | `/token/` | 获取 token 余额 | ✅ | ✨ |
| POST | `/token/update/` | 设置 token 值 | ✅ | ✨ |
| POST | `/token/add/` | 增加/扣除 token | ✅ | ✨ |
| POST | `/register/` | 注册 | ❌ | 修改 |
| GET | `/me/` | 获取用户信息 | ✅ | 修改 |
| PUT | `/profile/` | 修改用户信息 | ✅ | 修改 |

---

版本: 1.1.0  
更新日期: 2026-01-16
