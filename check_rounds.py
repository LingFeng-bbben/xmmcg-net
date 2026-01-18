#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
django.setup()

from songs.models import BiddingRound

print("=== 所有竞标轮次详情 ===")
for r in BiddingRound.objects.all():
    print(f"ID: {r.id} | 名称: {r.name}")
    print(f"  类型: {r.bidding_type} | 状态: {r.status}")
    print(f"  创建: {r.created_at} | 开始: {r.started_at} | 完成: {r.completed_at}")
    print()

print("=== 活跃的谱面竞标轮次 ===")
active_chart = BiddingRound.objects.filter(bidding_type='chart', status='active')
if active_chart.exists():
    for r in active_chart:
        print(f"✓ {r.id}. {r.name}")
else:
    print("✗ 未找到活跃的谱面竞标轮次")

print("\n=== 活跃的歌曲竞标轮次 ===")
active_song = BiddingRound.objects.filter(bidding_type='song', status='active')
if active_song.exists():
    for r in active_song:
        print(f"✓ {r.id}. {r.name}")
else:
    print("✗ 未找到活跃的歌曲竞标轮次")
