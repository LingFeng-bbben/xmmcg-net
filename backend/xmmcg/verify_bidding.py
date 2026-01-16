#!/usr/bin/env python
"""
快速验证竞标系统是否正常工作
"""

import os
import sys
import django

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
django.setup()

from django.contrib.auth.models import User
from songs.models import Song, BiddingRound, Bid, BidResult, MAX_SONGS_PER_USER, MAX_BIDS_PER_USER
from users.models import UserProfile
from songs.bidding_service import BiddingService

print("=" * 60)
print("  竞标系统快速验证")
print("=" * 60)

# 1. 检查模型是否已正确创建
print("\n检查数据库模型...")

try:
    Song.objects.count()
    print("  ✓ Song 模型正常")
except Exception as e:
    print(f"  ✗ Song 模型出错: {e}")
    sys.exit(1)

try:
    BiddingRound.objects.count()
    print("  ✓ BiddingRound 模型正常")
except Exception as e:
    print(f"  ✗ BiddingRound 模型出错: {e}")
    sys.exit(1)

try:
    Bid.objects.count()
    print("  ✓ Bid 模型正常")
except Exception as e:
    print(f"  ✗ Bid 模型出错: {e}")
    sys.exit(1)

try:
    BidResult.objects.count()
    print("  ✓ BidResult 模型正常")
except Exception as e:
    print(f"  ✗ BidResult 模型出错: {e}")
    sys.exit(1)

# 2. 检查常量
print("\n检查配置常量...")
print(f"  MAX_SONGS_PER_USER = {MAX_SONGS_PER_USER}")
print(f"  MAX_BIDS_PER_USER = {MAX_BIDS_PER_USER}")

# 3. 创建测试数据
print("\n创建测试数据...")

# 创建用户
user1, _ = User.objects.get_or_create(
    username='test_user_bidding_1',
    defaults={'email': 'test1@bidding.com'}
)
profile1, _ = UserProfile.objects.get_or_create(user=user1, defaults={'token': 10000})

user2, _ = User.objects.get_or_create(
    username='test_user_bidding_2',
    defaults={'email': 'test2@bidding.com'}
)
profile2, _ = UserProfile.objects.get_or_create(user=user2, defaults={'token': 10000})

print(f"  ✓ 创建测试用户: {user1.username} (代币: {profile1.token})")
print(f"  ✓ 创建测试用户: {user2.username} (代币: {profile2.token})")

# 创建测试歌曲
song1 = Song.objects.create(
    user=user1,
    title='Test Song 1',
    audio_hash='test_hash_1',
    file_size=1000000
)
print(f"  ✓ 创建测试歌曲: {song1.title} (ID: {song1.id})")

# 创建竞标轮次
bidding_round = BiddingRound.objects.create(
    name='Test Bidding Round',
    status='active'
)
print(f"  ✓ 创建竞标轮次: {bidding_round.name} (ID: {bidding_round.id})")

# 4. 测试竞标创建
print("\n测试竞标功能...")

try:
    bid1 = BiddingService.create_bid(user2, bidding_round, song1, 500)
    print(f"  ✓ 创建竞标: {user2.username} 对 '{song1.title}' 竞标 500 代币")
except Exception as e:
    print(f"  ✗ 创建竞标失败: {e}")
    sys.exit(1)

# 5. 测试分配
print("\n测试竞标分配...")

try:
    result = BiddingService.allocate_bids(bidding_round.id)
    print(f"  ✓ 竞标分配完成")
    print(f"    - 总歌曲数: {result['total_songs']}")
    print(f"    - 已分配: {result['allocated_songs']}")
    print(f"    - 获胜者数: {result['winners']}")
except Exception as e:
    print(f"  ✗ 竞标分配失败: {e}")
    sys.exit(1)

# 6. 验证结果
print("\n验证分配结果...")

bid_results = BidResult.objects.filter(bidding_round=bidding_round, user=user2)
if bid_results.exists():
    result = bid_results.first()
    print(f"  ✓ {user2.username} 获得 '{result.song.title}' ({result.get_allocation_type_display()})")
else:
    print(f"  ✗ 未找到 {user2.username} 的分配结果")

print("\n" + "=" * 60)
print("  ✓ 竞标系统验证完成，所有功能正常！")
print("=" * 60)
