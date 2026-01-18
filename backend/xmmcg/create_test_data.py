#!/usr/bin/env python
"""
完整测试数据生成脚本
创建用户、歌曲、竞标轮次、竞标、谱面等测试数据

使用方法:
python create_test_data.py
"""

import os
import sys
import django
from pathlib import Path

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from songs.models import (
    Song, BiddingRound, Bid, BidResult, Chart, 
    CompetitionPhase, MAX_SONGS_PER_USER, MAX_BIDS_PER_USER
)
from songs.bidding_service import BiddingService
from django.core.files.base import ContentFile
import random

User = get_user_model()

def print_header(text):
    """打印标题"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")

def create_users(count=10):
    """创建测试用户"""
    print_header(f"创建 {count} 个测试用户")
    
    users = []
    for i in range(1, count + 1):
        username = f'testuser{i:02d}'
        
        # 删除已存在的用户
        User.objects.filter(username=username).delete()
        
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='password123'
        )
        # 设置初始代币
        user.token = 100
        user.save()
        
        users.append(user)
        print(f"✓ 创建用户: {username} (初始代币: 100)")
    
    return users

def create_songs(users):
    """为用户创建歌曲"""
    print_header("创建测试歌曲")
    
    song_titles = [
        "星空下的约定", "夏日海风", "雨夜思念", "晨曦之光",
        "梦想起航", "时光列车", "心跳节奏", "银河漫步",
        "樱花雨", "午夜狂想曲", "彩虹之约", "月光奏鸣曲",
        "破晓时分", "星空下的约定", "夏日海风", "永恒瞬间"  # 后面加入重复标题
    ]
    
    songs = []
    song_index = 0
    
    # 每个用户上传1-2首歌曲
    for user in users[:8]:  # 只让前8个用户上传歌曲
        num_songs = random.randint(1, MAX_SONGS_PER_USER)
        
        for _ in range(num_songs):
            if song_index >= len(song_titles):
                break
                
            title = song_titles[song_index]
            song_index += 1
            
            # 创建虚拟音频文件
            audio_content = b'fake audio data'
            audio_file = ContentFile(audio_content, name=f'{title}.mp3')
            
            song = Song.objects.create(
                user=user,
                title=title,
                audio_file=audio_file,
                file_size=len(audio_content)  # 设置文件大小
            )
            songs.append(song)
            print(f"✓ {user.username} 上传歌曲: {title}")
    
    return songs

def create_bidding_round_and_bids(users, songs):
    """创建第一轮竞标（歌曲竞标）"""
    print_header("创建第一轮竞标（歌曲竞标）")
    
    # 创建竞标轮次
    now = timezone.now()
    bidding_round = BiddingRound.objects.create(
        name="第一轮歌曲竞标",
        bidding_type='song',
        status='active',
        started_at=now
    )
    print(f"✓ 创建竞标轮次: {bidding_round.name}")
    
    # 为每个用户创建竞标
    bids_created = 0
    for user in users:
        # 随机选择3-5首歌曲竞标
        num_bids = random.randint(3, min(MAX_BIDS_PER_USER, len(songs)))
        selected_songs = random.sample(songs, num_bids)
        
        for song in selected_songs:
            # 随机竞标金额 10-50
            amount = random.randint(10, 50)
            
            bid = Bid.objects.create(
                user=user,
                bidding_round=bidding_round,
                bid_type='song',
                song=song,
                amount=amount
            )
            bids_created += 1
            print(f"  • {user.username} 竞标 '{song.title}' - {amount} Token")
    
    print(f"\n✓ 总共创建 {bids_created} 个竞标")
    return bidding_round

def allocate_first_round(bidding_round):
    """分配第一轮竞标结果"""
    print_header("分配第一轮竞标结果")
    
    try:
        results = BiddingService.allocate_bids(bidding_round.id)
        
        print(f"✓ 分配完成:")
        if isinstance(results, dict):
            print(f"  - 成功分配: {results.get('allocated_count', 0)} 个")
            print(f"  - 失败竞标: {results.get('failed_count', 0)} 个")
        else:
            print(f"  - 分配结果: {results}")
        
        # 显示中标结果
        print("\n中标结果:")
        bid_results = BidResult.objects.filter(
            bidding_round=bidding_round,
            bid_type='song'
        ).select_related('user', 'song')
        
        for result in bid_results:
            print(f"  ✓ {result.user.username} 中标 '{result.song.title}' (支付 {result.bid_amount} Token)")
        
        if not bid_results:
            print("  (无中标结果)")
            
        return bid_results
        
    except Exception as e:
        print(f"✗ 分配失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 仍然返回现有的中标结果
        bid_results = BidResult.objects.filter(
            bidding_round=bidding_round,
            bid_type='song'
        ).select_related('user', 'song')
        return bid_results

def create_charts(bid_results):
    """为中标用户创建谱面"""
    print_header("创建半成品谱面")
    
    charts = []
    for i, result in enumerate(bid_results[:6]):  # 只让前6个中标者提交谱面
        # 创建虚拟谱面文件
        maidata_content = f"""&title={result.song.title}
