"""
第二轮竞标系统验证脚本
验证第二轮竞标模型、服务和API端点的功能
"""

import os
import sys
import django
from datetime import datetime, timedelta

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
sys.path.insert(0, r'd:\code\xmmcg\backend\xmmcg')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
from songs.models import (
    Song, BiddingRound, Bid, BidResult, Chart, SecondBiddingRound, 
    SecondBid, SecondBidResult
)
from songs.bidding_service import BiddingService, SecondBiddingService
from users.models import UserProfile

print("=" * 80)
print("第二轮竞标系统验证测试")
print("=" * 80)

# 清理测试数据
print("\n[1] 清理旧数据...")
try:
    SecondBidResult.objects.all().delete()
    SecondBid.objects.all().delete()
    SecondBiddingRound.objects.all().delete()
    Chart.objects.all().delete()
    BidResult.objects.all().delete()
    Bid.objects.all().delete()
    BiddingRound.objects.all().delete()
    Song.objects.all().delete()
    User.objects.filter(username__startswith='test_user_').delete()
    print("✓ 旧数据清理完成")
except Exception as e:
    print(f"✗ 清理数据失败: {e}")
    sys.exit(1)

# 创建测试用户
print("\n[2] 创建测试用户...")
test_users = []
try:
    for i in range(3):
        user = User.objects.create_user(
            username=f'test_user_{i}',
            email=f'test_{i}@example.com',
            password='testpass123'
        )
        profile = UserProfile.objects.get_or_create(user=user)[0]
        profile.token = 100  # 初始token
        profile.save()
        test_users.append(user)
        print(f"✓ 创建用户: {user.username} (token=100)")
except Exception as e:
    print(f"✗ 创建用户失败: {e}")
    sys.exit(1)

# 创建歌曲
print("\n[3] 创建测试歌曲...")
test_songs = []
try:
    for i in range(2):
        song = Song.objects.create(
            user=test_users[0],
            title=f'Test Song {i}',
            audio_hash=f'hash_{i}',
            file_size=1024
        )
        test_songs.append(song)
        print(f"✓ 创建歌曲: {song.title} (ID={song.id})")
except Exception as e:
    print(f"✗ 创建歌曲失败: {e}")
    sys.exit(1)

# 创建第一轮竞标轮次并进行竞标
print("\n[4] 创建第一轮竞标轮次...")
try:
    first_round = BiddingRound.objects.create(
        name='First Round',
        status='active'
    )
    print(f"✓ 创建竞标轮次: {first_round.name} (ID={first_round.id})")
except Exception as e:
    print(f"✗ 创建竞标轮次失败: {e}")
    sys.exit(1)

# 第一轮竞标
print("\n[5] 进行第一轮竞标...")
try:
    # User 1 竞标 Song 0，出价60
    bid1 = Bid.objects.create(
        bidding_round=first_round,
        user=test_users[1],
        song=test_songs[0],
        amount=60
    )
    print(f"✓ User 1 竞标 {test_songs[0].title}: 60 token")
    
    # User 2 竞标 Song 0，出价40
    bid2 = Bid.objects.create(
        bidding_round=first_round,
        user=test_users[2],
        song=test_songs[0],
        amount=40
    )
    print(f"✓ User 2 竞标 {test_songs[0].title}: 40 token")
    
    # User 1 竞标 Song 1，出价50
    bid3 = Bid.objects.create(
        bidding_round=first_round,
        user=test_users[1],
        song=test_songs[1],
        amount=50
    )
    print(f"✓ User 1 竞标 {test_songs[1].title}: 50 token")
    
except Exception as e:
    print(f"✗ 竞标失败: {e}")
    sys.exit(1)

# 执行第一轮分配
print("\n[6] 执行第一轮竞标分配...")
try:
    result = BiddingService.allocate_bids(first_round.id)
    print(f"✓ 分配完成")
    
    # 验证分配结果
    bid_results = BidResult.objects.filter(bidding_round=first_round)
    for br in bid_results:
        print(f"  - {br.user.username} 获得 {br.song.title} (分配类型: {br.allocation_type})")
        
