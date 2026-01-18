# 后台一键创建谱面竞标轮次 - 功能验证与使用指南

## 📋 需求回顾

用户问题：
> "现在的代码支不支持只需要我在后台重新创建一个新的竞标轮次并选择为谱面类型就可以自动将筛选出所有的半成品谱面设为新的标的进行竞标？"

---

## ✅ 功能状态：已完全实现

现在系统**完全支持**这个需求。Admin 可以通过一个简单的 API 调用或 Django Admin 创建新的谱面竞标轮次，系统会自动：
1. ✅ 识别轮次为谱面竞标类型
2. ✅ 自动筛选所有状态为 `part_submitted`（半成品）的谱面
3. ✅ 将这些谱面设置为本轮次的竞标标的

---

## 🚀 如何使用

### 方式 1：通过 API（推荐）

**创建谱面竞标轮次：**

```bash
POST /api/bidding-rounds/auto-create-chart-round/

Content-Type: application/json
Authorization: Bearer [ADMIN_TOKEN]

{
  "name": "第二轮竞标 - 谱面完成",
  "phase_id": 3  // 可选，绑定到某个比赛阶段
}
```

**响应示例：**

```json
{
  "success": true,
  "message": "成功创建谱面竞标轮次，包含 8 个半成品谱面",
  "round": {
    "id": 2,
    "name": "第二轮竞标 - 谱面完成",
    "bidding_type": "chart",
    "status": "active"
  },
  "available_charts_count": 8
}
```

### 方式 2：通过 Django Admin

1. 进入 Django Admin (`/admin`)
2. 导航到 `BiddingRound` 模块
3. 创建新记录：
   - `name`: "第二轮竞标 - 谱面完成"
   - `bidding_type`: 选择 "谱面竞标"（chart）
   - `status`: 选择 "进行中"（active）
   - `competition_phase`: 可选

4. 保存即可！系统自动将所有半成品谱面作为竞标标的

---

## 🔄 完整使用流程

### Step 1: 查看可竞标的谱面

创建轮次后，用户可以查看可竞标的谱面列表：

```bash
GET /api/bidding-rounds/{round_id}/available-charts/?page=1&page_size=20

Authorization: Bearer [USER_TOKEN]
```

**响应示例：**

```json
{
  "success": true,
  "round": {
    "id": 2,
    "name": "第二轮竞标 - 谱面完成",
    "bidding_type": "chart"
  },
  "count": 8,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "results": [
    {
      "id": 10,
      "song": {
        "id": 3,
        "title": "粉紅色の恋",
        "artist": "..."
      },
      "designer": "谱师 A",
      "status": "part_submitted",
      "status_display": "半成品",
      "created_at": "2026-01-18T10:00:00Z",
      "audio_url": "http://...",
      "cover_url": "http://...",
      "average_score": null,
      "review_count": 0
    },
    ...
  ]
}
```

### Step 2: 用户竞标谱面

用户选择感兴趣的谱面进行竞标：

```bash
POST /api/bids/

Content-Type: application/json
Authorization: Bearer [USER_TOKEN]

{
  "chart_id": 10,
  "amount": 150,
  "round_id": 2
}
```

**系统验证：**
- ✅ 谱面状态必须是 `part_submitted`
- ✅ 用户不能竞标自己的谱面
- ✅ 用户代币余额充足
- ✅ 未超过最大竞标数量

**响应示例：**

```json
{
  "success": true,
  "message": "竞标已创建",
  "bid": {
    "id": 45,
    "bid_type": "chart",
    "target": {
      "id": 10,
      "title": "粉紅色の恋",
      "creator": "谱师 A"
    },
    "amount": 150,
    "created_at": "2026-01-18T11:30:00Z"
  }
}
```

### Step 3: Admin 分配竞标

当竞标期结束，Admin 触发分配：

```bash
POST /api/bids/allocate/

Content-Type: application/json
Authorization: Bearer [ADMIN_TOKEN]

{
  "round_id": 2
}
```

