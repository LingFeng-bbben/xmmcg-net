# 谱面竞标流程指南

## 概述

该功能支持在第一阶段竞标与制谱完成后，进行**第二轮谱面竞标**，用户竞标半成品谱面并完成它们的后半部分。

---

## 核心流程

### 1. **第一阶段：歌曲竞标 + 制谱上传**
- 用户竞标歌曲 → 中标者上传音频、封面、maidata.txt → 系统保存为 `status='part_submitted'`（半成品）

### 2. **第二阶段：谱面竞标轮次创建**（Admin 操作）
- **请求**：
  ```
  POST /api/bidding-rounds/auto-create-chart-round/
  Content-Type: application/json
  
  {
    "name": "第二轮竞标 - 谱面完成",
    "phase_id": 3  // 可选，指定关联的 CompetitionPhase
  }
  ```

- **响应**：
  ```json
  {
    "success": true,
    "message": "成功创建谱面竞标轮次，包含 5 个半成品谱面",
    "round": {
      "id": 2,
      "name": "第二轮竞标 - 谱面完成",
      "bidding_type": "chart",
      "status": "active"
    },
    "available_charts_count": 5
  }
  ```

- **机制**：
  - 自动筛选所有 `status='part_submitted'` 的谱面作为竞标标的
  - 创建一个新的 `BiddingRound` 记录，`bidding_type='chart'`，`status='active'`
  - 不会自动生成 Bid 记录（用户需要主动竞标）

### 3. **用户竞标半成品谱面**（用户操作）
- **获取可竞标的谱面列表**：
  ```
  GET /api/bidding-rounds/{round_id}/available-charts/?page=1&page_size=20
  ```

- **响应**：
  ```json
  {
    "success": true,
    "round": {
      "id": 2,
      "name": "第二轮竞标 - 谱面完成",
      "bidding_type": "chart"
    },
    "count": 5,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "results": [
      {
        "id": 10,
        "song": {
          "id": 3,
          "title": "粉紅色の恋",
          ...
        },
        "designer": "谱师A",
        "status": "part_submitted",
        "status_display": "半成品",
        "created_at": "2026-01-18T10:00:00Z",
        ...
      },
      ...
    ]
  }
  ```

- **用户竞标**：
  ```
  POST /api/bids/
  Content-Type: application/json
  
  {
    "chart_id": 10,
    "amount": 150,
    "round_id": 2
  }
  ```

  **响应**：
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
        "creator": "谱师A"
      },
      "amount": 150,
      "created_at": "2026-01-18T11:30:00Z"
    }
  }
  ```

### 4. **后端分配竞标**（Admin 操作）
- **触发分配**：
  ```
  POST /api/bids/allocate/
  Content-Type: application/json
  
  {
    "round_id": 2
  }
  ```

- **分配算法**（已支持谱面类型）：
  1. 按竞标金额从高到低排序
  2. 依次为每个用户分配一个谱面
  3. 同一谱面的其他竞标标记为 `drop`
  4. 对未获得谱面的用户，从未分配的谱面中随机分配
  5. 设置竞标轮次状态为 `completed`

- **分配结果**：创建 `BidResult` 记录
  ```
  BidResult:
    - bidding_round: 2
    - user: 用户B
    - bid_type: 'chart'
    - chart: 半成品谱面 #10
    - bid_amount: 150
    - allocation_type: 'win'  // 或 'random'
  ```

### 5. **用户获取分配结果**（用户操作）
- **请求**：
  ```
  GET /api/bid-results/?round_id=2
  ```

- **响应**：
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
          "creator_username": "谱师A",
          "average_score": null
        }
      }
    ]
  }
  ```

---

## API 端点总结

### 新增端点

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/bidding-rounds/auto-create-chart-round/` | Admin | 创建谱面竞标轮次 |
| GET | `/api/bidding-rounds/{round_id}/available-charts/` | 已认证 | 获取可竞标的半成品谱面列表 |

### 现有端点（已支持谱面竞标）

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/bids/` | 已认证 | 创建竞标（支持 chart_id 参数） |
| POST | `/api/bids/allocate/` | Admin | 分配竞标（自动识别谱面类型） |
| GET | `/api/bid-results/` | 已认证 | 获取竞标结果 |

