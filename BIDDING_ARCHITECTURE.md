# 竞标系统架构说明

## 📋 当前架构

### 1. 两层模型设计

#### 层级关系
```
CompetitionPhase (比赛阶段 - 顶层)
    ↓
BiddingRound / SecondBiddingRound (具体竞标轮次 - 执行层)
    ↓
Bid / SecondBid (用户竞标记录)
    ↓
BidResult / SecondBidResult (分配结果)
```

#### CompetitionPhase（比赛阶段）
- **作用**: 整体比赛流程管理
- **特点**: 
  - 基于时间的状态计算（upcoming/active/ended）
  - 页面访问权限控制（page_access JSON字段）
  - 统计数据类型控制（submissions_type: songs/charts）
  - phase_key 区分不同阶段类型（如 'bidding', 'mapping', 'peer_review'）

#### BiddingRound（第一轮竞标 - 歌曲）
- **作用**: 竞标歌曲的具体轮次
- **特点**:
  - 独立的状态管理（pending/active/completed）
  - 由 CompetitionPhase 动态创建（get_or_create）
  - 关联 Bid（竞标记录）和 BidResult（分配结果）

#### SecondBiddingRound（第二轮竞标 - 谱面）
- **作用**: 竞标其他用户的一半谱面来续写
- **特点**:
  - 与 BiddingRound 一对一关联
  - 独立的竞标和分配逻辑
  - 关联 SecondBid 和 SecondBidResult

### 2. 当前关联逻辑

**views.py 中的处理方式**:
```python
# 获取竞标轮次时的逻辑
if round_id:
    # 尝试作为 CompetitionPhase ID
    try:
        phase = CompetitionPhase.objects.get(id=round_id, phase_key__icontains='bidding')
        # 动态创建 BiddingRound
        round_obj, created = BiddingRound.objects.get_or_create(
            name=phase.name,
            defaults={'status': 'active'}
        )
    except CompetitionPhase.DoesNotExist:
        # 回退到直接使用 BiddingRound ID
        round_obj = BiddingRound.objects.get(id=round_id)
else:
    # 自动查找当前活跃的竞标阶段
    active_phase = CompetitionPhase.objects.filter(
        phase_key__icontains='bidding',
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).first()
```

**问题**:
- ❌ CompetitionPhase 和 BiddingRound 没有直接的外键关联
- ❌ 使用 `name` 字段进行关联（不可靠）
- ❌ 代码复杂度高（需要双重查询和回退逻辑）

---

## 🔄 代码复用性分析

### 当前复用情况

#### ✅ 可复用的部分
1. **BiddingService.allocate_bids()** - 核心分配算法
   - 两阶段分配（竞价 + 随机保底）
   - 同价格随机分配
   - 用户单次中标限制
   - 代币扣除逻辑

2. **Bid 模型设计**
   - 用户、目标对象、金额、状态字段
   - drop 机制

3. **BidResult 模型设计**
   - allocation_type 区分（win/random）
   - 分配金额记录

#### ❌ 不可复用的部分
1. **硬编码的模型引用**
   ```python
   # bidding_service.py
   from .models import Bid, BidResult, BiddingRound, Song  # 硬编码
   
   all_bids = Bid.objects.filter(...)  # 固定使用 Bid 模型
   BidResult.objects.create(...)       # 固定使用 BidResult 模型
   ```

2. **视图层逻辑重复**
   - user_bids_root() - 处理第一轮竞标
   - second_bidding_user_bids() - 处理第二轮竞标（需要重写相似逻辑）

3. **序列化器重复定义**
   - BidSerializer / SecondBidSerializer
   - BidResultSerializer / SecondBidResultSerializer

---

## 🚀 改进建议

### 方案 A: 添加直接关联（推荐）

**优点**: 清晰、可靠、易维护
**缺点**: 需要数据库迁移

#### 1. 修改模型
```python
class BiddingRound(models.Model):
    """竞标轮次"""
    # 新增：关联 CompetitionPhase
    competition_phase = models.ForeignKey(
        CompetitionPhase,
        on_delete=models.CASCADE,
        related_name='bidding_rounds',
        null=True,  # 兼容旧数据
        blank=True,
        help_text='所属比赛阶段'
    )
    
    # 新增：竞标类型（复用性）
    BIDDING_TYPE_CHOICES = [
        ('song', '歌曲竞标'),
        ('chart', '谱面竞标'),
    ]
    bidding_type = models.CharField(
        max_length=20,
        choices=BIDDING_TYPE_CHOICES,
        default='song',
        help_text='竞标类型'
    )
    
    # ... 其他字段保持不变
```

