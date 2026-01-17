# 互评系统完整文档

## 系统概述

互评系统是游戏节奏游戏谱面设计竞赛中的第6阶段，用于用户对其他选手提交的谱面进行评分。核心特性：

- **匿名评分**：评分者身份保密
- **平衡分配**：每个选手刚好收到8个评分，每个评分者刚好评分8个谱面
- **文件外部托管**：谱面文件（maidata.txt）由外部服务器管理，本系统仅存储引用和评分数据
- **可配置满分**：评分满分默认50分，可通过Django settings配置

## 竞赛完整流程

```
阶段1：投稿歌曲
├─ 用户上传歌曲音频和元数据
└─ 系统存储并管理歌曲库

    ↓

阶段2：竞标选曲
├─ 创建竞标轮次 (BiddingRound)
├─ 用户使用虚拟货币(token)竞标心仪歌曲
├─ 支持二次投标：同一轮次中用户可多次竞标不同歌曲
└─ 各用户可获得多首歌曲

    ↓

阶段3：自动分配
├─ 按竞标金额从高到低分配（中标）
├─ 未中标的用户随机分配剩余歌曲
└─ 生成 BidResult 分配结果

    ↓

阶段4：创作谱面 (NEW - Phase 4)
├─ 用户为分配到的歌曲创作谱面（采用离线编辑）
├─ 提交谱面引用（chart_url 或 chart_id_external）
├─ 系统记录 Chart 对象，但文件由外部服务器托管
└─ 支持覆盖提交：用户可重新提交同一歌曲的谱面

    ↓

阶段5：上传谱面 (NEW - Phase 5)
├─ 谱面文件（maidata.txt）由用户上传到外部文件服务器
├─ 外部服务器返回 chart_url 或 chart_id
├─ 用户通过 /api/charts/{result_id}/submit/ 提交引用
└─ 前端无需编辑能力，仅下载歌曲和提交引用

    ↓

阶段6：随机互评 (NEW - Phase 6)
├─ 管理员调用 /api/peer-reviews/allocate/{round_id}/ 分配任务
├─ 系统使用平衡分配算法：
│  ├─ 保证每个谱面收到恰好8个评分
│  ├─ 保证每个评分者评分恰好8个谱面
│  ├─ 用户不能评自己的谱面
│  └─ 支持多轮优化确保完全匹配
├─ 创建 PeerReviewAllocation 分配记录
└─ 更新所有谱面状态为 under_review

    ↓

阶段6-续：提交评分
├─ 用户获取待评分任务列表
├─ 用户下载谱面文件进行评分
├─ 用户通过 /api/peer-reviews/allocations/{allocation_id}/submit/ 提交评分
├─ 系统验证评分范围 (0-50)
├─ 更新 Chart 的评分统计（review_count, total_score, average_score）
└─ 当某谱面收到8个评分时，标记为 reviewed

    ↓

最终排名
├─ 所有谱面评分完成后生成最终排名
├─ 通过 /api/rankings/{round_id}/ 获取排名
├─ 按平均分从高到低排序
└─ 展示选手名单、歌曲标题、平均分、评分数
```

## 二次投标支持设计

考虑用户可能在同一轮竞标中多次竞标不同歌曲的场景：

### 数据模型设计

```
Song (歌曲)
  ├─ user (上传者)
  ├─ title, audio_file, ...

BiddingRound (竞标轮次)
  ├─ name
  ├─ status: pending, active, completed

Bid (竞标记录)
  ├─ bidding_round (which round?)
  ├─ user (who bid?)
  ├─ song (which song?)
  ├─ amount (how much?)
  ├─ is_dropped (drop flag for non-winners)
  └─ unique_together: (bidding_round, user, song)

BidResult (分配结果)
  ├─ bidding_round (which round?)
  ├─ user (who got it?)
  ├─ song (which song?)
  ├─ allocation_type: win / random
  └─ unique_together: (bidding_round, user, song)

Chart (谱面)
  ├─ bidding_round (which round?)
  ├─ user (who created?)
  ├─ song (for which song?)
  ├─ bid_result (corresponding BidResult)
  ├─ status: draft, submitted, under_review, reviewed
  ├─ chart_url (外部URL)
  ├─ chart_id_external (外部ID)
  ├─ review_count, total_score, average_score
  └─ unique_together: (bidding_round, user, song)

PeerReviewAllocation (互评任务分配)
  ├─ bidding_round
  ├─ reviewer (who reviews?)
  ├─ chart (which chart to review?)
  ├─ status: pending, completed
  └─ unique_together: (bidding_round, reviewer, chart)

PeerReview (互评打分)
  ├─ allocation (reference to PeerReviewAllocation)
  ├─ reviewer, chart, bidding_round
  ├─ score (0-50)
  ├─ comment
  └─ created_at
```

