# 比赛阶段管理系统 - 完整文档

## 📋 系统概述

完整实现了一个**后端驱动的比赛阶段管理系统**，支持：
- 🎯 任意个阶段创建和时间配置
- 🔐 每个阶段的页面访问权限控制
- ⏱️ 实时阶段状态计算（进行中/即将开始/已结束）
- 📊 主页时间轴展示所有阶段
- 🚫 动态菜单禁用和路由守卫

---

## 🔧 后端实现

### 1. 数据模型 ([songs/models.py](songs/models.py))

```python
class CompetitionPhase(models.Model):
    # 阶段信息
    name                CharField        # 阶段名称，如"竞标期"
    phase_key           CharField(unique) # 唯一标识，用于权限绑定
    description         TextField        # 阶段描述
    
    # 时间配置
    start_time          DateTimeField    # 开始时间
    end_time            DateTimeField    # 结束时间
    
    # 权限和显示
    order               PositiveInteger  # 显示顺序
    is_active           BooleanField     # 是否启用
    page_access         JSONField        # 页面访问权限配置
    
    # @property status: 'upcoming'|'active'|'ended' (自动计算)
    # def get_time_remaining(): 返回剩余时间字符串
    # def get_progress_percent(): 返回进度百分比 (0-100)
```

### 2. 序列化器 ([songs/serializers.py](songs/serializers.py))

```python
class CompetitionPhaseSerializer(serializers.ModelSerializer):
    status              SerializerMethodField  # 自动计算，实时准确
    time_remaining      SerializerMethodField  # "2 天 5 小时" 格式
    progress_percent    SerializerMethodField  # 0-100 百分比
    
    fields: id, name, phase_key, description, start_time, end_time,
            order, status, time_remaining, progress_percent, page_access, is_active
```

### 3. API 端点 ([songs/views.py](songs/views.py))

#### `GET /api/songs/phases/` - 获取所有阶段
```json
[
  {
    "id": 1,
    "name": "竞标期",
    "phase_key": "bidding",
    "status": "active",
    "progress_percent": 45,
    "time_remaining": "3 天 2 小时",
    "page_access": {
      "home": true,
      "songs": true,
      "charts": false,
      "profile": true
    }
  },
  ...
]
```

#### `GET /api/songs/phase/current/` - 获取当前活跃阶段
```json
{
  "id": 1,
  "name": "竞标期",
  "phase_key": "bidding",
  "status": "active",
  "page_access": {...}
}
```

### 4. Django Admin 配置 ([songs/admin.py](songs/admin.py))

**CompetitionPhaseAdmin** 提供：
- ✅ 列表显示：名称、标识、状态、时间、顺序、启用状态
- ✅ 搜索：按名称和标识符搜索
- ✅ 过滤：按启用状态、开始时间等筛选
- ✅ 字段分组：基本信息 / 时间配置 / 权限设置 / 管理
- ✅ 拖拽排序：通过 order 字段控制显示顺序

**管理员操作流程：**
1. 访问 Django Admin: `http://localhost:8000/admin`
2. 点击"比赛阶段"
3. 点击"添加比赛阶段"
4. 填写表单：
   - 名称：竞标期
   - 标识：bidding
   - 开始时间、结束时间
   - 顺序：1
   - 页面访问权限：`{"home": true, "songs": true, "charts": false, "profile": true}`
5. 保存

### 5. 初始数据 ([add_sample_data.py](songs/management/commands/add_sample_data.py))

已预设 **4 个标准阶段**：

| 阶段 | phase_key | 持续时间 | 开放功能 |
|------|-----------|---------|---------|
| 竞标期 | bidding | 7 天 | songs, charts(只读) |
| 制谱期 | mapping | 14 天 | charts, songs(只读) |
| 互评期 | peer_review | 14 天 | charts(互评), 其他只读 |
| 结束期 | ended | 26 天 | 排名查看，其他只读 |

