# 谱面上传控件中标检测修复

## 问题分析

用户反馈：上传控件没有检测到中标状态，导致无法上传终稿。

### 问题原因

`handleUpload()` 函数存在以下缺陷：

1. **缺少中标检查**：没有验证用户是否真的中标了（`myBidResult.value` 是否存在）
2. **缺少类型提示**：上传时没有明确提示用户正在上传"半成品"还是"完成稿"
3. **缺少标题提示**：没有显示当前上传的谱面标题，容易混淆不同的谱面

### 数据结构

- `myBidResult.value` 是一个中标结果对象，包含：
  - `bid_type`：'song'（歌曲竞标-上传半成品）或 'chart'（谱面竞标-上传完成稿）
  - `song.title`：歌曲标题
  - `id`：竞标结果 ID（用于提交）

### 后端已有正确逻辑

[songs/views.py#L1036-L1050](backend/xmmcg/songs/views.py#L1036-L1050) 的 `submit_chart()` 已经根据 `bid_result.bid_type` 自动判断状态：
```python
if bid_result.bid_type == 'song':
    target_status = 'part_submitted'   # 半成品
    status_msg = '半成品'
elif bid_result.bid_type == 'chart':
    target_status = 'final_submitted'  # 完成稿
    status_msg = '完成稿'
```

## 修复方案

修改 [front/src/views/Charts.vue](front/src/views/Charts.vue) 的 `handleUpload()` 函数（第704行）：

### 改进 1：中标检查
```javascript
if (!myBidResult.value) {
  ElMessage.error('还没有中标，无法上传谱面')
  return
}
```

### 改进 2：上传类型判断
```javascript
const isSecondStageUpload = myBidResult.value.bid_type === 'chart'
const uploadType = isSecondStageUpload ? '完成稿' : '半成品'
const songTitle = myBidResult.value.song?.title || '未知歌曲'
```

### 改进 3：上传确认对话框
使用 `ElMessageBox.confirm()` 在上传前显示：
- ✅ **谱面标题**：显示当前要上传的谱面所属的歌曲名称
- ✅ **上传类型**：显示是"半成品"还是"完成稿"（用不同颜色区分）
- ✅ **谱师名义**：显示从 maidata.txt 解析出的谱师名
- ✅ **阶段提示**：
  - 半成品：提示用户"可以继续编辑并在第二阶段提交完成稿"
  - 完成稿：⚠️ 警告用户"此后该谱面将进入互评阶段"

示例对话框：
```
┌─────────────────────────────────┐
│ 确认上传谱面                      │
├─────────────────────────────────┤
│ 谱面标题：Lost Song              │
│ 上传类型：完成稿 (黄色)            │
│ 谱师名义：Designer Name           │
│                                 │
│ ⚠️ 您正在提交该谱面的完成稿，     │
│ 此后该谱面将进入互评阶段。         │
├─────────────────────────────────┤
│  [取消]  [确认上传]              │
└─────────────────────────────────┘
```

### 改进 4：成功提示
上传成功时显示：`✓ 成功上传完成稿谱面：Lost Song`

## 实现细节

**文件修改**：[front/src/views/Charts.vue](front/src/views/Charts.vue#L704-L780)

**关键改进**：
1. 添加 `myBidResult.value` 的存在检查
2. 使用 `ElMessageBox.confirm()` 替代直接提交
3. 确认对话框中显示谱面标题、上传类型、谱师名义
4. 根据 `bid_type` 动态显示阶段提示信息
5. 使用 HTML 格式化对话框内容，支持颜色和样式

## 相关已有代码

页面中已有的计算属性也反映了这个逻辑：

```javascript
// uploadCardTitle 已正确显示类型
const uploadCardTitle = computed(() => {
  if (!myBidResult.value) return '上传谱面'
  return isSecondStage.value ? '上传谱面（完成稿）' : '上传谱面（半成品）'
})

// stageDescription 已显示阶段说明
const stageDescription = computed(() => {
  if (!myBidResult.value) return ''
  if (isSecondStage.value) {
    return '📝 第二阶段：您中标了谱面竞标，请继续完成该谱面并提交完成稿'
  }
  return '📝 第一阶段：您中标了歌曲竞标，请制作半成品谱面并上传'
})
```

现在上传确认对话框也会显示这些信息，确保用户清楚他们在上传什么以及上传的是哪个版本。

## 验证步骤

1. 中标一个歌曲竞标
2. 准备好音频、封面、谱面文件
3. 点击"上传谱面"按钮
4. 确认对话框应显示：
   - 正确的歌曲标题
   - "半成品"（蓝色）
   - 正确的谱师名义
5. 点击"确认上传"完成上传
6. 看到成功提示："✓ 成功上传半成品谱面：歌曲标题"

## 后续测试

若要测试"完成稿"上传：
1. 中标一个**谱面竞标**
2. 准备修改并提交最终版本
3. 对话框应显示"完成稿"（黄色）和警告信息
4. 上传后应显示："✓ 成功上传完成稿谱面：歌曲标题"
