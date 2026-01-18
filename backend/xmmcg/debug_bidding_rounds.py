#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
django.setup()

from songs.models import BiddingRound, Bid, BidResult

# 查询所有谱面竞标轮次
print('===== 所有谱面竞标轮次 =====')
chart_rounds = BiddingRound.objects.filter(bidding_type='chart').order_by('-created_at')
for r in chart_rounds:
    bid_count = Bid.objects.filter(bidding_round=r, bid_type='chart').count()
    result_count = BidResult.objects.filter(bidding_round=r, bid_type='chart').count()
    print(f'轮次ID: {r.id}, 类型: {r.bidding_type}, 状态: {r.status}, Bid数: {bid_count}, Result数: {result_count}')

print()
print('===== 最新轮次的详细信息 =====')
if chart_rounds.exists():
    latest = chart_rounds.first()
    print(f'轮次ID: {latest.id}, 状态: {latest.status}')
    print()
    print('所有Bid:')
    bids = Bid.objects.filter(bidding_round=latest, bid_type='chart')
    for bid in bids:
        result = BidResult.objects.filter(bidding_round=latest, user=bid.user, bid_type='chart', chart=bid.chart).first()
        status = result.allocation_type if result else '无'
        print(f'  Bid ID: {bid.id}, 用户: {bid.user.username}, Chart: {bid.chart.id}, 结果: {status}')
else:
    print('没有谱面竞标轮次')