运行命令加载初始数据：
```bash
python manage.py add_sample_data
```

---

## 🎨 前端实现

### 1. API 集成 ([src/api/index.js](src/api/index.js))

```javascript
// 获取所有阶段
export const getCompetitionPhases = async () 
  // GET /api/songs/phases/
  // 返回: [{...phase}, ...]

// 获取当前活跃阶段
export const getCurrentPhase = async ()
  // GET /api/songs/phase/current/
  // 返回: {...currentPhase} 或默认阶段对象
```

### 2. 路由守卫 ([src/router/index.js](src/router/index.js))

```javascript
// 导出函数，供组件使用
export const useCurrentPhase = async ()
  // 获取当前阶段信息，带 10 秒缓存

// router.beforeEach 检查页面访问权限
// 如果 phase.page_access[pageName] === false
//   → 显示警告提示
//   → 重定向回首页
```

**工作流程：**
1. 用户点击"歌曲"菜单
2. 路由守卫拦截，检查当前阶段权限
3. 如果竞标期允许访问 `page_access.songs = true`，进入页面
4. 否则显示浮窗提示 "此功能将在竞标期开放"，停留在当前页面

### 3. 时间轴组件 ([src/components/PhaseTimeline.vue](src/components/PhaseTimeline.vue))

**显示内容：**
- 📅 所有阶段的时间线
- 🏷️ 每个阶段的状态标签（进行中/即将开始/已结束）
- ⏱️ 剩余时间倒计时
- 📊 进度条（仅进行中的阶段）
- 🔓 该阶段开放的功能（带绿色标签）和锁定的功能（带灰色标签）

**特性：**
- 每 30 秒自动刷新（更新倒计时和进度）
- 响应式设计，自动适配移动端

### 4. 导航栏增强 ([src/components/Navbar.vue](src/components/Navbar.vue))

**动态菜单功能：**
- 根据当前阶段的 `page_access`，动态禁用菜单项
- 禁用项变灰且显示警告图标
- 鼠标悬停显示提示："此功能在竞标期开放"
- 点击被禁用菜单项时显示警告消息

**代码示例：**
```vue
<el-menu-item 
  index="/songs"
  :disabled="!pageAccess.songs"
  :class="{ 'disabled-menu-item': !pageAccess.songs }"
>
  歌曲
  <el-tooltip v-if="!pageAccess.songs" content="此功能在竞标期开放">
    <el-icon><Warning /></el-icon>
  </el-tooltip>
</el-menu-item>
```

### 5. 主页集成 ([src/views/Home.vue](src/views/Home.vue))

在首页展示：
- 竞赛阶段日程时间轴（PhaseTimeline 组件）
- 当前活跃阶段的状态和剩余时间

---

## ⏱️ Status 字段解释

`status` 字段是**实时计算的属性**，不保存到数据库：

```python
@property
def status(self):
    from django.utils import timezone
    now = timezone.now()
    
    if now < self.start_time:
        return 'upcoming'       # ⏳ 即将开始
    elif now <= self.end_time:
        return 'active'         # ⏱️ 进行中（最多 2 天 5 小时）
    else:
        return 'ended'          # ✅ 已结束
```

**优点：**
- ✅ 前端每次获取都是最新的实时状态
- ✅ 不需要定时任务或数据库更新
- ✅ 时间准确到秒

---

## 🔄 数据流示例

### 场景 1：竞标期 (2026-01-17 00:00 ~ 2026-01-24 00:00)

**后端返回：**
```json
{
  "name": "竞标期",
  "status": "active",
  "time_remaining": "2 天 5 小时",
  "progress_percent": 45,
  "page_access": {
    "home": true,
    "songs": true,
    "charts": false,
    "profile": true
  }
}
```

**前端行为：**
- ✅ 首页、歌曲、个人中心菜单**可点击**
- ❌ 谱面菜单**禁用**（灰显 + 警告图标）
- ⏱️ 主页显示"竞标期，剩余 2 天 5 小时"