### 支持二次投标的关键设计

1. **Bid.unique_together = (bidding_round, user, song)**
   - 同一轮中，用户对同一歌曲只能出价一次
   - 但用户可以对不同歌曲出价多次

2. **BidResult.unique_together = (bidding_round, user, song)**
   - 同一轮中，用户对同一歌曲最多获得一次
   - 但用户可以从不同歌曲获得多个分配

3. **Chart.unique_together = (bidding_round, user, song)**
   - 同一轮中，用户对同一歌曲最多提交一个谱面
   - 但用户可以创建多个不同歌曲的谱面

4. **工作流支持**：
   ```
   用户A投标歌曲X（100代币）→ 投标歌曲Y（80代币）
   ↓
   分配结果：歌曲X（中标）、歌曲Z（随机）
   ↓
   创建谱面X → 提交
   ↓
   创建谱面Z → 提交
   ↓
   互评分配给用户A共8个评分任务
   ↓
   用户A完成所有8个评分
   ↓
   排名统计
   ```

## 数据库模型

### Chart 模型

```python
class Chart(models.Model):
    """用户提交的谱面（beatmap）"""
    
    STATUS_CHOICES = [
        ('draft', '草稿'),           # 创建但未提交
        ('submitted', '已提交'),      # 提交但未进行互评
        ('under_review', '评分中'),   # 正在被互评
        ('reviewed', '已评分'),       # 互评完成
    ]
    
    # 关系
    bidding_round = ForeignKey(BiddingRound)  # 所属竞标轮次
    user = ForeignKey(User)                   # 谱面创建者
    song = ForeignKey(Song)                   # 对应歌曲
    bid_result = ForeignKey(BidResult)        # 对应的竞标结果
    
    # 状态
    status = CharField(choices=STATUS_CHOICES, default='draft')
    
    # 文件引用（外部托管）
    chart_url = URLField(null=True, blank=True)              # 完整URL
    chart_id_external = CharField(max_length=100, null=True) # 外部ID
    
    # 时间戳
    created_at = DateTimeField(auto_now_add=True)
    submitted_at = DateTimeField(null=True, blank=True)      # 提交时间
    review_completed_at = DateTimeField(null=True)           # 评分完成时间
    
    # 评分统计（冗余字段，便于查询）
    review_count = IntegerField(default=0)                  # 收到的评分数
    total_score = IntegerField(default=0)                   # 总评分
    average_score = FloatField(default=0.0)                 # 平均分(0-50)
    
    class Meta:
        unique_together = ('bidding_round', 'user', 'song')
```

### PeerReviewAllocation 模型

```python
class PeerReviewAllocation(models.Model):
    """互评任务分配"""
    
    bidding_round = ForeignKey(BiddingRound)      # 所属轮次
    reviewer = ForeignKey(User)                   # 评分者
    chart = ForeignKey(Chart)                     # 被评谱面
    status = CharField(                           # 任务状态
        choices=[('pending', '待评分'), ('completed', '已完成')],
        default='pending'
    )
    allocated_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('bidding_round', 'reviewer', 'chart')
```

### PeerReview 模型

```python
class PeerReview(models.Model):
    """互评打分记录"""
    
    allocation = OneToOneField(PeerReviewAllocation)  # 对应分配任务
    bidding_round = ForeignKey(BiddingRound)
    reviewer = ForeignKey(User)                       # 评分者身份
    chart = ForeignKey(Chart)                         # 被评谱面
    
    score = IntegerField()         # 评分(0-50)
    comment = TextField(blank=True)  # 评论
    created_at = DateTimeField(auto_now_add=True)
```

## 平衡分配算法

### 核心需求