#### 2. 简化视图逻辑
```python
# 简化后的逻辑
if phase_id:
    phase = CompetitionPhase.objects.get(id=phase_id)
    # 直接通过外键获取
    round_obj = phase.bidding_rounds.filter(bidding_type='song').first()
    if not round_obj:
        # 创建新轮次
        round_obj = BiddingRound.objects.create(
            competition_phase=phase,
            name=phase.name,
            bidding_type='song',
            status='active'
        )
```

#### 3. 合并 SecondBiddingRound
```python
# 不需要单独的 SecondBiddingRound，使用统一的 BiddingRound
first_round = BiddingRound.objects.filter(
    competition_phase=phase, 
    bidding_type='song'
).first()

second_round = BiddingRound.objects.create(
    competition_phase=phase,
    bidding_type='chart',
    name=f"{phase.name} - 谱面竞标",
    status='active'
)
```

### 方案 B: 泛型竞标服务（高复用性）

**优点**: 极高复用性，一套代码处理所有竞标类型
**缺点**: 实现复杂度高

#### 1. 创建通用竞标服务
```python
# songs/generic_bidding_service.py
class GenericBiddingService:
    """通用竞标分配服务"""
    
    @staticmethod
    def allocate_bids(
        bidding_round,
        bid_model,           # 传入 Bid 或 SecondBid
        result_model,        # 传入 BidResult 或 SecondBidResult
        target_field='song', # 竞标目标字段名
        target_model=None    # 目标模型类（Song 或 Chart）
    ):
        """
        通用分配算法
        - bidding_round: 竞标轮次对象
        - bid_model: 竞标模型类（Bid/SecondBid）
        - result_model: 结果模型类（BidResult/SecondBidResult）
        - target_field: 目标字段名（'song'/'chart'）
        - target_model: 目标模型类（用于获取未分配对象）
        """
        # ... 通用分配逻辑（参数化所有模型引用）
```

#### 2. 使用示例
```python
# 第一轮竞标（歌曲）
GenericBiddingService.allocate_bids(
    bidding_round=round_obj,
    bid_model=Bid,
    result_model=BidResult,
    target_field='song',
    target_model=Song
)

# 第二轮竞标（谱面）
GenericBiddingService.allocate_bids(
    bidding_round=second_round_obj,
    bid_model=SecondBid,
    result_model=SecondBidResult,
    target_field='chart',
    target_model=Chart
)
```

### 方案 C: 保持现状 + 抽象公共逻辑（折中）

**优点**: 改动最小，风险低
**缺点**: 部分代码仍有重复

#### 1. 抽取公共算法
```python
# songs/bidding_utils.py
def allocate_generic(all_bids, get_target_id, create_result, drop_bid):
    """
    通用分配算法（无模型依赖）
    
    参数:
    - all_bids: 竞标列表
    - get_target_id: 函数，从竞标获取目标ID
    - create_result: 函数，创建分配结果
    - drop_bid: 函数，标记竞标为dropped
    """
    # 同价格随机打乱
    from collections import defaultdict
    bids_by_amount = defaultdict(list)
    for bid in all_bids:
        bids_by_amount[bid.amount].append(bid)
    
    sorted_bids = []
    for amount in sorted(bids_by_amount.keys(), reverse=True):
        group = bids_by_amount[amount]
        random.shuffle(group)
        sorted_bids.extend(group)
    
    allocated_targets = set()
    allocated_users = {}
    
    # 第一阶段：竞价分配
    for bid in sorted_bids:
        if bid.user.id in allocated_users:
            drop_bid(bid)
            continue
        
        target_id = get_target_id(bid)
        if target_id not in allocated_targets:
            create_result(bid, 'win')
            allocated_targets.add(target_id)
            allocated_users[bid.user.id] = target_id
            # drop其他竞标...
        else:
            drop_bid(bid)
    
    # 返回分配状态
    return allocated_targets, allocated_users
```

#### 2. 在具体服务中使用
```python
# bidding_service.py
from .bidding_utils import allocate_generic

class BiddingService:
    @staticmethod
    def allocate_bids(bidding_round_id):
        # ... 前置准备
        
        all_bids = Bid.objects.filter(...)
        
        allocated_targets, allocated_users = allocate_generic(
            all_bids=all_bids,
            get_target_id=lambda bid: bid.song.id,
            create_result=lambda bid, alloc_type: BidResult.objects.create(...),
            drop_bid=lambda bid: bid.update(is_dropped=True)
        )
        
        # ... 后续保底分配
```

