# 谱面竞标前端 UI 实现完成

## 更新时间
2024年

## 概述
已为 Charts.vue 添加完整的谱面竞标功能，实现了四项关键需求：

1. ✅ **制谱期阶段控制** - 上传功能仅在制谱期开放
2. ✅ **我的谱面竞标组件** - 显示已提交的谱面竞标和状态
3. ✅ **谱面卡片竞标按钮** - 完整的竞标浮窗和提交流程
4. ✅ **状态筛选功能** - 按谱面状态筛选列表

## 详细改动

### 1. 阶段控制和上传禁用

**实现**：
- 新增 `checkChartingPhase()` 函数调用 `getCurrentPhase()` API
- 新增 `isChartingPhase` ref 来控制上传表单的 `disabled` 状态
- 新增阶段警告提示（`el-alert`），显示当前阶段名称

**代码位置**：
- 模板：第 17-27 行（阶段警告）
- 脚本：第 439-450 行（`checkChartingPhase` 函数）
- 表单：第 35 行（`:disabled="uploading || !!myChart || !isChartingPhase"`）

**逻辑**：
```javascript
isChartingPhase.value = phase.page_access?.charts === true || 
                        phase.phase_key?.includes('mapping') ||
                        phase.phase_key?.includes('chart')
```

### 2. "我的谱面竞标"组件

**实现**：
- 新增独立卡片显示谱面竞标信息
- 显示当前轮次名称、已竞标数量（已竞标/最大数）
- 表格展示：歌曲标题、竞标金额、状态、竞标时间、操作（下载）
- 状态标签颜色：
  - 进行中：蓝色（info）
  - ✓ 已中选：绿色（success）
  - 已落选：红色（danger）

**代码位置**：
- 模板：第 122-188 行
- 脚本：第 521-535 行（`loadMyChartBids` 函数）

**数据过滤**：
```javascript
myChartBids.value = res.bids?.filter(b => b.bidding_type === 'chart') || []
```

### 3. 谱面卡片竞标功能

**竞标按钮**：
- 在每个谱面卡片下方添加"竞标"按钮（绿色，成功类型）
- 点击打开竞标对话框

**竞标对话框**：
- 显示谱面信息：歌曲标题、谱师名义、竞标轮次
- 显示用户状态：代币余额、已竞标数量
- 金额输入：支持输入数字，自动校验范围（1 到用户余额）
- 错误提示：
  - 代币不足 → 红色警告
  - 达到竞标限制 → 黄色警告
- 提交按钮：disabled 状态自动根据条件控制

**代码位置**：
- 按钮：第 235-241 行
- 对话框：第 280-360 行
- 显示函数：第 584-616 行（`showChartBidDialog`）
- 提交函数：第 618-641 行（`handleSubmitChartBid`）

**API 调用**：
```javascript
const response = await submitBid({
  chartId: chartBidForm.chartId,
  amount: chartBidForm.amount,
  roundId: currentChartBidRound.value.id
})
```

### 4. 状态筛选

**实现**：
- 在谱面列表头部添加下拉选择器
- 筛选选项：
  - 半成品（`part_submitted`）
  - 完成稿（`final_submitted`）
  - 已审核（`reviewed`）
- 支持清除筛选（clearable）

**代码位置**：
- 模板：第 197-206 行（筛选器）
- 计算属性：第 337-343 行（`filteredCharts`）
- 数据绑定：第 218 行（`v-for="chart in filteredCharts"`）

**筛选逻辑**：
```javascript
const filteredCharts = computed(() => {
  if (!selectedStatusFilter.value) {
    return charts.value
  }
  return charts.value.filter(chart => chart.status === selectedStatusFilter.value)
})
```

## 新增 API 引用

从 `@/api/index.js` 引入：
- `getCurrentPhase` - 获取当前比赛阶段
- `getMyBids` - 获取用户竞标列表
- `getBiddingRounds` - 获取竞标轮次
- `submitBid` - 提交竞标
- `getUserProfile` - 获取用户信息（代币余额）

## 新增图标

从 `@element-plus/icons-vue` 引入：
- `TrophyBase` - 奖杯图标（竞标按钮）

## 数据结构

### 谱面竞标表单（chartBidForm）
```javascript
{
  chartId: number,        // 谱面 ID
  chartTitle: string,     // 歌曲标题
  designer: string,       // 谱师名义
  amount: number | null   // 竞标金额
}
```

### 状态映射（Bid Status）
```javascript
{
  'bidding': '进行中',    // 竞标进行中
  'won': '✓ 已中选',      // 中标
  'lost': '已落选'         // 未中标
}
```

### 状态标签类型
```javascript
{
  'bidding': 'info',      // 蓝色
  'won': 'success',       // 绿色
  'lost': 'danger'        // 红色
}
```

## 样式调整

1. **卡片间距**：新增 `.my-bids-card` 样式，margin-bottom: 20px
2. **竞标信息**：新增 `.round-info` 样式，margin-bottom: 20px
3. **按钮布局**：`.chart-actions` 改为 `flex-direction: column`，让两个按钮垂直排列

## 用户体验改进

1. **加载状态**：所有异步操作都有 loading 提示
2. **错误处理**：API 失败时显示 ElMessage.error
3. **成功反馈**：竞标提交成功后显示提示并刷新列表
4. **空状态提示**：
   - 没有中标结果 → 显示"前往竞标"按钮
   - 没有谱面竞标轮次 → 显示提示信息
   - 没有竞标记录 → 显示"去浏览谱面"按钮
5. **按钮禁用**：根据阶段、代币余额、竞标数量自动禁用

## 测试要点

### 1. 阶段控制
- [ ] 在非制谱期，上传表单应该被禁用
- [ ] 阶段警告显示当前阶段名称
- [ ] 制谱期内上传表单正常工作

### 2. 竞标流程
- [ ] 点击竞标按钮显示对话框
- [ ] 对话框显示正确的谱面信息和用户状态
- [ ] 代币不足时显示错误提示
- [ ] 达到竞标限制时显示警告
- [ ] 提交成功后刷新"我的谱面竞标"列表

### 3. 状态筛选
- [ ] 选择筛选器后只显示对应状态的谱面
- [ ] 清除筛选后显示所有谱面
- [ ] 筛选结果实时更新

### 4. 竞标结果显示
- [ ] "我的谱面竞标"表格正确显示竞标记录
- [ ] 中标状态显示绿色"✓ 已中选"
- [ ] 中标记录显示"下载"按钮
- [ ] 未中标记录显示 "-"

## 与 Songs.vue 的一致性

已完全参考 Songs.vue 的实现模式：
- ✅ 竞标对话框结构一致
- ✅ 状态标签颜色和文本一致
- ✅ 表格列布局相似
- ✅ 按钮图标和样式一致
- ✅ 错误提示逻辑一致
- ✅ API 调用模式一致

## 后续可能的优化

1. **分页支持**："我的谱面竞标"表格如果记录过多可添加分页
2. **排序功能**：竞标列表支持按时间、金额排序
3. **多条件筛选**：谱面列表支持按设计师、歌曲标题等多维度筛选
4. **竞标历史**：显示所有轮次的竞标历史而非仅当前轮次

## 相关文件

- `front/src/views/Charts.vue` - 主文件（已更新）
- `front/src/api/index.js` - API 模块（已存在，无需修改）
- `front/src/views/Songs.vue` - 参考实现
