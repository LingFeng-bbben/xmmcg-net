# 谱面竞标分配结果显示问题修复

## 问题诊断

通过查询数据库发现：

```
===== 所有谱面竞标轮次 =====
轮次ID: 42, 类型: chart, 状态: completed, Bid数: 1, Result数: 1
轮次ID: 38, 类型: chart, 状态: completed, Bid数: 25, Result数: 7

===== 最新轮次的详细信息 =====
轮次ID: 42, 状态: completed
所有Bid:
  Bid ID: 588, 用户: sniperpigeon, Chart: 72, 结果: win
```

**根本原因**：前端代码只查找 `status === 'active'` 的轮次，而管理员分配后轮次状态变为 `completed`，导致已完成的轮次及其分配结果无法显示。

## 代码问题分析

### Charts.vue - loadMyChartBids() 

**原有逻辑**：
```javascript
// 找活跃的谱面竞标轮次
const activeChartRound = roundsResponse.rounds.find(r => r.status === 'active' && r.bidding_type === 'chart')
if (!activeChartRound) {
  console.log('当前没有活跃的谱面竞标轮次')
  currentChartBidRound.value = null
  myChartBids.value = []
  return  // ❌ 直接返回，无法显示已完成轮次的结果
}
```

**问题**：当管理员执行 `allocate_bids()` 后，轮次状态变为 'completed'，上述代码找不到该轮次就直接返回，导致分配结果无法显示。

### Songs.vue - loadMyBids()

同样问题。

## 修复方案

### Charts.vue - loadMyChartBids()

**新增逻辑**：
```javascript
// 找最新的谱面竞标轮次（优先活跃，其次已完成以显示分配结果）
let targetChartRound = roundsResponse.rounds.find(r => r.status === 'active' && r.bidding_type === 'chart')
if (!targetChartRound) {
  // 没有活跃的，则查找最新的已完成轮次（用于显示分配结果）
  const completedChartRounds = roundsResponse.rounds.filter(r => r.status === 'completed' && r.bidding_type === 'chart')
  if (completedChartRounds.length > 0) {
    targetChartRound = completedChartRounds[0]  // 已排序，第一个是最新的
  }
}

if (!targetChartRound) {
  console.log('当前没有活跃或已完成的谱面竞标轮次')
  currentChartBidRound.value = null
  myChartBids.value = []
  return
}
```

**改进点**：
1. 优先查找活跃轮次（用于正在进行的竞标）
2. 如果没有活跃轮次，则查找最新的已完成轮次（用于显示分配结果）
3. 由于 `getBiddingRounds()` 返回的轮次已按创建时间倒序排列，第一个已完成轮次就是最新的

### Songs.vue - loadMyBids()

应用相同逻辑。

## 显示效果

修复后，用户将看到：

### 表格列配置已支持：
1. **竞标金额**：显示用户竞标的金额
2. **状态标签**：
   - 🔵 进行中 (bidding) - 蓝色标签
   - ✅ 已中选 (won) - 绿色标签
   - ❌ 已落选 (lost) - 灰色标签
3. **操作按钮**：
   - 已中选状态：显示 "下载" 按钮 → 下载获得的谱面资源
   - 进行中状态：显示 "撤回" 按钮 → 取消竞标

## 测试验证步骤

1. 打开 **我的谱面竞标** 标签页
2. 浏览器控制台应显示：
   ```
   当前没有活跃的谱面竞标轮次
   加载谱面竞标成功，总数: 1
   竞标 1: {
     id: 588,
     chart_id: 72,
     song_title: "Song Title",
     amount: 150,
     status: "won",
     bid_type: "chart"
   }
   ```
3. 表格中应显示该竞标，并在状态列显示 ✅ 已中选
4. 点击 "下载" 按钮应能下载获得的谱面资源

## 数据库轮次查询验证

若要手动验证数据库状态：
```bash
cd backend\xmmcg
.venv\Scripts\activate
python debug_bidding_rounds.py
```

输出应显示：
- 所有谱面竞标轮次及其状态
- 最新轮次的详细 Bid 和 BidResult 数据

## 相关文件修改

- `front/src/views/Charts.vue` - loadMyChartBids() 函数（第856行起）
- `front/src/views/Songs.vue` - loadMyBids() 函数（第882行起）

## 后续改进方向

1. **自动刷新**：在完成竞标分配后，自动刷新竞标列表（WebSocket 或轮询）
2. **UI 提示**：当进入已完成轮次的查看模式时，显示 "本轮次已结束，显示分配结果" 提示
3. **多轮次历史**：允许用户切换查看历历史轮次的竞标记录