---

## 📊 实施建议

### 短期（1-2周）
1. **添加 CompetitionPhase ↔ BiddingRound 外键关联**（方案A.1）
   - 修改模型添加 `competition_phase` 字段
   - 添加 `bidding_type` 区分歌曲/谱面竞标
   - 创建数据迁移

2. **简化视图层逻辑**（方案A.2）
   - 移除 `get_or_create` 的 name 匹配逻辑
   - 使用外键直接查询

### 中期（2-4周）
3. **抽象公共分配逻辑**（方案C）
   - 创建 `bidding_utils.py`
   - 重构现有 `BiddingService.allocate_bids()`
   - 为第二轮竞标创建类似服务

### 长期（可选）
4. **泛型服务升级**（方案B）
   - 完全参数化的分配服务
   - 支持未来任意类型的竞标（如：竞标评审权、竞标展示位等）

---

## 🔍 当前问题总结

### 1. 架构问题
- ❌ CompetitionPhase 和 BiddingRound 缺少直接关联
- ❌ 使用字符串匹配（name, phase_key）而非外键
- ❌ SecondBiddingRound 作为独立模型，未统一设计

### 2. 复用性问题
- ❌ BiddingService 硬编码模型引用
- ❌ 第一轮和第二轮竞标视图逻辑重复
- ⚠️ 序列化器和模型定义重复

### 3. 维护性问题
- ⚠️ get_or_create 容易导致数据不一致
- ⚠️ 双重查询增加数据库负担
- ⚠️ 缺少清晰的数据流文档

---

## ✅ 最佳实践

**对于您的问题**:

1. **竞标轮次和比赛阶段的对应关系**
   - 当前：通过 `name` 字段和 `phase_key` 字符串匹配关联
   - 建议：添加外键 `BiddingRound.competition_phase`

2. **代码复用性**
   - 当前：**不具备良好复用性**，需要为谱面竞标重写大部分逻辑
   - 建议：实施方案A（添加关联）+ 方案C（抽象公共逻辑）

3. **下一步行动**
   - ✅ 立即：添加 `competition_phase` 外键和 `bidding_type` 字段
   - ✅ 本周：重构视图层，使用外键关联
   - 📅 下周：抽象分配算法到 `bidding_utils.py`
   - 📅 未来：考虑统一 BiddingRound 和 SecondBiddingRound

---

## 📝 代码示例：推荐改造

### 迁移文件
```python
# songs/migrations/0008_add_bidding_phase_link.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('songs', '0007_competitionphase'),
    ]

    operations = [
        migrations.AddField(
            model_name='biddinground',
            name='competition_phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name='bidding_rounds',
                to='songs.competitionphase'
            ),
        ),
        migrations.AddField(
            model_name='biddinground',
            name='bidding_type',
            field=models.CharField(
                choices=[('song', '歌曲竞标'), ('chart', '谱面竞标')],
                default='song',
                help_text='竞标类型',
                max_length=20
            ),
        ),
    ]
```

### 简化后的视图
```python
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_bids_root(request):
    user = request.user
    
    if request.method == 'GET':
        phase_id = request.query_params.get('phase_id')
        
        if phase_id:
            phase = get_object_or_404(CompetitionPhase, id=phase_id)
            round_obj = phase.bidding_rounds.filter(bidding_type='song').first()
            
            if not round_obj:
                # 自动创建
                round_obj = BiddingRound.objects.create(
                    competition_phase=phase,
                    bidding_type='song',
                    name=phase.name,
                    status='active' if phase.status == 'active' else 'pending'
                )
        else:
            # 查找当前活跃的歌曲竞标阶段
            active_phase = CompetitionPhase.objects.filter(
                phase_key__icontains='bidding',
                is_active=True,
                status='active'  # 使用计算属性
            ).first()
            
            if not active_phase:
                return Response({'success': True, 'bids': [], 'message': '当前无活跃竞标'})
            
            round_obj = active_phase.bidding_rounds.filter(bidding_type='song').first()
        
        # ... 其余逻辑
```

这样修改后，**第二轮谱面竞标只需要修改 `bidding_type='chart'`**，其他逻辑完全复用！