对于竞赛的互评阶段，需要满足以下条件：

1. **每个提交谱面的选手**恰好收到 **8 个评分**
2. **每个评分者** 恰好评分 **8 个谱面**
3. **评分者不能评自己的谱面**
4. **分配尽可能平衡**

### 数学模型

设：
- $n$ = 提交谱面的选手数
- $k$ = 每个选手应收的评分数（通常为8）

则：
- 总评分任务数 = $n \times k$
- 每个评分者的任务数 = $k$
- 所需评分者数 = $n$（必须等于选手数）

理想情况下：$n \times k = n \times k$ ✓

### 算法实现

采用**贪心轮转算法**：

```python
def allocate_peer_reviews(bidding_round_id, reviews_per_user=8):
    """
    分配互评任务
    
    算法步骤：
    1. 获取该轮所有已提交谱面 (charts_list)
    2. 获取所有参与选手 (reviewers_list)
    3. 初始化计数器：chart_review_counts, reviewer_task_counts
    4. 循环分配 total_assignments_needed = len(charts) * reviews_per_user 次：
       a. 找到评分数最少的谱面
       b. 轮转寻找合适的评分者（满足条件）：
          - 任务未满（reviewer_task_counts < reviews_per_user）
          - 不是该谱面的创建者
          - 还未评过这个谱面
       c. 创建分配记录，更新计数器
    5. 批量创建所有分配记录
    """
```

### 时间复杂度

- **主循环**：$O(n \times k)$
- **内层循环**：$O(n)$（最坏情况下寻找评分者）
- **总体**：$O(n^2 \times k)$

对于 $n=30, k=8$：约 7200 次操作，完全可接受

## API 端点设计

### 1. 提交谱面

```http
POST /api/charts/{result_id}/submit/
Content-Type: application/json
Authorization: Bearer <token>

{
  "chart_url": "https://chart-server.com/charts/abc123/maidata.txt",
  "chart_id_external": "abc123"  // 至少提供一个
}
```

**响应**：
```json
{
  "success": true,
  "message": "谱面提交成功",
  "chart": {
    "id": 1,
    "username": "user1",
    "song": { "id": 5, "title": "Song Title", ... },
    "status": "submitted",
    "status_display": "已提交",
    "chart_url": "https://...",
    "review_count": 0,
    "average_score": 0.0,
    "created_at": "2026-01-17T12:00:00Z",
    "submitted_at": "2026-01-17T12:05:00Z"
  }
}
```

### 2. 获取用户谱面列表

```http
GET /api/charts/me/?bidding_round_id=1
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "count": 3,
  "charts": [
    {
      "id": 1,
      "username": "user1",
      "song": {...},
      "status": "reviewed",
      "status_display": "已评分",
      "review_count": 8,
      "average_score": 42.5,
      ...
    }
  ]
}
```

### 3. 分配互评任务（管理员操作）

```http
POST /api/peer-reviews/allocate/{round_id}/
Content-Type: application/json
Authorization: Bearer <token>

{
  "reviews_per_user": 8  // 可选，默认为8
}
```

**响应**：
```json
{
  "success": true,
  "message": "互评任务分配成功",
  "allocation": {
    "bidding_round_id": 1,
    "total_allocations": 240,  // 30个谱面 × 8 = 240
    "charts_count": 30,
    "reviewers_count": 30,
    "reviews_per_chart": 8,
    "tasks_per_reviewer": 8,
    "status": "success"
  }
}
```

### 4. 获取用户的评分任务

```http
GET /api/peer-reviews/tasks/{round_id}/
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "round": {
    "id": 1,
    "name": "竞赛第一轮"
  },
  "task_count": 8,
  "tasks": [
    {
      "id": 101,
      "chart_id": 15,
      "song_title": "Example Song",
      "chart_url": "https://chart-server.com/charts/xyz789/maidata.txt",
      "status": "pending",
      "status_display": "待评分",
      "allocated_at": "2026-01-17T10:00:00Z"
    },
    ...
  ]
}
```

### 5. 提交评分

```http
POST /api/peer-reviews/allocations/{allocation_id}/submit/
Content-Type: application/json
Authorization: Bearer <token>

{
  "score": 42,
  "comment": "节奏感很强！"  // 可选
}
```

