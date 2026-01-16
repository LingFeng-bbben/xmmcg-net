# Token API 使用指南

## 📊 Token API 端点概览

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/users/token/` | 获取当前余额 | ✅ |
| POST | `/api/users/token/update/` | 设置余额（绝对值） | ✅ |
| POST | `/api/users/token/add/` | 增加 token | ✅ |
| POST | `/api/users/token/deduct/` | 扣除 token | ✅ |

---

## 🔍 API 详细说明

### 1. 获取 Token 余额

**请求**
```http
GET /api/users/token/
```

**响应**
```json
{
    "success": true,
    "user_id": 1,
    "username": "john_doe",
    "token": 500
}
```

---

### 2. 设置 Token 余额（绝对值）

直接设置用户的 token 值，通常由后端管理系统调用。

**请求**
```http
POST /api/users/token/update/
Content-Type: application/json

{
    "token": 1000
}
```

**成功响应**
```json
{
    "success": true,
    "message": "Token 已更新",
    "user_id": 1,
    "username": "john_doe",
    "old_token": 500,
    "new_token": 1000
}
```

**错误响应（无效的 token 值）**
```json
{
    "success": false,
    "errors": {
        "token": ["Token 不能为负数"]
    }
}
```

---

### 3. 增加 Token

增加用户的 token 余额，用于奖励、充值等操作。

**请求**
```http
POST /api/users/token/add/
Content-Type: application/json

{
    "amount": 100
}
```

**成功响应**
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

**错误响应（负数）**
```json
{
    "success": false,
    "message": "增加数量必须为正数，如需扣除请使用 /token/deduct/ 端点"
}
```

---

### 4. 扣除 Token ⭐ 新增

扣除用户的 token 余额，用于消费、处罚等操作。

**请求**
```http
POST /api/users/token/deduct/
Content-Type: application/json

{
    "amount": 50
}
```

**成功响应**
```json
{
    "success": true,
    "message": "Token 已扣除 50",
    "user_id": 1,
    "username": "john_doe",
    "old_token": 600,
    "new_token": 550,
    "amount_changed": -50
}
```

**错误响应（余额不足）**
```json
{
    "success": false,
    "message": "Token 余额不足。当前余额: 30，无法扣除 50"
}
```

**错误响应（无效的扣除数量）**
```json
{
    "success": false,
    "message": "扣除数量必须大于 0"
}
```

---

## 💻 使用场景示例

### 场景 1: 用户签到获得奖励
```bash
curl -X POST http://localhost:8000/api/users/token/add/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "amount": 10
  }'
```

### 场景 2: 用户消费 token
```bash
curl -X POST http://localhost:8000/api/users/token/deduct/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "amount": 50
  }'
```

### 场景 3: 查看账户余额
```bash
curl -X GET http://localhost:8000/api/users/token/ \
  -b cookies.txt
```

### 场景 4: 管理员初始化用户余额
```bash
curl -X POST http://localhost:8000/api/users/token/update/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "token": 5000
  }'
```

---

## 🔐 权限和安全

### 权限规则
- ✅ 所有 token API 都需要身份认证
- ✅ 用户只能操作自己的 token
- ⚠️ 建议前端不要直接暴露 `/token/update/` 端点

### 安全机制
- 🔒 Token 不能为负数
- 🔒 扣除时会检查余额是否足够
- 🔒  所有操作都有时间戳记录
- 🔒  增加和扣除是分离的端点，逻辑更清晰

---

## 📱 前端集成示例

### Vue 3 Composition API

```javascript
// API 服务
export const tokenService = {
    // 获取余额
    getBalance: () => api.get('/token/'),
    
    // 增加 token
    addToken: (amount) => api.post('/token/add/', { amount }),
    
    // 扣除 token
    deductToken: (amount) => api.post('/token/deduct/', { amount }),
    
    // 设置余额（管理员用）
    setToken: (token) => api.post('/token/update/', { token }),
};

// 使用示例
import { ref } from 'vue';
import { tokenService } from '@/services/authService';

export function useToken() {
    const balance = ref(0);
    const loading = ref(false);
    const error = ref(null);

    // 获取余额
    const getBalance = async () => {
        loading.value = true;
        try {
            const response = await tokenService.getBalance();
            balance.value = response.data.token;
        } catch (err) {
            error.value = err.response?.data?.message;
        } finally {
            loading.value = false;
        }
    };

    // 增加 token
    const addToken = async (amount) => {
        loading.value = true;
        try {
            const response = await tokenService.addToken(amount);
            balance.value = response.data.new_token;
            return response.data;
        } catch (err) {
            error.value = err.response?.data?.message;
            throw err;
        } finally {
            loading.value = false;
        }
    };

    // 扣除 token
    const deductToken = async (amount) => {
        loading.value = true;
        try {
            const response = await tokenService.deductToken(amount);
            balance.value = response.data.new_token;
            return response.data;
        } catch (err) {
            error.value = err.response?.data?.message;
            throw err;
        } finally {
            loading.value = false;
        }
    };

    return {
        balance,
        loading,
        error,
        getBalance,
        addToken,
        deductToken,
    };
}

