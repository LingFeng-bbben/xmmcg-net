#!/usr/bin/env python
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
django.setup()

from songs.models import Bid, BiddingRound
from songs.serializers import BidSerializer
from django.contrib.auth.models import User

# 查找最新的谱面竞标轮次
chart_round = BiddingRound.objects.filter(bidding_type='chart').order_by('-created_at').first()
if not chart_round:
    print('没有谱面竞标轮次')
    exit()

print(f'轮次ID: {chart_round.id}, 状态: {chart_round.status}')
print()

# 获取该轮次的所有竞标
bids = Bid.objects.filter(bidding_round=chart_round, bid_type='chart')
print(f'该轮次的谱面竞标数: {bids.count()}')
print()

for bid in bids:
    print(f'Bid ID: {bid.id}')
    # 序列化
    serialized = BidSerializer(bid).data
    print('序列化后的数据:')
    print(json.dumps(serialized, indent=2, default=str))
    print()