&des=Testuser{i+1:02d}
&lv_1=1
&lv_2=3
&lv_3=5
&lv_4=7

E_00000000
""".encode('utf-8')
        
        chart_file = ContentFile(maidata_content, name='maidata.txt')
        audio_file = ContentFile(b'fake audio', name='track.mp3')
        cover_file = ContentFile(b'fake image', name='bg.jpg')
        
        chart = Chart.objects.create(
            bidding_round=result.bidding_round,
            user=result.user,
            song=result.song,
            bid_result=result,
            status='part_submitted',
            designer=f'Testuser{i+1:02d}',
            chart_file=chart_file,
            audio_file=audio_file,
            cover_image=cover_file,
            submitted_at=timezone.now()
        )
        charts.append(chart)
        print(f"✓ {result.user.username} 提交谱面: {result.song.title} (半成品)")
    
    return charts

def create_second_bidding_round(charts, users):
    """创建第二轮竞标（谱面竞标）"""
    print_header("创建第二轮竞标（谱面竞标）")
    
    # 检查是否有谱面可竞标
    if not charts:
        print("⚠ 没有谱面可竞标，跳过第二轮竞标创建")
        return None
    
    # 创建第二轮竞标轮次
    now = timezone.now()
    bidding_round = BiddingRound.objects.create(
        name="第二轮谱面竞标",
        bidding_type='chart',
        status='active',
        started_at=now
    )
    print(f"✓ 创建竞标轮次: {bidding_round.name}")
    
    # 为每个用户创建谱面竞标
    bids_created = 0
    for user in users:
        # 过滤出不是该用户的谱面
        available_charts = [c for c in charts if c.user != user]
        
        if not available_charts:
            continue
        
        # 随机选择2-3个半成品谱面竞标
        num_bids = random.randint(2, min(3, len(available_charts)))
        selected_charts = random.sample(available_charts, num_bids)
        
        for chart in selected_charts:
            # 随机竞标金额 5-30
            amount = random.randint(5, 30)
            
            bid = Bid.objects.create(
                user=user,
                bidding_round=bidding_round,
                bid_type='chart',
                chart=chart,
                amount=amount
            )
            bids_created += 1
            print(f"  • {user.username} 竞标谱面 '{chart.song.title}' (by {chart.designer}) - {amount} Token")
    
    print(f"\n✓ 总共创建 {bids_created} 个谱面竞标")
    return bidding_round

def allocate_second_round(bidding_round):
    """分配第二轮竞标结果"""
    print_header("分配第二轮竞标结果")
    
    try:
        results = BiddingService.allocate_bids(bidding_round.id)
        
        print(f"✓ 分配完成:")
        if isinstance(results, dict):
            print(f"  - 成功分配: {results.get('allocated_count', 0)} 个")
            print(f"  - 失败竞标: {results.get('failed_count', 0)} 个")
        else:
            print(f"  - 分配结果: {results}")
        
        # 显示中标结果
        print("\n中标结果:")
        bid_results = BidResult.objects.filter(
            bidding_round=bidding_round,
            bid_type='chart'
        ).select_related('user', 'chart', 'chart__song')
        
        for result in bid_results:
            print(f"  ✓ {result.user.username} 中标谱面 '{result.chart.song.title}' (支付 {result.bid_amount} Token)")
        
        if not bid_results:
            print("  (无中标结果)")
            
        return bid_results
        
    except Exception as e:
        print(f"✗ 分配失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 仍然返回现有的中标结果
        bid_results = BidResult.objects.filter(
            bidding_round=bidding_round,
            bid_type='chart'
        ).select_related('user', 'chart', 'chart__song')
        return bid_results

def create_final_charts(bid_results):
    """为第二轮中标用户创建完成稿"""
    print_header("创建完成稿谱面")
    
    charts = []
    for i, result in enumerate(bid_results[:3]):  # 只让前3个提交完成稿
        # 获取原来的半成品谱面
        original_chart = result.chart
        
        # 创建虚拟完成稿文件
        maidata_content = f"""&title={result.chart.song.title}
&des={result.user.username}
&lv_1=2
&lv_2=5
&lv_3=8
&lv_4=10
&lv_5=12