// 在组件中使用
<template>
  <div class="token-widget">
    <!-- 显示余额 -->
    <div class="balance">
      <span class="label">虚拟货币:</span>
      <span class="amount">{{ balance }}</span>
    </div>

    <!-- 增加按钮 -->
    <button @click="handleAdd" :disabled="loading">增加</button>

    <!-- 扣除按钮 -->
    <button @click="handleDeduct" :disabled="loading">扣除</button>

    <!-- 错误提示 -->
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useToken } from '@/composables/useToken';

const { balance, loading, error, getBalance, addToken, deductToken } = useToken();

onMounted(() => {
  getBalance();
});

const handleAdd = async () => {
  try {
    await addToken(100);
    alert('成功增加 100 token');
  } catch (err) {
    alert('增加失败: ' + error.value);
  }
};

const handleDeduct = async () => {
  try {
    await deductToken(50);
    alert('成功扣除 50 token');
  } catch (err) {
    alert('扣除失败: ' + error.value);
  }
};
</script>

<style scoped>
.token-widget {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
}

.balance {
  font-weight: bold;
}

.amount {
  color: #e67e22;
  font-size: 18px;
}

button {
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  background: #3498db;
  color: white;
  cursor: pointer;
}

button:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.error {
  color: #e74c3c;
  margin-top: 10px;
}
</style>
```

---

## 📊 Token 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户虚拟货币系统                           │
└─────────────────────────────────────────────────────────────────┘

                          获取余额
                             │
                    GET /token/ 🔍
                             │
                             ▼
                    {token: 500}
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    增加 token          设置 token          扣除 token
    POST /add/          POST /update/       POST /deduct/
    {amount: 100}       {token: 1000}       {amount: 50}
        │                    │                    │
        ▼                    ▼                    ▼
    500 → 600            任意值 → 1000        500 → 450
    ✅ 成功                 ✅ 成功              ✅ 成功
                                              
                          错误情况
                             │
                             ▼
                    扣除数量 > 余额
                             │
                             ▼
                    返回 400 错误
                    "Token 余额不足"
```

---

## 🔄 API 对比

### 增加 vs 扣除

| 特性 | 增加 API | 扣除 API |
|------|---------|---------|
| 端点 | `/token/add/` | `/token/deduct/` |
| 参数 | `amount` | `amount` |
| 参数值 | 正整数 | 正整数 |
| 校验 | 拒绝负数 | 拒绝负数，检查余额 |
| 用途 | 奖励、充值 | 消费、处罚 |
| 错误处理 | 参数校验 | 参数校验 + 余额检查 |

### 增加 vs 设置

| 特性 | 增加 API | 设置 API |
|------|---------|---------|
| 操作类型 | 相对 (增量) | 绝对 (直接设置) |
| 需要知道 | 增加的数量 | 最终的余额 |
| 使用场景 | 日常操作 | 管理员操作 |
| 原值 | 自动获取 | 可选 (可查询后设置) |

---

## 🧪 测试用例

### 测试 1: 正常增加
```json
请求: POST /token/add/
{
  "amount": 100
}

期望: 200 OK
{
  "success": true,
  "message": "Token 已增加 100"
}
```

### 测试 2: 正常扣除
```json
请求: POST /token/deduct/
{
  "amount": 50
}

期望: 200 OK
{
  "success": true,
  "message": "Token 已扣除 50"
}
```

### 测试 3: 扣除时余额不足
```json
请求: POST /token/deduct/
{
  "amount": 1000
}

期望: 400 BAD REQUEST
{
  "success": false,
  "message": "Token 余额不足。当前余额: 450，无法扣除 1000"
}
```

### 测试 4: 增加时使用负数
```json
请求: POST /token/add/
{
  "amount": -50
}

期望: 400 BAD REQUEST
{
  "success": false,
  "message": "增加数量必须为正数，如需扣除请使用 /token/deduct/ 端点"
}
```

---

## 📝 版本历史

### v1.0 (原始版本)
- 单一的 `/token/add/` 端点
- 支持正数和负数

### v1.1 ⭐ 新版本 (当前)
- 分离 `/token/add/` 和 `/token/deduct/` 端点
- `/token/add/` 只接受正数
- `/token/deduct/` 专门处理扣除，包含余额检查
- 更清晰的 API 设计
- 更好的错误提示

---

版本: 1.1  
最后更新: 2026-01-16
