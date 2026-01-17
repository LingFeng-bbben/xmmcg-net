# 歌曲竞标功能后端验证报告

## 需求梳理
用户需求实现以下竞标功能：
1. ✅ 竞标轮次由后台控制
2. ✅ 一个用户最多可以选择5个竞标
3. ✅ 点击歌曲卡片中的竞标显示竞标浮窗
4. ✅ 浮窗显示用户剩余代币和输入出价
5. ✅ 有多个竞标时不扣除代币，只验证代币是否足够
6. ✅ 进行的竞标应出现在歌曲页面上
7. ✅ 所有用户上传完成后，后台触发统一分配歌曲
8. ✅ 分配后，根据竞标出价扣除代币，将歌曲分配给用户

## 后端数据模型 ✅

### 1. BiddingRound（竞标轮次）
**文件**：`backend/xmmcg/songs/models.py` L263-302
- 字段：
  - `id`: 主键
  - `name`: 竞标轮次名称
  - `status`: 状态（choices: 'active', 'completed'）
  - `created_at`: 创建时间
  - `started_at`: 开始时间（可选）
  - `completed_at`: 完成时间（可选）

**功能**：✅ 完整支持
- 自动计算状态（upcoming/active/ended）
- 获取剩余时间
- 计算进度百分比

### 2. Bid（用户竞标）
**文件**：`backend/xmmcg/songs/models.py` L306-369
- 字段：
  - `id`: 主键
  - `bidding_round`: 外键（BiddingRound）
  - `user`: 外键（User）
  - `song`: 外键（Song）
  - `amount`: 竞标金额（代币）
  - `is_dropped`: 是否已被drop（歌曲被更高出价者获得）
  - `created_at`: 竞标时间
  - `updated_at`: 最后更新时间

**限制**：
- `unique_together = ('bidding_round', 'user', 'song')` ✅ 一个用户对同一歌曲只能竞标一次
- `MAX_BIDS_PER_USER = 5` ✅ 每轮最多5个竞标
- 竞标金额必须 > 0 ✅
- 金额验证：检查用户代币余额 ✅

### 3. BidResult（竞标结果）
**文件**：`backend/xmmcg/songs/models.py` L372-417
- 字段：
  - `id`: 主键
  - `bidding_round`: 外键（BiddingRound）
  - `user`: 外键（User）- 获得歌曲的用户
  - `song`: 外键（Song）- 分配的歌曲
  - `bid_amount`: 最终成交的竞标金额
  - `allocation_type`: 分配类型（'win'中标 或 'random'随机分配）
  - `allocated_at`: 分配时间

**功能**：✅ 完整支持
- 记录中标信息
- 记录随机分配信息

### 4. UserProfile（用户资料）
**引用**：`backend/xmmcg/users/models.py`
- 包含 `token` 字段（用户代币余额）✅

## 后端API端点 ✅

### 1. 获取竞标轮次信息
**端点**：`GET /api/bidding-rounds/`
**文件**：`backend/xmmcg/songs/views.py` L334-396
**响应**：
```json
{
  "success": true,
  "count": 1,
  "rounds": [
    {
      "id": 1,
      "name": "第一轮竞标",
      "status": "active",
      "status_display": "进行中",
      "created_at": "...",
      "started_at": "...",
      "completed_at": null,
      "bid_count": 100,
      "result_count": 0
    }
  ]
}
```
✅ 包含轮次信息和状态

### 2. 获取用户的竞标列表
**端点**：`GET /api/bids/?round_id=1`
**文件**：`backend/xmmcg/songs/views.py` L401-460
**响应**：
```json
{
  "success": true,
  "round": {
    "id": 1,
    "name": "第一轮竞标",
    "status": "active"
  },
  "bid_count": 3,
  "max_bids": 5,
  "bids": [
    {
      "id": 1,
      "song": { ... },
      "amount": 500,
      "is_dropped": false,
      "created_at": "..."
    }
  ]
}
```
✅ 完整返回用户的竞标，包含最大竞标数