---

## 前端集成示例

### 1. 显示可竞标的谱面列表
```javascript
// 获取谱面竞标轮次的可用谱面
async function getAvailableChartsForBidding(roundId) {
  const response = await fetch(`/api/bidding-rounds/${roundId}/available-charts/`)
  return response.json()
}

// 返回包含所有半成品谱面的列表
// UI 显示卡片，用户可选择竞标的谱面
```

### 2. 创建竞标
```javascript
// 用户选择谱面和出价后
async function placeBid(chartId, amount, roundId) {
  const response = await fetch('/api/bids/', {
    method: 'POST',
    body: JSON.stringify({
      chart_id: chartId,
      amount: amount,
      round_id: roundId
    })
  })
  return response.json()
}
```

### 3. 获取竞标结果
```javascript
// 分配完成后，用户查看中标的谱面
async function getBidResults(roundId) {
  const response = await fetch(`/api/bid-results/?round_id=${roundId}`)
  return response.json()
}

// 返回用户中标的谱面列表
// UI 显示用户需要完成的谱面
```

---

## 现状与支持

### ✅ 已支持
- ✅ 竞标模型支持 `bidding_type='chart'`
- ✅ 用户可竞标具体的谱面（chart_id）
- ✅ 分配算法支持谱面竞标分配
- ✅ 获取可竞标的半成品谱面列表 API
- ✅ 自动创建谱面竞标轮次 API

### 🔧 进行中 / 计划中
- 后端验证：确保谱面竞标时只能竞标 `status='part_submitted'` 的谱面
- 前端：集成谱面竞标 UI（显示可竞标列表、竞标界面、结果展示）

---

## 使用场景示例

### 完整流程演示

**时间线**：
```
Day 1-7:   第一阶段（歌曲竞标）
           - 用户竞标歌曲
           - 中标用户上传音频、封面、maidata.txt
           - 系统保存为 status='part_submitted'

Day 8:     第二阶段启动（谱面竞标）
           - Admin: POST /api/bidding-rounds/auto-create-chart-round/
           - 系统自动筛选所有 half-finished charts
           - 创建竞标轮次，状态 'active'

Day 8-14:  用户竞标阶段
           - 用户: GET /api/bidding-rounds/2/available-charts/
           - 用户: POST /api/bids/ (竞标谱面)
           - 用户查看自己的竞标: GET /api/bids/?round_id=2

Day 15:    分配阶段
           - Admin: POST /api/bids/allocate/?round_id=2
           - 系统分配谱面给用户

Day 15+:   用户查看结果
           - 用户: GET /api/bid-results/?round_id=2
           - 用户开始完成谱面的后半部分
```

---

## 常见问题

**Q: 谱面竞标轮次自动筛选哪些谱面？**
A: 所有 `status='part_submitted'` 的谱面。这些是第一阶段用户上传但尚未完成后半部分的谱面。

**Q: 一个用户可以竞标多个谱面吗？**
A: 可以。用户可以竞标最多 `MAX_BIDS_PER_USER` 个谱面，但分配后只能中标一个。

**Q: 如果竞标数少于可用谱面数，会怎样？**
A: 未被竞标的谱面将保持 `status='part_submitted'`，不会被分配给任何人。

**Q: 可以创建多个谱面竞标轮次吗？**
A: 可以。每次调用 `auto-create-chart-round` 都会创建一个新轮次，都会包含所有半成品谱面。

---

## 后续优化建议

1. **验证增强**：在用户竞标时验证谱面状态必须是 `part_submitted`
2. **前端 UI**：实现完整的谱面竞标页面（列表、竞标表单、结果展示）
3. **统计分析**：添加竞标统计、热门谱面排名等
4. **自动流程**：支持后台定时自动创建谱面竞标轮次
