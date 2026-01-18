#!/usr/bin/env python
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
django.setup()

from songs.models import BidResult, BiddingRound
from songs.serializers import BidResultSerializer

# 查找最新的谱面竞标轮次
chart_round = BiddingRound.objects.filter(bidding_type='chart').order_by('-created_at').first()
if not chart_round:
    print('没有谱面竞标轮次')
    exit()

print(f'轮次ID: {chart_round.id}, 状态: {chart_round.status}')
print()

# 获取该轮次的所有分配结果
results = BidResult.objects.filter(bidding_round=chart_round, bid_type='chart')
print(f'该轮次的谱面分配结果数: {results.count()}')
print()

for r in results:
    data = BidResultSerializer(r).data
    print('序列化后的 BidResult 数据:')
    print(json.dumps(data, indent=2, default=str))
    print()