**响应**：
```json
{
  "success": true,
  "message": "评分提交成功",
  "review": {
    "id": 501,
    "score": 42,
    "comment": "节奏感很强！",
    "created_at": "2026-01-17T13:00:00Z"
  }
}
```

### 6. 获取谱面的所有评分（匿名）

```http
GET /api/charts/{chart_id}/reviews/
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "chart": {
    "id": 15,
    "username": "creator_user",
    "song": { "id": 5, "title": "Example Song", ... },
    "status": "reviewed",
    "review_count": 8,
    "average_score": 42.5,
    "total_score": 340,
    "reviews": [
      {
        "score": 42,
        "comment": "节奏感很强！",
        "created_at": "2026-01-17T13:00:00Z"
      },
      ...
    ]
  }
}
```

### 7. 获取轮次排名

```http
GET /api/rankings/{round_id}/
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "round": {
    "id": 1,
    "name": "竞赛第一轮"
  },
  "total": 30,
  "rankings": [
    {
      "rank": 1,
      "username": "top_player",
      "song_title": "Popular Song",
      "average_score": 48.2,
      "review_count": 8,
      "total_score": 386
    },
    {
      "rank": 2,
      "username": "second_place",
      "song_title": "Another Song",
      "average_score": 45.8,
      "review_count": 8,
      "total_score": 366
    },
    ...
  ]
}
```

## 代码复用设计

### 竞标阶段代码

```python
class BiddingService:
    @staticmethod
    @transaction.atomic
    def allocate_bids(bidding_round_id):
        """第3阶段：自动分配算法"""
        # 获取BiddingRound, Bid, 计算allocation
        pass
    
    @staticmethod
    def get_user_results(user, bidding_round):
        """查询用户的分配结果"""
        pass
```

### 互评阶段代码

```python
class PeerReviewService:
    @staticmethod
    @transaction.atomic
    def allocate_peer_reviews(bidding_round_id, reviews_per_user=8):
        """第6阶段：互评分配算法"""
        # 结构与 BiddingService.allocate_bids 类似：
        # 1. 获取实体列表（Chart vs Bid）
        # 2. 验证条件
        # 3. 使用轮转算法分配
        # 4. 批量创建记录
        pass
    
    @staticmethod
    def submit_peer_review(allocation_id, score, comment=None):
        """提交评分"""
        pass
    
    @staticmethod
    def get_user_review_tasks(user, bidding_round):
        """查询用户的评分任务"""
        pass
```

### 复用策略

1. **模式复用**：
   - 分配算法的基本结构相同（排序/轮转 + 批量创建）
   - 可提取为 `AbstractAllocationService`

2. **模型设计复用**：
   - BidResult 和 PeerReview 都是"结果记录"
   - PeerReviewAllocation 和 Bid 都是"待处理任务"

3. **验证逻辑复用**：
   - 两个系统都需要检查用户权限
   - 都需要检查轮次状态

## 配置和调整

### Django Settings

```python
# settings.py

# 竞标系统配置
MAX_SONGS_PER_USER = 2           # 每个用户最多上传2首歌曲
MAX_BIDS_PER_USER = 5            # 每个用户每轮最多竞标5次

# 互评系统配置
PEER_REVIEW_TASKS_PER_USER = 8   # 每个用户评分8个谱面
PEER_REVIEW_MAX_SCORE = 50       # 互评满分50分

# 外部文件服务器配置
CHART_EXTERNAL_SERVER = 'https://chart-server.com'
CHART_URL_PATTERN = '{server}/charts/{chart_id}/maidata.txt'
```

### 满分调整

满分从 50 分调整为其他值：

1. **修改常量**：
   ```python
   # songs/models.py
   PEER_REVIEW_MAX_SCORE = 100  # 改为100分
   ```

2. **或使用Django Settings**（推荐）：
   ```python
   # settings.py
   PEER_REVIEW_MAX_SCORE = 100
   ```

3. **在序列化器中使用**：
   ```python
   # serializers.py
   from django.conf import settings
   
   class PeerReviewSubmitSerializer(serializers.ModelSerializer):
       def validate_score(self, value):
           max_score = getattr(settings, 'PEER_REVIEW_MAX_SCORE', 50)
           if value < 0 or value > max_score:
               raise ValidationError(f'评分必须在0-{max_score}之间')
           return value
   ```