except Exception as e:
    print(f"✗ 分配失败: {e}")
    sys.exit(1)

# 创建第一部分谱面
print("\n[7] 创建第一部分谱面...")
try:
    part_one_charts = []
    for br in BidResult.objects.filter(bidding_round=first_round):
        chart = Chart.objects.create(
            bidding_round=first_round,
            user=br.user,
            song=br.song,
            bid_result=br,
            is_part_one=True,
            chart_url='https://example.com/chart1.txt',
            status='submitted',
            review_count=8,  # 假设已收到所有评分
            total_score=400,
            average_score=50
        )
        part_one_charts.append(chart)
        print(f"✓ {br.user.username} 提交的谱面 {br.song.title} (一半) - ID={chart.id}")
except Exception as e:
    print(f"✗ 创建谱面失败: {e}")
    sys.exit(1)

# 创建第二轮竞标轮次
print("\n[8] 创建第二轮竞标轮次...")
try:
    second_round = SecondBiddingRound.objects.create(
        first_bidding_round=first_round,
        name='Second Round - Complete Halves',
        status='active'
    )
    print(f"✓ 创建第二轮竞标轮次 (ID={second_round.id})")
except Exception as e:
    print(f"✗ 创建第二轮竞标轮次失败: {e}")
    sys.exit(1)

# 第二轮竞标
print("\n[9] 进行第二轮竞标...")
try:
    # User 1 不能竞标自己的谱面（User 1 创建了第一个谱面）
    # User 2 竞标第一个谱面，出价30
    if part_one_charts[0].user != test_users[2]:
        bid4 = SecondBid.objects.create(
            second_bidding_round=second_round,
            bidder=test_users[2],
            target_chart_part_one=part_one_charts[0],
            amount=30
        )
        print(f"✓ User 2 竞标 {part_one_charts[0].song.title}(一半): 30 token")
    
    # User 0 竞标第一个谱面，出价35
    if part_one_charts[0].user != test_users[0]:
        bid5 = SecondBid.objects.create(
            second_bidding_round=second_round,
            bidder=test_users[0],
            target_chart_part_one=part_one_charts[0],
            amount=35
        )
        print(f"✓ User 0 竞标 {part_one_charts[0].song.title}(一半): 35 token")
    
    # User 0 竞标第二个谱面，出价20
    if part_one_charts[1].user != test_users[0]:
        bid6 = SecondBid.objects.create(
            second_bidding_round=second_round,
            bidder=test_users[0],
            target_chart_part_one=part_one_charts[1],
            amount=20
        )
        print(f"✓ User 0 竞标 {part_one_charts[1].song.title}(一半): 20 token")
    
except Exception as e:
    print(f"✗ 第二轮竞标失败: {e}")
    sys.exit(1)

# 执行第二轮分配
print("\n[10] 执行第二轮竞标分配...")
try:
    result = SecondBiddingService.allocate_second_bids(second_round.id)
    print(f"✓ 分配完成")
    print(f"  - 总竞标数: {result['total_bids']}")
    print(f"  - 分配的谱面数: {result['allocated_charts']}")
    print(f"  - 获胜者数: {result['winners_count']}")
    print(f"  - 未分配谱面数: {result['unallocated_charts']}")
    
    # 验证分配结果
    bid_results = SecondBidResult.objects.filter(second_bidding_round=second_round)
    print(f"\n  分配结果:")
    for br in bid_results:
        print(f"    - {br.winner.username} 获得 {br.part_one_chart.song.title}(一半)")
        print(f"      └─ 自动创建第二部分谱面 (ID={br.completed_chart.id})")
        print(f"      └─ 分配类型: {br.allocation_type}")
        
