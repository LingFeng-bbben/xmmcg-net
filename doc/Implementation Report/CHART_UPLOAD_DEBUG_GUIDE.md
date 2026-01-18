# 谱面上传调试指南

## 详细日志已添加

已在 Charts.vue 中的以下函数添加了详细的 console 日志：

1. **handleUpload()** - 上传谱面的主函数
2. **loadMyBidResult()** - 加载中标结果的函数

## 如何查看调试日志

### 第一步：打开浏览器开发者工具

- **Windows/Linux**: `F12` 或 `Ctrl+Shift+I`
- **macOS**: `Cmd+Option+I`

### 第二步：打开 Console 标签

在开发者工具中找到 **Console** 标签，确保所有日志都可见。

## 预期的日志输出流程

### 页面加载时

```
getBidResults 响应: {success: true, results: [...]}
所有中标结果: [{id: ..., bid_type: 'chart', song: {...}, ...}]
✓ 找到中标结果: {id: ..., bid_type: 'chart', ...}
getMyCharts 响应: {success: true, charts: [...]}
匹配的谱面: {id: 72, song: {id: 205, title: 'Fire Bird'}, ...}
```

### 点击上传按钮时

```
=== handleUpload 开始 ===
myBidResult.value: {id: ..., bid_type: 'chart', song: {title: 'Fire Bird'}, ...}
uploading.value: false
✓ 已中标，继续...
✓ uploadFormRef 存在，开始验证表单...
表单验证结果: true
✓ 表单验证通过
detectedDesigner.value: Designer Name
✓ 谱师名义已检测
上传信息: {
  isSecondStageUpload: true,
  uploadType: "完成稿",
  songTitle: "Fire Bird",
  bid_type: "chart",
  bidResultId: ...
}
显示上传确认对话框...
```

### 点击"确认上传"后

```
✓ 用户点击了"确认上传"
附加文件到 FormData:
  ✓ audio_file: filename.mp3
  ✓ cover_image: filename.jpg
  - background_video: 可选，未提供
  ✓ chart_file: maidata.txt
调用 submitChart API，resultId: ...
API 响应: {success: true, message: '...'}
✓ 上传成功
=== handleUpload 结束 ===
```

## 常见问题调试

### 问题 1: "还没有中标，无法上传谱面"

**检查项**：
```
myBidResult.value: null
```

这表示页面未能加载中标结果。查看上面的日志，看 `getBidResults 响应` 是什么。可能原因：
- API 返回失败
- 用户没有中标任何谱面

### 问题 2: 表单验证失败

**检查项**：
```
表单验证结果: false
```

可能原因：
- 音频文件未选择
- 封面图片未选择
- 谱面文件未选择
- 谱师名义未检测到

### 问题 3: 上传按钮被禁用

**检查项**：
- 表单中的 `:disabled` 属性是否为 true
- 可能原因：`uploading` 或 `myChart` 或 `!isChartingPhase` 中的某个为 true

查看页面源码（第46行）：
```vue
:disabled="uploading || !!myChart || !isChartingPhase"
```

## 主要修复点

### 修复 1: loadMyBidResult() 函数
**问题**：原来只查找 `bid_type === 'song'` 的结果
**解决**：改为优先查 song，其次查 chart

旧代码：
```javascript
myBidResult.value = res.results.find(r => r.bid_type === 'song')
```

新代码：
```javascript
let bidResult = res.results.find(r => r.bid_type === 'song')
if (!bidResult) {
  bidResult = res.results.find(r => r.bid_type === 'chart')
}
myBidResult.value = bidResult
```

这确保了即使是谱面竞标获胜的用户也能看到上传表单。

### 修复 2: handleUpload() 函数
添加了详细的 console 日志来追踪上传流程的每一步。

## 数据结构参考

### getBidResults 返回的数据

```javascript
{
  success: true,
  results: [
    {
      id: 123,
      bid_type: 'song' | 'chart',
      song: {
        id: 205,
        title: 'Fire Bird',
        ...
      },
      chart: null | {...},  // 仅当 bid_type='chart' 时有值
      username: 'user123',
      bid_amount: 31,
      allocation_type: 'win',
      ...
    }
  ]
}
```

## 建议的排查步骤

1. 刷新页面，打开 Console
2. 查看是否有错误（红色）
3. 查看 `getBidResults 响应` 的内容
4. 确认 `✓ 找到中标结果` 出现
5. 尝试点击上传按钮
6. 查看 `=== handleUpload 开始 ===` 之后的日志
7. 按照"常见问题调试"中对应的检查项进行排查

## 导出日志

如果问题难以排查，可以在 Console 中右键点击日志，选择 "Save all messages as..." 来导出日志，然后分享给开发者。

或使用以下命令复制所有输出：
```javascript
// 在 Console 中粘贴这个命令
copy(
  Array.from(document.querySelectorAll('.console-message'))
    .map(el => el.textContent)
    .join('\n')
)
```