### 场景 2：制谱期 (2026-01-24 00:00 ~ 2026-02-07 00:00)

**自动转换：**
```json
{
  "name": "制谱期",
  "status": "active",
  "page_access": {
    "home": true,
    "songs": false,
    "charts": true,
    "profile": true
  }
}
```

**前端行为：**
- ✅ 首页、谱面、个人中心菜单**可点击**
- ❌ 歌曲菜单**禁用**
- 用户访问 `/songs` 时自动重定向到首页并显示提示

---

## 📊 数据库迁移

已自动创建迁移文件 `0007_competitionphase.py`

**创建表的字段：**
- id (PK)
- name, phase_key, description
- start_time, end_time
- order, is_active
- page_access (JSON)
- created_at, updated_at

---

## 🎯 使用指南

### 管理员：添加新阶段

1. **访问 Admin**：http://localhost:8000/admin → 比赛阶段
2. **点击"添加"**
3. **填写表单**：
   ```
   名称：互评期
   标识：peer_review
   描述：对他人作品进行评分...
   开始时间：2026-02-07 00:00
   结束时间：2026-02-21 00:00
   顺序：3
   启用：✓
   
   页面访问权限 JSON：
   {
     "home": true,
     "songs": false,
     "charts": true,
     "profile": true
   }
   ```
4. **保存**

### 用户：查看阶段日程

- 访问首页，滚动到**竞赛阶段日程**部分
- 查看所有阶段的时间线、状态、剩余时间、开放功能

### 用户：受到权限限制

- 尝试访问被禁用的功能
- 浮窗提示："此功能将在xxx阶段开放。当前阶段：竞标期 (2 天 5 小时)"
- 自动停留在当前页面

---

## 📁 文件修改清单

### 后端文件

| 文件 | 修改内容 |
|------|---------|
| `songs/models.py` | 添加 CompetitionPhase 模型 + 时间计算方法 |
| `songs/serializers.py` | 添加 CompetitionPhaseSerializer |
| `songs/views.py` | 添加 get_competition_phases() 和 get_current_phase() |
| `songs/urls.py` | 添加 /phases/ 和 /phase/current/ 路由 |
| `songs/admin.py` | 添加 CompetitionPhaseAdmin 配置 |
| `songs/migrations/0007_competitionphase.py` | 数据库迁移（自动生成） |
| `songs/management/commands/add_sample_data.py` | 添加 4 个初始阶段 |

### 前端文件

| 文件 | 修改内容 |
|------|---------|
| `src/api/index.js` | 添加 getCurrentPhase() 和 getCompetitionPhases() 函数 |
| `src/router/index.js` | 添加路由守卫和权限检查逻辑 |
| `src/components/PhaseTimeline.vue` | 新建时间轴组件 |
| `src/components/Navbar.vue` | 动态菜单禁用和权限检查 |
| `src/views/Home.vue` | 集成 PhaseTimeline 组件 |

---

## ✅ 测试清单

- [ ] 后端迁移成功：`python manage.py migrate`
- [ ] 初始数据加载：`python manage.py add_sample_data`
- [ ] Admin 可访问阶段列表：http://localhost:8000/admin/songs/competitionphase/
- [ ] API 返回正确数据：`GET /api/songs/phases/`
- [ ] 当前阶段 API 工作：`GET /api/songs/phase/current/`
- [ ] 首页显示时间轴
- [ ] 菜单项动态禁用/启用
- [ ] 路由守卫阻止非授权访问
- [ ] 浮窗提示正确显示

---

## 🔮 后续扩展

### 可选功能

1. **阶段回放**：已结束的阶段可查看历史数据
2. **提前提示**：阶段即将开始时发送通知
3. **手动覆盖**：管理员可临时调整权限（绕过自动计算）
4. **阶段统计**：每个阶段的参与情况报表
5. **权限细粒度**：支持用户组级别的不同权限

