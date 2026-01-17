from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from songs.models import Banner, Announcement, CompetitionPhase


class Command(BaseCommand):
    help = '添加示例 Banner、Announcement 和 CompetitionPhase 数据'

    def handle(self, *args, **options):
        # 清空现有数据
        Banner.objects.all().delete()
        Announcement.objects.all().delete()
        CompetitionPhase.objects.all().delete()
        
        # 创建示例 Banner
        banners = [
            Banner.objects.create(
                title='欢迎来到 XMMCG',
                content='谱面创作竞赛平台，展现你的创意才华',
                color='#409EFF',
                link='/songs',
                button_text='开始竞标',
                priority=10,
                is_active=True
            ),
            Banner.objects.create(
                title='第一轮竞标进行中',
                content='参与歌曲竞标，赢取制谱权利',
                color='#67C23A',
                link='/charts',
                button_text='查看谱面',
                priority=9,
                is_active=True
            ),
            Banner.objects.create(
                title='互评系统',
                content='公平公正的评分机制，让优秀作品脱颖而出',
                color='#E6A23C',
                link='/profile',
                button_text='个人中心',
                priority=8,
                is_active=True
            ),
        ]
        
        # 创建示例 Announcement
        announcements = [
            Announcement.objects.create(
                title='平台使用说明',
                content='''# XMMCG 平台使用指南

欢迎来到谱面创作竞赛平台！本平台为音乐谱面创作者提供了完整的竞标和评分系统。

## 主要功能

- **歌曲竞标**：使用虚拟代币竞标喜爱的歌曲
- **谱面创作**：为竞标成功的歌曲制作谱面
- **互评系统**：参与公平的互相评分
- **排名统计**：实时查看创作者排名

## 快速开始

1. 登录或注册账号
2. 获取初始代币
3. 竞标感兴趣的歌曲
4. 创作精美谱面
5. 参与互评获得高分

## 注意事项

- 每位用户最多可竞标 **5 首** 歌曲
- 每位用户最多可上传 **2 首** 歌曲
- 代币有限，请合理分配
- 互评结果将影响最终排名

祝您创作愉快！''',
                category='notice',
                priority=10,
                is_pinned=True,
                is_active=True
            ),
            Announcement.objects.create(
                title='第一轮竞标已启动',
                content='''## 重要通知

第一轮歌曲竞标现已正式开始！

### 活动时间
- 开始时间：2026-01-17
- 预计持续：7 天

### 参与方式

在首页导航栏点击**歌曲**，即可查看所有可竞标的歌曲列表。

每首歌曲的详情页面会显示：
- 歌曲名称与上传者
- 网易云链接（如有）
- 当前最高出价
- 竞标人数

### 竞标规则

- 单次竞标金额：1 代币及以上
- 每位用户限额：5 首歌曲
- 最后统计时间：竞标结束时

### 温馨提示

💡 **策略建议**：
- 合理评估每首歌曲的价值
- 根据个人实力分配代币
- 不要在最后关头仓促决定

如有任何问题，欢迎在平台内反馈。祝各位竞标顺利！''',
                category='event',
                priority=9,
                is_pinned=True,
                is_active=True
            ),
            Announcement.objects.create(
                title='互评系统上线',
                content='''互评系统现已正式上线！

每位参赛者都将获得评分任务，评价他人的谱面作品。

**评分标准**（0-50 分）：
- 创意性：10 分
- 难度设计：10 分  
- 音乐契合度：10 分
- 操作流畅性：10 分
- 整体印象：10 分

您的评分将被纳入最终排名计算。''',
                category='news',
                priority=8,
                is_active=True
            ),
        ]
        
        # 创建标准比赛阶段（4 个）
        now = timezone.now()
        phases = [
            CompetitionPhase.objects.create(
                name='竞标期',
                phase_key='bidding',
                description='选择喜爱的歌曲，使用虚拟代币进行竞标。这是获得制谱权利的第一步。',
                start_time=now - timedelta(days=1),  # 已开始
                end_time=now + timedelta(days=6),   # 7 天后结束
                order=1,
                is_active=True,
                page_access={
                    'songs': True,
                    'charts': False,
                    'profile': True
                }
            ),
            CompetitionPhase.objects.create(
                name='制谱期',
                phase_key='mapping',
                description='根据竞标结果，在规定时间内完成歌曲的谱面制作。',
                start_time=now + timedelta(days=6),
                end_time=now + timedelta(days=20),  # 14 天
                order=2,
                is_active=True,
                page_access={
                    'songs': False,
                    'charts': True,
                    'profile': True
                }
            ),
            CompetitionPhase.objects.create(
                name='互评期',
                phase_key='peer_review',
                description='对其他创作者的作品进行公平评分。您的评分结果将影响最终排名。',
                start_time=now + timedelta(days=20),
                end_time=now + timedelta(days=34),  # 14 天
                order=3,
                is_active=True,
                page_access={
                    'songs': False,
                    'charts': True,
                    'profile': True
                }
            ),
            CompetitionPhase.objects.create(
                name='结束期',
                phase_key='ended',
                description='本轮竞赛已结束。点击"排名"查看最终成绩。',
                start_time=now + timedelta(days=34),
                end_time=now + timedelta(days=60),
                order=4,
                is_active=True,
                page_access={
                    'songs': False,
                    'charts': False,
                    'profile': True
                }
            ),
        ]
        
        self.stdout.write(self.style.SUCCESS(f'✓ 成功创建 {len(banners)} 个 Banner'))
        self.stdout.write(self.style.SUCCESS(f'✓ 成功创建 {len(announcements)} 个 Announcement'))
        self.stdout.write(self.style.SUCCESS(f'✓ 成功创建 {len(phases)} 个 CompetitionPhase'))