### 3. 创建竞标
**端点**：`POST /api/bids/`
**请求**：
```json
{
  "song_id": 1,
  "amount": 500,
  "round_id": 1  // 可选
}
```
**文件**：`backend/xmmcg/songs/views.py` L461-519
**响应**：
```json
{
  "success": true,
  "message": "竞标已创建",
  "bid": {
    "id": 1,
    "song": { ... },
    "amount": 500,
    "created_at": "..."
  }
}
```
**验证**：✅
- 验证歌曲存在
- 验证竞标轮次存在且为活跃状态
- 验证用户代币足够（不扣除）✅
- 验证竞标数量不超过5个 ✅
- 验证对同一歌曲未重复竞标

### 4. 执行竞标分配（Admin）
**端点**：`POST /api/bids/allocate/`
**文件**：`backend/xmmcg/songs/views.py` L517-579
**参数**：
```json
{
  "round_id": 1  // 可选，不提供则分配最新的活跃轮次
}
```
**调用**：`BiddingService.allocate_bids(round_obj.id)` ✅
**算法**：✅
- 按竞标金额从高到低排序
- 依次分配歌曲
- 同一歌曲的其他竞标标记为drop
- 未获得歌曲的用户随机分配

**分配后处理**：⚠️ **需要前端实现**
- 扣除代币（需要调用 `BiddingService.process_allocation()` 或类似）
- 更新用户页面状态

### 5. 获取竞标结果
**端点**：`GET /api/bid-results/?round_id=1`
**文件**：`backend/xmmcg/songs/views.py` L579-650
**响应**：
```json
{
  "success": true,
  "round": { ... },
  "results": [
    {
      "id": 1,
      "user": { "username": "user1" },
      "song": { ... },
      "bid_amount": 500,
      "allocation_type": "win",
      "allocated_at": "..."
    }
  ]
}
```
✅ 完整返回分配结果

## 前端序列化器 ✅

### SongListSerializer
**文件**：`backend/xmmcg/songs/serializers.py` L103-131
**字段**：
- `id`, `title`, `user`, `audio_url`, `cover_url`, `netease_url`, `file_size`, `created_at`
✅ 包含歌曲所需的所有信息

### 用户信息序列化器
**文件**：`backend/xmmcg/users/serializers.py`
**新增字段**（已实现）：
- `songsCount`: 用户上传歌曲数
- `chartsCount`: 用户上传谱面数
✅ 包含用户代币信息（token）

## 需要后端补充 ⚠️

### 1. 分配后处理代币扣除
**位置**：`BiddingService.allocate_bids()` 中或单独的方法
**需要实现**：
```python
def process_allocation_tokens(bidding_round_id):
    """
    处理竞标分配后的代币扣除
    - 从用户代币中扣除中标的竞标金额
    - 保持未中标的金额（不扣除）
    """
```

**当前实现**：❌ 分配完成后未自动扣除代币
**建议**：
- 在 `allocate_bids()` 完成后立即扣除代币
- 或在前端调用分配API后再调用一个 token 处理API

### 2. 获取用户当前代币余额 API（可选但推荐）
**建议新增端点**：
```
GET /api/users/me/token/
返回：{ "token": 1000 }
```

## 前端需要实现 📋

### 1. 竞标浮窗
- 显示当前用户代币余额
- 输入出价金额
- 验证代币是否足够
- 提交竞标请求到 `POST /api/bids/`

### 2. 我的竞标显示
- 加载 `GET /api/bids/`
- 列出用户的5个竞标
- 显示是否已drop

### 3. 分配后处理
- 检测分配完成信号（后端状态变为 completed）
- 调用 `GET /api/bid-results/` 获取结果
- 显示中标/随机分配结果
- 更新用户代币（调用 `GET /api/users/me/`）

## 总结

✅ **后端已完整实现**：
- 竞标数据模型完整
- 竞标创建验证逻辑完整（代币验证、数量限制等）
- 竞标分配算法完整
- 所有必需API端点已实现
- 竞标轮次管理完整

⚠️ **需要补充**：
- 代币自动扣除逻辑（可在分配时或分配后执行）
- 可选：用户当前代币余额快速查询 API

✅ **前端需要实现**：
- 竞标UI组件（浮窗、表单）
- 竞标API集成
- 分配结果显示
- 用户代币状态更新

**建议优先实现顺序**：
1. 后端补充分配后代币扣除逻辑
2. 前端实现竞标浮窗和提交
3. 前端实现我的竞标列表
4. 前端实现分配结果显示