**分配算法：**
1. 按出价从高到低排序
2. 依次为每个用户分配一个不同的谱面
3. 同一谱面的其他竞标标记为 `drop`
4. 未获得谱面的用户从未分配的谱面中随机分配
5. 设置轮次状态为 `completed`

**响应示例：**

```json
{
  "success": true,
  "message": "竞标分配完成",
  "round": {
    "id": 2,
    "name": "第二轮竞标 - 谱面完成",
    "status": "completed"
  },
  "statistics": {
    "total_users": 8,
    "total_charts": 8,
    "allocations": 8,
    "random_allocations": 0,
    "tokens_deducted": 1200
  }
}
```

### Step 4: 用户查看结果

用户查看自己中标的谱面：

```bash
GET /api/bid-results/?round_id=2

Authorization: Bearer [USER_TOKEN]
```

**响应示例：**

```json
{
  "success": true,
  "round": {
    "id": 2,
    "name": "第二轮竞标 - 谱面完成",
    "status": "completed",
    "completed_at": "2026-01-18T14:00:00Z"
  },
  "result_count": 1,
  "results": [
    {
      "id": 65,
      "bid_type": "chart",
      "bid_type_display": "谱面竞标",
      "bid_amount": 150,
      "allocation_type": "win",
      "allocation_type_display": "竞标获胜",
      "chart": {
        "id": 10,
        "song_title": "粉紅色の恋",
        "creator_username": "谱师 A",
        "average_score": null
      }
    }
  ]
}
```

用户即可开始完成这个半成品谱面的后半部分。

---

## 🔍 技术实现细节

### 后端改动

| 文件 | 改动 | 说明 |
|------|------|------|
| `views.py` | 新增 `get_available_charts_for_round()` | 获取可竞标的半成品谱面列表 |
| `views.py` | 新增 `auto_create_chart_bidding_round()` | 自动创建谱面竞标轮次 |
| `urls.py` | 新增两条路由 | 注册上述两个新端点 |
| `bidding_service.py` | 增强 `create_bid()` 验证 | 确保只能竞标状态为 `part_submitted` 的谱面 |

### 已支持但不需要改动

- ✅ `BiddingService.allocate_bids()` - 已支持谱面竞标类型
- ✅ `BiddingRound.bidding_type` - 已支持 'chart' 值
- ✅ 用户竞标 API (`POST /api/bids/`) - 已支持 `chart_id` 参数
- ✅ 竞标结果查询 (`GET /api/bid-results/`) - 已支持谱面结果

---

## 📊 数据流示意

```
第一阶段（歌曲竞标）
├─ 用户竞标歌曲
├─ 中标者上传谱面（音频、封面、maidata.txt）
└─ 系统保存为 Chart(status='part_submitted')

         ↓

第二阶段（谱面竞标）
├─ Admin: POST /api/bidding-rounds/auto-create-chart-round/
│  ├─ 系统自动查询所有 Chart.objects.filter(status='part_submitted')
│  └─ 创建新的 BiddingRound(bidding_type='chart')
│
├─ 用户: GET /api/bidding-rounds/{round_id}/available-charts/
│  └─ 系统返回所有可竞标的谱面列表
│
├─ 用户: POST /api/bids/ (竞标具体谱面)
│  └─ 系统验证谱面状态、代币余额等
│
├─ Admin: POST /api/bids/allocate/
│  └─ 系统分配谱面给用户（按出价排序）
│
└─ 用户: GET /api/bid-results/
   └─ 用户获取中标的谱面并开始完成
```

---

## 💡 关键特性

### 1️⃣ **自动筛选**
- 创建轮次时自动识别所有 `part_submitted` 的谱面
- 无需手动逐个添加标的
- 如果没有半成品谱面，API 返回错误

### 2️⃣ **灵活竞标**
- 用户可自由选择竞标哪些谱面
- 最多竞标 `MAX_BIDS_PER_USER` 个
- 但分配后只中标一个