E_00000000
T_11111111
""".encode('utf-8')
        
        chart_file = ContentFile(maidata_content, name='maidata.txt')
        audio_file = ContentFile(b'fake audio final', name='track.mp3')
        cover_file = ContentFile(b'fake image final', name='bg.jpg')
        
        chart = Chart.objects.create(
            bidding_round=result.bidding_round,
            user=result.user,
            song=result.chart.song,
            bid_result=None,  # 完成稿不关联第一轮的bid_result
            completion_bid_result=result,  # 关联第二轮的bid_result
            status='final_submitted',
            designer=result.user.username,
            chart_file=chart_file,
            audio_file=audio_file,
            cover_image=cover_file,
            submitted_at=timezone.now(),
            is_part_one=False,  # 这是第二部分/完成稿
            part_one_chart=original_chart  # 指向原来的半成品谱面
        )
        charts.append(chart)
        print(f"✓ {result.user.username} 提交谱面: {result.chart.song.title} (完成稿，基于 {original_chart.designer} 的半成品)")
    
    return charts

def create_competition_phases():
    """创建比赛阶段"""
    print_header("创建比赛阶段")
    
    now = timezone.now()
    
    phases = [
        {
            'name': '歌曲上传期',
            'phase_key': 'song_upload',
            'start_time': now - timedelta(days=30),
            'end_time': now - timedelta(days=20),
            'page_access': {
                'home': True,
                'songs': True,
                'charts': False,
                'profile': True
            }
        },
        {
            'name': '第一轮竞标期',
            'phase_key': 'first_bidding',
            'start_time': now - timedelta(days=20),
            'end_time': now - timedelta(days=10),
            'page_access': {
                'home': True,
                'songs': True,
                'charts': False,
                'profile': True
            }
        },
        {
            'name': '制谱期',
            'phase_key': 'mapping',
            'start_time': now - timedelta(days=10),
            'end_time': now + timedelta(days=5),
            'page_access': {
                'home': True,
                'songs': True,
                'charts': True,
                'profile': True
            }
        },
        {
            'name': '第二轮竞标期',
            'phase_key': 'second_bidding',
            'start_time': now + timedelta(days=5),
            'end_time': now + timedelta(days=15),
            'page_access': {
                'home': True,
                'songs': True,
                'charts': True,
                'profile': True
            }
        }
    ]
    
    for phase_data in phases:
        # 使用 get_or_create 避免重复
        phase, created = CompetitionPhase.objects.get_or_create(
            phase_key=phase_data['phase_key'],
            defaults={
                'name': phase_data['name'],
                'start_time': phase_data['start_time'],
                'end_time': phase_data['end_time'],
                'is_active': True,
                'page_access': phase_data['page_access']
            }
        )
        if created:
            print(f"✓ 创建阶段: {phase.name} ({phase.status})")
        else:
            print(f"~ 阶段已存在: {phase.name} ({phase.status})")

def print_summary():
    """打印数据统计"""
    print_header("测试数据统计")
    
    print(f"用户总数: {User.objects.count()}")
    print(f"歌曲总数: {Song.objects.count()}")
    print(f"竞标轮次: {BiddingRound.objects.count()}")
    print(f"  - 歌曲竞标轮次: {BiddingRound.objects.filter(bidding_type='song').count()}")
    print(f"  - 谱面竞标轮次: {BiddingRound.objects.filter(bidding_type='chart').count()}")
    print(f"竞标总数: {Bid.objects.count()}")
    print(f"  - 歌曲竞标: {Bid.objects.filter(bid_type='song').count()}")
    print(f"  - 谱面竞标: {Bid.objects.filter(bid_type='chart').count()}")
    print(f"中标结果: {BidResult.objects.count()}")
    print(f"  - 歌曲中标: {BidResult.objects.filter(bid_type='song').count()}")
    print(f"  - 谱面中标: {BidResult.objects.filter(bid_type='chart').count()}")
    print(f"谱面总数: {Chart.objects.count()}")
    print(f"  - 半成品: {Chart.objects.filter(status='part_submitted').count()}")
    print(f"  - 完成稿: {Chart.objects.filter(status='final_submitted').count()}")
    print(f"比赛阶段: {CompetitionPhase.objects.count()}")

def main():
    """主函数"""
    print_header("开始创建测试数据")
    
    # 清理旧数据
    print("清理旧数据...")
    Bid.objects.all().delete()
    BidResult.objects.all().delete()
    Chart.objects.all().delete()
    BiddingRound.objects.all().delete()
    Song.objects.all().delete()
    print("✓ 旧数据已清理\n")
    
    # 1. 创建用户
    users = create_users(10)
    
    # 2. 创建歌曲
    songs = create_songs(users)
    
    # 3. 创建第一轮竞标
    first_round = create_bidding_round_and_bids(users, songs)
    
    # 4. 分配第一轮竞标
    first_results = allocate_first_round(first_round)
    
    # 5. 创建半成品谱面
    part_charts = create_charts(first_results)
    
    # 6. 创建第二轮竞标
    second_round = create_second_bidding_round(part_charts, users)
    
    # 7. 分配第二轮竞标（如果有第二轮）
    second_results = []
    if second_round:
        second_results = allocate_second_round(second_round)
    
    # 8. 创建完成稿谱面
    if second_results:
        final_charts = create_final_charts(second_results)
    
    # 9. 创建比赛阶段
    create_competition_phases()
    
    # 10. 打印统计
    print_summary()
    
    print_header("测试数据创建完成！")
    print("现在可以访问前端查看数据:")
    print("  - http://localhost:5173")
    print("\n测试账号:")
    print("  用户名: testuser01 ~ testuser10")
    print("  密码: password123")

if __name__ == '__main__':
    main()
