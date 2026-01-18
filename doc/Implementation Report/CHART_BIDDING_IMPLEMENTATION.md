# 实现总结：自动谱面竞标轮次创建与筛选

## 概述

支持 Admin 在后台通过一个 API 调用，**自动创建谱面竞标轮次并自动筛选所有半成品谱面作为竞标标的**。用户无需手动设置每个标的，系统会自动识别可竞标的谱面。

---

## 功能实现

### ✅ 已实现的功能

#### 1. **自动创建谱面竞标轮次** 
- **端点**：`POST /api/bidding-rounds/auto-create-chart-round/`
- **权限**：Admin Only
- **请求示例**：
  ```json
  {
    "name": "第二轮竞标 - 谱面完成",
    "phase_id": 3  // 可选，绑定到某个 CompetitionPhase
  }
  ```
- **响应示例**：
  ```json
  {
    "success": true,
    "message": "成功创建谱面竞标轮次，包含 12 个半成品谱面",
    "round": {
      "id": 5,
      "name": "第二轮竞标 - 谱面完成",
      "bidding_type": "chart",
      "status": "active"
    },
    "available_charts_count": 12
  }
  ```
- **功能**：
  - 自动查询所有 `status='part_submitted'` 的谱面
  - 统计半成品数量，若无则返回错误
  - 创建新的 `BiddingRound` 记录，设置 `bidding_type='chart'`，`status='active'`

#### 2. **获取可竞标的谱面列表**
- **端点**：`GET /api/bidding-rounds/{round_id}/available-charts/`
- **权限**：已认证用户
- **查询参数**：`page=1&page_size=20`
- **响应**：包含所有 `status='part_submitted'` 的谱面
- **功能**：
  - 分页显示可竞标的半成品谱面
  - 返回谱面详细信息（歌曲、设计者、创建时间等）

#### 3. **谱面竞标时的状态验证**
- **位置**：`BiddingService.create_bid()`
- **验证规则**：
  ```python
  if chart and chart.status != 'part_submitted':
      raise ValidationError(f'只能竞标半成品谱面，该谱面当前状态为：{chart.get_status_display()}')
  ```
- **功能**：确保用户只能竞标处于半成品状态的谱面

#### 4. **现有分配逻辑已支持谱面竞标**
- 利用现有的 `BiddingService.allocate_bids()` 方法
- 当 `BiddingRound.bidding_type='chart'` 时，自动：
  - 获取所有谱面竞标
  - 按出价从高到低分配
  - 返回 `BidResult` 记录

---

## 完整工作流程

```
Step 1: Admin 创建谱面竞标轮次
  POST /api/bidding-rounds/auto-create-chart-round/
  ↓
  ✓ 系统自动筛选所有 status='part_submitted' 的谱面
  ✓ 创建 BiddingRound，bidding_type='chart'，status='active'
  ✓ 返回可竞标的谱面数量

Step 2: 用户获取可竞标的谱面列表
  GET /api/bidding-rounds/{round_id}/available-charts/
  ↓
  ✓ 返回所有半成品谱面列表

Step 3: 用户创建竞标
  POST /api/bids/
  Body: { "chart_id": 10, "amount": 150, "round_id": 5 }
  ↓
  ✓ 验证谱面状态必须是 'part_submitted'
  ✓ 验证不能竞标自己的谱面
  ✓ 验证代币余额
  ✓ 创建 Bid 记录

Step 4: Admin 分配竞标
  POST /api/bids/allocate/
  Body: { "round_id": 5 }
  ↓
  ✓ 按出价从高到低分配谱面
  ✓ 每个用户最多中标一个谱面
  ✓ 未中标用户随机分配
  ✓ 创建 BidResult 记录

Step 5: 用户查看竞标结果
  GET /api/bid-results/?round_id=5
  ↓
  ✓ 返回用户中标的谱面信息
  ✓ 用户开始完成谱面的后半部分
```

---

## 代码改动

### 1. `views.py` 新增两个端点

#### `get_available_charts_for_round()`
- 获取指定竞标轮次的可竞标谱面列表
- 支持分页