### 3️⃣ **安全验证**
- ✅ 竞标时验证谱面状态必须是 `part_submitted`
- ✅ 防止竞标自己的谱面
- ✅ 验证代币余额
- ✅ 防止重复竞标同一谱面

### 4️⃣ **公平分配**
- 按出价从高到低分配
- 同价格随机打乱顺序
- 未竞标的用户从剩余目标中随机分配

---

## 🎯 常见用法示例

### 示例 1: 完整的二轮竞标流程

```python
# 第一轮竞标完成后，创建第二轮

# 1. Admin 创建谱面竞标轮次
response = requests.post(
    'http://localhost:8000/api/bidding-rounds/auto-create-chart-round/',
    json={'name': '第二轮竞标 - 谱面完成'},
    headers={'Authorization': 'Bearer admin_token'}
)
round_id = response.json()['round']['id']
# 返回: 包含 12 个半成品谱面

# 2. 用户查看可竞标列表
response = requests.get(
    f'http://localhost:8000/api/bidding-rounds/{round_id}/available-charts/',
    headers={'Authorization': 'Bearer user_token'}
)
# 返回: 12 个可竞标的谱面

# 3. 用户竞标 3 个谱面
for chart_id in [10, 11, 12]:
    requests.post(
        'http://localhost:8000/api/bids/',
        json={'chart_id': chart_id, 'amount': 100, 'round_id': round_id},
        headers={'Authorization': 'Bearer user_token'}
    )

# 4. Admin 分配竞标
response = requests.post(
    'http://localhost:8000/api/bids/allocate/',
    json={'round_id': round_id},
    headers={'Authorization': 'Bearer admin_token'}
)
# 返回: 分配完成，12 个谱面已分配给 12 个用户

# 5. 用户查看中标结果
response = requests.get(
    f'http://localhost:8000/api/bid-results/?round_id={round_id}',
    headers={'Authorization': 'Bearer user_token'}
)
# 返回: 用户中标的 1 个谱面
```

### 示例 2: 通过 Django Shell

```python
from django.core.management.call_commands import call_command
from songs.models import BiddingRound, Chart
from songs.views import auto_create_chart_bidding_round

# 查看有多少个半成品谱面
print(f"当前半成品谱面数: {Chart.objects.filter(status='part_submitted').count()}")

# 创建新的谱面竞标轮次
round_obj = BiddingRound.objects.create(
    name='第二轮竞标 - 谱面完成',
    bidding_type='chart',
    status='active'
)
print(f"创建成功: {round_obj.name} (ID: {round_obj.id})")

# 验证半成品谱面可以竞标
available = Chart.objects.filter(status='part_submitted')
print(f"可竞标的谱面: {available.count()} 个")
```

---

## ⚠️ 注意事项

1. **谱面状态**：只有 `status='part_submitted'` 的谱面才能被竞标
2. **用户限制**：用户不能竞标自己的谱面
3. **代币验证**：竞标时需要验证用户的代币余额
4. **轮次状态**：只能在 `status='active'` 的轮次中创建新竞标
5. **分配一次性**：分配后轮次状态变为 `completed`，无法再竞标

---

## 📝 相关文档

- [CHART_BIDDING_GUIDE.md](./CHART_BIDDING_GUIDE.md) - 详细的谱面竞标流程指南
- [CHART_BIDDING_IMPLEMENTATION.md](./CHART_BIDDING_IMPLEMENTATION.md) - 实现细节和设计思想
- [BIDDING_SYSTEM_GUIDE.md](./BIDDING_SYSTEM_GUIDE.md) - 竞标系统总体指南

---

## ✨ 总结

**现在你可以通过一个简单的 API 调用或几个 Django Admin 点击，自动创建谱面竞标轮次并自动筛选所有半成品谱面作为竞标标的。系统会完全自动处理剩余的所有流程。**

需要的话，我可以继续实现前端页面来展示这个功能，让用户界面更直观。

