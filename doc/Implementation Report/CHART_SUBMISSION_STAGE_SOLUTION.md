# 谱面提交阶段区分方案

## 问题描述

系统有两阶段竞标流程：
1. **第一阶段**：歌曲竞标 → 中标后制作半成品（part_submitted）
2. **第二阶段**：谱面竞标 → 中标后完成完成稿（final_submitted）

当前问题：`submit_chart()` 视图硬编码 `status='part_submitted'`，无法区分两个阶段的提交。

## 推荐方案：基于 BidResult.bid_type 自动判断

### 优势
- ✅ **无需手动选择**：系统根据竞标类型自动设置状态
- ✅ **逻辑清晰**：bid_type='song' → 半成品，bid_type='chart' → 完成稿
- ✅ **数据一致性**：利用现有字段，无需新增复杂逻辑
- ✅ **防止错误**：用户无法选错状态

### 实现方式

#### 后端修改（songs/views.py）

**当前代码**（第 1016 行附近）：
```python
chart.status = 'part_submitted'  # 硬编码
```

**改进后**：
```python
# 根据竞标类型自动设置状态
if bid_result.bid_type == 'song':
    # 第一阶段：歌曲竞标中标，提交半成品
    chart.status = 'part_submitted'
elif bid_result.bid_type == 'chart':
    # 第二阶段：谱面竞标中标，提交完成稿
    chart.status = 'final_submitted'
else:
    # 默认为半成品（兼容性）
    chart.status = 'part_submitted'
```

#### 完整修改

需要修改两处（创建和更新）：

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_chart(request, result_id):
    """提交谱面"""
    from .models import BidResult, Chart
    from .serializers import ChartCreateSerializer, ChartSerializer
    
    user = request.user
    bid_result = get_object_or_404(BidResult, id=result_id, user=user)
    
    # 检查是否已有谱面
    chart = Chart.objects.filter(
        user=user,
        song=bid_result.song,
        bidding_round=bid_result.bidding_round
    ).first()
    
    serializer = ChartCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    validated = serializer.validated_data
    new_file = validated.get('chart_file')
    designer = validated.get('designer')
    new_audio = validated.get('audio_file')
    new_cover = validated.get('cover_image')
    
    # 🔥 关键改动：根据竞标类型自动设置状态
    if bid_result.bid_type == 'song':
        target_status = 'part_submitted'
    elif bid_result.bid_type == 'chart':
        target_status = 'final_submitted'
    else:
        target_status = 'part_submitted'  # 默认
    
    if chart:
        # 更新现有谱面
        if new_file:
            if chart.chart_file:
                chart.chart_file.delete(save=False)
            chart.chart_file = new_file
        if new_audio:
            if chart.audio_file:
                chart.audio_file.delete(save=False)
            chart.audio_file = new_audio
        if new_cover:
            if chart.cover_image:
                chart.cover_image.delete(save=False)
            chart.cover_image = new_cover
        chart.designer = designer
        chart.status = target_status  # 🔥 使用自动判断的状态
        chart.submitted_at = timezone.now()
        chart.save()
    else:
        # 创建新谱面
        chart = Chart.objects.create(
            bidding_round=bid_result.bidding_round,
            user=user,
            song=bid_result.song,
            bid_result=bid_result,
            status=target_status,  # 🔥 使用自动判断的状态
            designer=designer,
            audio_file=new_audio,
            cover_image=new_cover,
            chart_file=new_file,
            submitted_at=timezone.now()
        )
    
    result_serializer = ChartSerializer(chart, context={'request': request})
    return Response({
        'success': True,
        'message': f'谱面提交成功（{"半成品" if target_status == "part_submitted" else "完成稿"}）',
        'chart': result_serializer.data
    }, status=status.HTTP_201_CREATED)
```

#### 前端调整（可选：显示提示）

在 Charts.vue 的上传成功后，可以根据状态显示不同提示：

```javascript
const handleUpload = async () => {
  // ... 现有代码 ...
  
  try {
    const res = await submitChart(myBidResult.value.id, formData)
    if (res.success) {
      // 显示具体提交的是半成品还是完成稿
      ElMessage.success(res.message || '谱面上传成功')
      resetUploadForm()
      await loadMyBidResult()
      await loadCharts()
    }
  } catch (error) {
    // ... 错误处理 ...
  }
}
```

### 流程示例

#### 场景1：第一阶段（歌曲竞标）
1. 用户竞标歌曲 → BidResult.bid_type='song'
2. 中标后上传谱面 → 自动设置 status='part_submitted'
3. 谱面显示"半成品"标签（黄色）

#### 场景2：第二阶段（谱面竞标）
1. 用户竞标他人半成品谱面 → BidResult.bid_type='chart'
2. 中标后继续完成 → 自动设置 status='final_submitted'
3. 谱面显示"完成稿"标签（绿色）

### 验证逻辑

可以在后端添加额外验证：

```python
# 在 submit_chart 开头添加验证
if bid_result.bid_type == 'chart':
    # 谱面竞标必须基于已有半成品
    if not bid_result.chart or bid_result.chart.status != 'part_submitted':
        return Response({
            'success': False,
            'message': '谱面竞标必须基于已存在的半成品谱面'
        }, status=status.HTTP_400_BAD_REQUEST)
```

## 替代方案（不推荐）

### 方案2：基于 CompetitionPhase 阶段判断

```python
# 获取当前阶段
current_phase = CompetitionPhase.objects.filter(
    is_active=True,
    start_time__lte=timezone.now(),
    end_time__gte=timezone.now()
).first()

if current_phase and 'chart_bidding' in current_phase.phase_key:
    target_status = 'final_submitted'
else:
    target_status = 'part_submitted'
```

**缺点**：
- ❌ 依赖阶段时间，如果用户延迟提交会出错
- ❌ 需要精确配置阶段 phase_key
- ❌ 无法处理跨阶段提交

### 方案3：用户手动选择

在前端添加选择框：
```vue
<el-radio-group v-model="submitType">
  <el-radio label="part">半成品</el-radio>
  <el-radio label="final">完成稿</el-radio>
</el-radio-group>
```

**缺点**：
- ❌ 用户可能选错
- ❌ 增加操作复杂度
- ❌ 容易造成数据混乱（例如歌曲竞标中标却提交完成稿）

### 方案4：基于是否已有谱面

```python
existing_chart = Chart.objects.filter(user=user, song=bid_result.song).first()
target_status = 'final_submitted' if existing_chart else 'part_submitted'
```

**缺点**：
- ❌ 第一次提交就是完成稿时无法区分
- ❌ 多次更新半成品会被误判为完成稿
- ❌ 逻辑不够清晰

## 总结

**推荐使用方案1**（基于 BidResult.bid_type）：
- 简单直接，利用现有数据结构
- 逻辑清晰，与竞标流程一致
- 无需额外配置或用户操作
- 自动防止状态混乱

### 实施步骤

1. ✅ 修改 `backend/xmmcg/songs/views.py` 的 `submit_chart()` 函数
2. ✅ 测试两种竞标流程：
   - 歌曲竞标 → 上传 → 验证状态为 part_submitted
   - 谱面竞标 → 上传 → 验证状态为 final_submitted
3. ✅ （可选）前端显示不同提示消息
4. ✅ 更新文档说明自动判断逻辑

### 相关代码位置

- **模型定义**：`backend/xmmcg/songs/models.py` - BidResult（第484行）
- **提交视图**：`backend/xmmcg/songs/views.py` - submit_chart（第960行）
- **前端上传**：`front/src/views/Charts.vue` - handleUpload（第 370 行左右）