#### `auto_create_chart_bidding_round()`
- 自动创建谱面竞标轮次
- 自动筛选半成品谱面
- 返回统计信息

### 2. `urls.py` 新增路由

```python
path('bidding-rounds/<int:round_id>/available-charts/', views.get_available_charts_for_round, name='available-charts'),
path('bidding-rounds/auto-create-chart-round/', views.auto_create_chart_bidding_round, name='auto-create-chart-round'),
```

### 3. `bidding_service.py` 增强验证

在 `create_bid()` 中添加：
```python
if chart and chart.status != 'part_submitted':
    raise ValidationError(f'只能竞标半成品谱面，该谱面当前状态为：{chart.get_status_display()}')
```

---

## 设计思想

### 为什么不自动生成 Bid 记录？

当 Admin 创建谱面竞标轮次时，**不自动生成 Bid 记录**，而是让用户主动竞标，原因：

1. **灵活性**：不同用户感兴趣的谱面不同，自动竞标所有目标会浪费代币
2. **选择权**：用户可以根据自己的偏好和代币余额选择竞标
3. **公平性**：所有半成品谱面是平等的，任何用户都可以竞标任何一个
4. **易维护**：无需维护额外的关联表，利用现有的 Bid 模型

### 为什么验证谱面状态？

为了防止：
1. 用户竞标已完成的谱面（浪费代币）
2. 系统数据不一致（谱面被修改了状态）
3. 混乱的竞标流程（不清楚竞标的是什么）

---

## 使用指南（Admin）

### 创建新的谱面竞标轮次

```bash
# 方式 1：通过 curl
curl -X POST http://localhost:8000/api/bidding-rounds/auto-create-chart-round/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "第二轮竞标 - 谱面完成",
    "phase_id": 3
  }'

# 方式 2：通过 Django Admin Shell
from songs.models import BiddingRound
from songs.views import auto_create_chart_bidding_round
# ... 或通过 Python 调用 API
```

### 观察可竞标的谱面

```bash
curl http://localhost:8000/api/bidding-rounds/5/available-charts/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 分配竞标

```bash
curl -X POST http://localhost:8000/api/bids/allocate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"round_id": 5}'
```

---

## 测试建议

### 单元测试

```python
def test_auto_create_chart_round():
    # 1. 创建半成品谱面
    chart1 = Chart.objects.create(status='part_submitted', ...)
    chart2 = Chart.objects.create(status='part_submitted', ...)
    
    # 2. 创建谱面竞标轮次
    response = client.post('/api/bidding-rounds/auto-create-chart-round/', {
        'name': 'Test Round'
    })
    
    # 3. 验证轮次创建
    assert response.status_code == 201
    assert response.json()['available_charts_count'] == 2
    
    # 4. 验证可竞标列表
    round_id = response.json()['round']['id']
    resp = client.get(f'/api/bidding-rounds/{round_id}/available-charts/')
    assert len(resp.json()['results']) == 2
```

### 集成测试

```python
def test_full_chart_bidding_flow():
    # 1. 创建谱面竞标轮次
    # 2. 用户竞标谱面
    # 3. Admin 分配
    # 4. 验证结果
```

---

## 后续优化

- [ ] 支持批量创建多个谱面竞标轮次
- [ ] 支持指定具体的谱面进行竞标（而不是所有 part_submitted）
- [ ] 前端 UI：显示谱面竞标列表、竞标对话框、结果展示
- [ ] 统计分析：谱面热度、竞标趋势等
- [ ] 自动流程：定时创建谱面竞标轮次

---

## 常见问题

**Q: 创建谱面竞标轮次时，能否只选择特定的谱面？**
A: 当前不支持，所有 `part_submitted` 的谱面都会被包含。若需要选择，可以手动设置谱面状态或修改 API。

**Q: 一个用户能竞标多个谱面吗？**
A: 可以，最多 `MAX_BIDS_PER_USER` 个。但分配后只能中标一个。

**Q: 如果没有任何半成品谱面，会怎样？**
A: API 返回 400 错误，轮次不会被创建。

**Q: 能否修改已创建的竞标轮次？**
A: 可以通过 Django Admin 或修改 BiddingRound 模型来调整，但 API 未提供直接支持。

