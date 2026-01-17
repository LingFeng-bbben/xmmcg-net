# 竞标功能实现进度

## 已完成的任务 ✅

### 1. 后端代币扣除逻辑 ✅
**文件**：`backend/xmmcg/songs/bidding_service.py`

**新增方法**：`process_allocation_tokens(bidding_round_id)`
- 在竞标分配完成后自动调用
- 为所有中标用户（allocation_type='win'）从其代币中扣除竞标金额
- 随机分配的用户（bid_amount=0）不扣除代币
- 返回扣除统计信息，包括失败用户列表

**修改方法**：`allocate_bids(bidding_round_id)`
- 在竞标分配完成后立即调用 `process_allocation_tokens()`
- 返回结果中新增 `token_deduction` 字段，包含扣除统计

**处理流程**：
```
1. 获取分配结果（中标的）
2. 逐个处理用户：
   - 验证代币足够
   - 扣除对应金额
   - 记录失败的用户
3. 返回统计信息
```

### 2. 前端 API 方法 ✅
**文件**：`front/src/api/index.js`

**新增方法**：
- `getBidResults(roundId)` - 获取竞标分配结果

**已有方法**：
- `getBiddingRounds()` - 获取竞标轮次
- `getMyBids(roundId)` - 获取用户的竞标
- `submitBid(songId, amount, roundId)` - 提交竞标

### 3. 前端竞标UI ✅
**文件**：`front/src/views/Songs.vue`

**状态数据**：
```javascript
// 竞标对话框
bidDialogVisible          // 对话框显示状态
bidForm                   // 竞标表单（songId, songTitle, amount）
bidSubmitting             // 提交中状态
userToken                 // 用户代币余额
currentRound              // 当前竞标轮次
myBidsCount               // 用户已有的竞标数
maxBids                   // 最大竞标数（5）
```

**新增方法**：
- `showBidDialog(song)` - 打开竞标对话框
  - 加载当前竞标轮次
  - 获取用户已有竞标数
  - 获取用户代币余额
  
- `handleSubmitBid()` - 提交竞标
  - 验证竞标金额有效
  - 验证未超过竞标数量限制
  - 验证代币足够
  - 调用 API 提交竞标
  - 刷新竞标列表

**竞标对话框界面**：
- 显示歌曲标题
- 显示竞标轮次名称
- 显示用户代币余额（标签）
- 显示已竞标/最大竞标数
- 输入框：竞标金额（数字输入，范围 1-userToken）
- 警告提示：
  - 代币不足时显示
  - 超过竞标限制时显示
- 按钮：提交竞标（满足条件时启用）

### 4. 竞标按钮启用 ✅
**文件**：`front/src/views/Songs.vue`

**修改**：
- 移除 `disabled` 属性
- 点击时调用 `showBidDialog(song)`
- 改为 "竞标"（去掉"即将开放"）

## 使用流程

### 用户端流程：
1. 打开歌曲页面
2. 展开歌曲卡片详情
3. 点击"竞标"按钮
4. 竞标对话框打开，显示：
   - 当前代币余额
   - 已竞标数量和上限
   - 输入框用于输入出价
5. 输入出价金额（必须≤代币余额，且未超过5个竞标）
6. 点击"提交竞标"
7. 竞标成功后刷新列表

### 管理员端流程（分配）：
1. 所有竞标结束后，管理员执行分配
2. 调用 `POST /api/bids/allocate/`
3. 后端执行分配算法：
   - 按出价从高到低排序
   - 分配歌曲给最高出价者
   - 标记低出价者为drop
   - 为未中标用户随机分配
   - **自动扣除代币**
4. 返回分配统计

### 用户查看结果：
1. 用户可以调用 `GET /api/bid-results/?round_id=X` 查看分配结果
2. 显示中标的歌曲和扣除的代币
3. 用户代币余额已更新

## 需要测试的场景

- [ ] 代币足够时，竞标正常提交
- [ ] 代币不足时，不允许提交
- [ ] 已有5个竞标时，不允许继续竞标
- [ ] 分配完成后，代币正确扣除
- [ ] 未中标用户的代币不扣除
- [ ] 随机分配用户的代币不扣除
- [ ] 分配失败的用户被记录

## API 响应示例

### 提交竞标成功
```json
{
  "success": true,
  "message": "竞标已创建",
  "bid": {
    "id": 1,
    "song": { "id": 1, "title": "..." },
    "amount": 500,
    "created_at": "..."
  }
}
```

### 分配完成响应
```json
{
  "success": true,
  "message": "竞标分配完成",
  "statistics": {
    "total_deducted": 15000,
    "users_deducted": 10,
    "failed_users": [],
    "failed_count": 0
  }
}
```

### 获取分配结果
```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "user": { "username": "user1" },
      "song": { "id": 1, "title": "..." },
      "bid_amount": 500,
      "allocation_type": "win",
      "allocated_at": "..."
    }
  ]
}
```

## 后续优化建议

1. **实时通知**：竞标分配完成时，向用户发送通知
2. **竞标历史**：记录用户的竞标历史和结果
3. **代币回退**：支持用户修改竞标金额（如果允许）
4. **排名显示**：在我的竞标列表中显示当前排名
5. **倒计时**：显示竞标剩余时间

## 文件修改清单

1. ✅ `backend/xmmcg/songs/bidding_service.py`
   - 添加 `process_allocation_tokens()` 方法
   - 修改 `allocate_bids()` 调用代币处理

2. ✅ `front/src/api/index.js`
   - 添加 `getBidResults()` 方法

3. ✅ `front/src/views/Songs.vue`
   - 导入 `submitBid`, `getBiddingRounds` API
   - 添加竞标相关状态数据
   - 添加 `showBidDialog()` 方法
   - 添加 `handleSubmitBid()` 方法
   - 启用竞标按钮
   - 添加竞标对话框UI

## 已知问题 / 待处理

- 竞标对话框关闭时，是否清空表单数据（可选）
- 首次加载时是否预加载竞标轮次信息（性能考虑）
- 多轮竞标切换时的状态管理（需确认需求）