## 测试用例

### 场景1：完整流程测试

```
Step 1: 创建竞标轮次
  - 创建 BiddingRound (status='pending')

Step 2: 用户上传歌曲
  - 用户A上传歌曲X、Y
  - 用户B上传歌曲Z、W

Step 3: 开启竞标
  - 更新 BiddingRound.status = 'active'

Step 4: 用户竞标
  - 用户A竞标歌曲X (100代币)、歌曲Z (80代币)
  - 用户B竞标歌曲X (120代币)、歌曲Y (60代币)

Step 5: 执行分配
  - 调用 /api/bids/allocate/
  - 歌曲X → 用户B (120代币，中标)
  - 歌曲Z → 用户A (80代币，中标)
  - 歌曲Y → 用户A (随机分配)
  - 歌曲W → 用户B (随机分配)
  - BiddingRound.status = 'completed'

Step 6: 用户创建谱面
  - 用户A创建谱面Z、Y
  - 用户B创建谱面X、W
  - 调用 /api/charts/{result_id}/submit/

Step 7: 分配互评
  - 调用 /api/peer-reviews/allocate/1/
  - 创建 2×8=16 个 PeerReviewAllocation
  - 验证每个用户8个任务、每个谱面8个评分者

Step 8: 用户提交评分
  - 用户A调用 /api/peer-reviews/tasks/1/
  - 获取8个评分任务
  - 逐个调用 /api/peer-reviews/allocations/{id}/submit/
  - 用户B同样操作

Step 9: 查看排名
  - 调用 /api/rankings/1/
  - 返回按平均分排序的排名
```

### 场景2：二次投标测试

```
用户A已获得歌曲X，创建并提交谱面
之后想再竞标歌曲Y（同一轮）
→ 创建新的Bid记录
→ 分配后再创建谱面Y
→ 互评时评分2个谱面（X和Y）
```

## 前后端约定

### 前端需要的功能

1. **谱面管理界面**
   - 显示用户获得的歌曲列表
   - 显示下载链接（指向外部服务器）
   - 显示提交谱面的表单（输入chart_url或chart_id_external）

2. **互评界面**
   - 显示待评分任务列表
   - 提供下载链接到外部服务器
   - 提供评分表单（0-50滑块/输入框）
   - 可选的评论输入框
   - 提交评分按钮

3. **排名界面**
   - 显示排名表格
   - 显示平均分、总评分数等

### 后端提供的数据

- Chart 对象中包含 `chart_url` 和 `chart_id_external`
- PeerReviewAllocation 中包含 `chart_url` 供前端下载
- PeerReview 中的 `score` 和 `comment` 为匿名（不显示评分者）

## 错误处理

### 常见错误

1. **分配时选手数不足**
   ```
   错误：无法进行平衡分配：25个谱面 × 8个评分 = 200，
        但20个评分者 × 8个任务 = 160
   处理：要求所有参与竞标的用户都必须提交谱面
   ```

2. **用户评自己的谱面**
   ```
   检查：reviewer.id != chart.user_id
   处理：自动跳过该分配，寻找其他评分者
   ```

3. **评分范围错误**
   ```
   验证：0 <= score <= PEER_REVIEW_MAX_SCORE
   返回：400 Bad Request，提示正确范围
   ```

## 性能优化

1. **查询优化**
   - 使用 `select_related` 加载关联对象
   - 使用 `prefetch_related` 预加载反向关系
   - 索引关键查询字段（reviewer, chart, bidding_round）

2. **批量操作**
   - 使用 `bulk_create` 一次性创建所有分配
   - 不在循环中执行数据库查询

3. **缓存**
   - 缓存排名结果（评分完成后）
   - 缓存用户的任务列表

## 总结

该互评系统：
- ✅ 支持完全匿名评分
- ✅ 保证平衡分配（每人8个任务和8个评分）
- ✅ 支持二次投标（同轮多歌曲）
- ✅ 外部文件托管（仅存储引用）
- ✅ 灵活的满分配置
- ✅ 高效的算法（O(n²k)）
- ✅ 代码复用（与竞标系统模式相同）
