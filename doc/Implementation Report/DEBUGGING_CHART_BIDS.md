# 谱面竞标调试指南

## 问题
用户提交了谱面竞标，但在"我的谱面竞标"列表中看不到。

## 根本原因（已修复）
`loadMyChartBids()`在调用`getMyBids()`时，没有传递谱面竞标轮次的ID。导致后端返回的是**当前活跃轮次**（可能是歌曲竞标轮次），而不是谱面竞标轮次。

## 修复内容

### 1. Charts.vue - loadMyChartBids()
- 修复前：直接调用 `getMyBids()` 返回当前活跃轮次
- 修复后：
  1. 先调用 `getBiddingRounds()` 获取所有竞标轮次
  2. 查找 `status === 'active' && bidding_type === 'chart'` 的轮次
  3. 用该轮次ID调用 `getMyBids(activeChartRound.id)`
  4. 过滤出 `bid_type === 'chart'` 的竞标

### 2. Songs.vue - loadMyBids()
- 同样修复：明确指定获取歌曲竞标轮次（`bidding_type === 'song'`）

### 3. serializers.py - BidSerializer.get_chart()
- 返回完整的song对象：`{'id': ..., 'title': ...}`
- 而不是只返回`song_title`字符串

## 调试步骤

### 在浏览器控制台中验证

1. **打开浏览器开发者工具** (F12)
2. **切换到Console标签**
3. **执行以下测试：**

```javascript
// 1. 检查是否有竞标轮次数据
await api.getBiddingRounds().then(r => console.log('竞标轮次:', r))

// 2. 查看是否有活跃的谱面竞标轮次
const rounds = await api.getBiddingRounds()
const chartRound = rounds.rounds?.find(r => r.status === 'active' && r.bidding_type === 'chart')
console.log('活跃谱面竞标轮次:', chartRound)

// 3. 获取该轮次的竞标
if (chartRound) {
  const bids = await api.getMyBids(chartRound.id)
  console.log('我的竞标:', bids)
  console.log('谱面竞标:', bids.bids?.filter(b => b.bid_type === 'chart'))
}

// 4. 查看单条竞标的数据结构
const bid = bids.bids?.[0]
console.log('竞标详情:', bid)
console.log('chart对象:', bid?.chart)
console.log('song标题:', bid?.chart?.song?.title)
```

## 测试流程

1. **重启后端**以应用serializer修改
2. **重新加载前端页面**
3. **提交一个谱面竞标**
4. **打开浏览器控制台检查：**
   - `console.log` 中是否有"加载谱面竞标成功"的消息
   - 返回的数据结构是否包含正确的chart.song.title

## 预期结果

控制台应该输出类似内容：
```
加载谱面竞标成功: [{
  id: 1,
  bid_type: 'chart',
  status: 'bidding',
  amount: 100,
  chart: {
    id: 5,
    song: {
      id: 2,
      title: '歌曲标题'
    }
  },
  created_at: '2026-01-18T10:00:00Z'
}]
```

## 常见问题排查

| 问题 | 解决方案 |
|------|--------|
| 控制台没有"加载谱面竞标成功"消息 | 检查是否有活跃的谱面竞标轮次 |
| chart对象中没有song字段 | 确认后端已重启，serializer修改已生效 |
| 列表还是显示"您还没有竞标任何谱面" | 检查filter逻辑是否正确：`b.bid_type === 'chart'` |
| bid_type显示为其他值 | 打印原始API响应检查字段名 |

## 关键日志位置

**Charts.vue:**
- Line 879: `console.log('加载谱面竞标成功:', myChartBids.value)`

**Songs.vue:**
- Line 899: `console.log('加载歌曲竞标成功:', myBids.value)`

在这些位置的日志会告诉你数据加载是否成功。