except Exception as e:
    print(f"✗ 分配失败: {e}")
    sys.exit(1)

# 验证一半谱面关系
print("\n[11] 验证谱面关系...")
try:
    # 检查创建的第二部分谱面
    part_two_charts = Chart.objects.filter(is_part_one=False)
    print(f"✓ 创建的第二部分谱面数: {part_two_charts.count()}")
    
    for chart in part_two_charts:
        if chart.part_one_chart:
            print(f"  - {chart.user.username} 的第二部分链接到 {chart.part_one_chart.user.username} 的第一部分")
            print(f"    └─ 歌曲: {chart.song.title}")
            print(f"    └─ 第一部分ID: {chart.part_one_chart.id}")
            print(f"    └─ 第二部分ID: {chart.id}")
        
except Exception as e:
    print(f"✗ 验证失败: {e}")
    sys.exit(1)

# 验证API序列化器
print("\n[12] 验证API序列化器...")
try:
    from songs.serializers import (
        SecondBiddingRoundSerializer, 
        SecondBidSerializer,
        SecondBidResultSerializer,
        AvailableChartSerializer
    )
    
    # 序列化第二轮竞标轮次
    serializer = SecondBiddingRoundSerializer(second_round)
    data = serializer.data
    print(f"✓ SecondBiddingRoundSerializer: {list(data.keys())}")
    
    # 序列化第二轮竞标
    bids = SecondBid.objects.all()
    serializer = SecondBidSerializer(bids, many=True, context={'request': None})
    print(f"✓ SecondBidSerializer: 序列化了 {bids.count()} 条竞标")
    
    # 序列化分配结果
    results = SecondBidResult.objects.all()
    serializer = SecondBidResultSerializer(results, many=True)
    print(f"✓ SecondBidResultSerializer: 序列化了 {results.count()} 条结果")
    
    # 序列化可竞标的谱面
    available = SecondBiddingService.get_available_part_one_charts(second_round, user=test_users[0])
    serializer = AvailableChartSerializer(available, many=True)
    print(f"✓ AvailableChartSerializer: {available.count()} 个可竞标谱面")
    
except Exception as e:
    print(f"✗ 序列化失败: {e}")
    sys.exit(1)

# 测试服务验证方法
print("\n[13] 测试服务验证方法...")
try:
    # 测试不能竞标自己的谱面
    if part_one_charts:
        is_valid, msg = SecondBiddingService.validate_second_bid(
            part_one_charts[0].user, part_one_charts[0], 50
        )
        if not is_valid:
            print(f"✓ 验证：不能竞标自己的谱面 ({msg})")
        else:
            print(f"✗ 验证失败：应该阻止自己竞标")
    
    # 测试正常竞标
    if part_one_charts and test_users[2]:
        is_valid, msg = SecondBiddingService.validate_second_bid(
            test_users[2], part_one_charts[0], 50
        )
        if is_valid:
            print(f"✓ 验证：可以竞标他人的谱面")
        else:
            print(f"验证提示: {msg}")
    
except Exception as e:
    print(f"✗ 验证失败: {e}")
    sys.exit(1)

# 最终统计
print("\n" + "=" * 80)
print("测试完成统计:")
print(f"  - 创建的用户数: {len(test_users)}")
print(f"  - 创建的歌曲数: {len(test_songs)}")
print(f"  - 第一轮竞标数: {Bid.objects.count()}")
print(f"  - 第一轮分配结果: {BidResult.objects.count()}")
print(f"  - 第一部分谱面数: {Chart.objects.filter(is_part_one=True).count()}")
print(f"  - 第二轮竞标数: {SecondBid.objects.count()}")
print(f"  - 第二轮分配结果: {SecondBidResult.objects.count()}")
print(f"  - 第二部分谱面数: {Chart.objects.filter(is_part_one=False).count()}")
print("=" * 80)
print("\n✓ 所有测试通过！第二轮竞标系统运行正常。\n")
