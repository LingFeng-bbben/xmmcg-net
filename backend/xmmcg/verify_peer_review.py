"""
Peer review system complete test script
Test all new API endpoints and business logic
"""

import os
import sys
import django

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from songs.models import (
    Song, BiddingRound, Bid, BidResult, Chart, 
    PeerReviewAllocation, PeerReview,
    PEER_REVIEW_TASKS_PER_USER, PEER_REVIEW_MAX_SCORE
)
from songs.bidding_service import BiddingService, PeerReviewService
from songs.serializers import (
    ChartSerializer, PeerReviewAllocationSerializer,
    PeerReviewSerializer, ChartDetailSerializer
)
import hashlib


def print_section(title):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def create_test_data():
    """创建测试数据"""
    print_section("Step 1: Create test data")
    
    # 创建8个用户（这样才能进行平衡分配）
    users = []
    for i in range(1, 9):
        user, created = User.objects.get_or_create(
            username=f'test_user_{i}',
            defaults={'email': f'user{i}@test.com'}
        )
        users.append(user)
        status = "created" if created else "exists"
        print(f"[OK] User {user.username} {status}")
    
    # 创建竞标轮次
    round_obj, created = BiddingRound.objects.get_or_create(
        name='Test Round',
        defaults={'status': 'active'}
    )
    status = "created" if created else "exists"
    print(f"[OK] Bidding Round {round_obj.name} {status}")
    
    # 创建歌曲
    songs_list = []
    for i, user in enumerate(users, 1):
        for j in range(1, 2):  # Each user uploads 1 song
            # 生成虚假的音频哈希
            audio_hash = hashlib.sha256(f'audio_{user.id}_{j}'.encode()).hexdigest()
            song, created = Song.objects.get_or_create(
                user=user,
                title=f'{user.username}_song_{j}',
                defaults={
                    'audio_file': f'songs/test_{user.id}_{j}.mp3',
                    'audio_hash': audio_hash,
                    'file_size': 5000000 + i * 1000000 + j * 100000,
                }
            )
            if created:
                songs_list.append(song)
                print(f"[OK] Song {song.title} created (ID: {song.id})")
            else:
                if song not in songs_list:
                    songs_list.append(song)
                print(f"[OK] Song {song.title} exists (ID: {song.id})")
    
    print(f"\nTotal: {len(users)} users, {len(songs_list)} songs")
    return users, round_obj, songs_list


def test_bidding_phase(users, round_obj, songs_list):
    """测试竞标阶段（第2-3阶段）"""
    print_section("Step 2: Test bidding and allocation")
    
    # 重置竞标轮次状态为active
    round_obj.status = 'active'
    round_obj.save()
    
    # 清空旧的竞标记录
    Bid.objects.filter(bidding_round=round_obj).delete()
    BidResult.objects.filter(bidding_round=round_obj).delete()
    
    # 创建竞标
    print("Creating bids...")
    bids_data = [
        (users[0], songs_list[1], 100),  
        (users[1], songs_list[0], 120),  
        (users[2], songs_list[1], 80),   
        (users[3], songs_list[2], 90),   
        (users[4], songs_list[3], 70),   
        (users[5], songs_list[4], 110),  
        (users[6], songs_list[5], 85),   
        (users[7], songs_list[0], 95),   
    ]
    
    for user, song, amount in bids_data:
        bid, created = Bid.objects.get_or_create(
            bidding_round=round_obj,
            user=user,
            song=song,
            defaults={'amount': amount}
        )
        if created:
            print(f"  [OK] {user.username} bid {song.title} ({amount} tokens)")
    
    # 执行分配
    print("\nExecuting allocation...")
    try:
        allocation_result = BiddingService.allocate_bids(round_obj.id)
        print(f"[OK] Allocation completed")
        print(f"  - Winners: {allocation_result.get('winners', 0)}")
        print(f"  - Total bidders: {allocation_result.get('total_bidders', 0)}")
        print(f"  - Allocated songs: {allocation_result.get('allocated_songs', 0)}")
        print(f"  - Unallocated songs: {allocation_result.get('unallocated_songs', 0)}")
    except Exception as e:
        print(f"[ERROR] Allocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 验证分配结果
    results = BidResult.objects.filter(bidding_round=round_obj)
    print(f"\nAllocation verification (total {results.count()}):")
    for result in results:
        print(f"  - {result.user.username} got {result.song.title}")
        print(f"    Type: {result.get_allocation_type_display()}, Price: {result.bid_amount}")
    
    return True


def test_chart_submission(users, round_obj):
    """Test chart submission phase"""
    print_section("Step 3: Test chart submission")
    
    # Clear old chart records
    Chart.objects.filter(bidding_round=round_obj).delete()
    
    results = BidResult.objects.filter(bidding_round=round_obj)
    charts_created = []
    
    print(f"Submitting charts for {results.count()} allocation results...")
    for result in results:
        chart, created = Chart.objects.get_or_create(
            bidding_round=round_obj,
            user=result.user,
            song=result.song,
            bid_result=result,
            defaults={
                'status': 'submitted',
                'chart_url': f'https://chart-server.com/charts/chart_{result.id}/maidata.txt',
                'chart_id_external': f'chart_{result.id}',
                'submitted_at': timezone.now(),
            }
        )
        if created:
            charts_created.append(chart)
            print(f"  [OK] {result.user.username} submitted chart for {result.song.title}")
    
    print(f"\n[OK] {len(charts_created)} charts submitted")
    
    # Verify chart information
    charts = Chart.objects.filter(bidding_round=round_obj)
    print(f"\nChart verification:")
    for chart in charts:
        print(f"  - Chart #{chart.id}: {chart.user.username} - {chart.song.title}")
        print(f"    URL: {chart.chart_url}")
        print(f"    Status: {chart.get_status_display()}")
    
    return charts


def test_peer_review_allocation(charts, round_obj):
    """测试互评分配阶段（第6阶段）"""
    print_section("Step 4: Test peer review allocation")
    
    # Convert to list to get length
    charts_list = list(charts)
    
    # 清空旧的分配记录
    PeerReviewAllocation.objects.filter(bidding_round=round_obj).delete()
    PeerReview.objects.filter(bidding_round=round_obj).delete()
    
    print(f"Allocating peer review tasks for {len(charts_list)} charts...")
    print(f"Requirements: 8 reviews per chart, 8 tasks per reviewer\n")
    
    try:
        allocation_result = PeerReviewService.allocate_peer_reviews(round_obj.id)
        print(f"[OK] Allocation successful!")
        print(f"  - Total allocations: {allocation_result['total_allocations']}")
        print(f"  - Charts: {allocation_result['charts_count']}")
        print(f"  - Reviewers: {allocation_result['reviewers_count']}")
        print(f"  - Reviews per chart: {allocation_result['reviews_per_chart']}")
        print(f"  - Tasks per reviewer: {allocation_result['tasks_per_reviewer']}")
    except Exception as e:
        print(f"[ERROR] Allocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify allocations
    allocations = PeerReviewAllocation.objects.filter(bidding_round=round_obj)
    print(f"\nAllocation verification (total {allocations.count()} records):")
    
    # Count per chart and reviewer
    chart_counts = {}
    reviewer_counts = {}
    for alloc in allocations:
        chart_counts[alloc.chart_id] = chart_counts.get(alloc.chart_id, 0) + 1
        reviewer_counts[alloc.reviewer_id] = reviewer_counts.get(alloc.reviewer_id, 0) + 1
    
    # Verify balance
    chart_counts_list = list(chart_counts.values())
    reviewer_counts_list = list(reviewer_counts.values())
    
    print(f"  - Reviews per chart: {set(chart_counts_list)}")
    print(f"    (Should all be {PEER_REVIEW_TASKS_PER_USER})")
    print(f"  - Tasks per reviewer: {set(reviewer_counts_list)}")
    print(f"    (Should all be {PEER_REVIEW_TASKS_PER_USER})")
    
    if all(c == PEER_REVIEW_TASKS_PER_USER for c in chart_counts_list):
        print(f"  [OK] Chart review count balance verified!")
    else:
        print(f"  [ERROR] Chart review counts not balanced!")
        return False
    
    if all(r == PEER_REVIEW_TASKS_PER_USER for r in reviewer_counts_list):
        print(f"  [OK] Reviewer task count balance verified!")
    else:
        print(f"  [ERROR] Reviewer task counts not balanced!")
        return False
    
    # Verify no self-review
    print(f"\nVerifying self-review prevention:")
    for alloc in allocations:
        if alloc.reviewer_id == alloc.chart.user_id:
            print(f"  [ERROR] Self-review found: {alloc.reviewer.username} reviews own chart")
            return False
    print(f"  [OK] No self-review found")
    
    return True


def test_peer_review_submission(round_obj):
    """Test peer review submission phase"""
    print_section("Step 5: Test peer review submission")
    
    # Get all pending allocations
    allocations = PeerReviewAllocation.objects.filter(
        bidding_round=round_obj,
        status='pending'
    )[:5]  # Test only first 5
    
    print(f"Testing submission of {len(allocations)} reviews...\n")
    
    for alloc in allocations:
        score = (hash(alloc.id) % (PEER_REVIEW_MAX_SCORE + 1))  # Random score
        comment = f"Test comment - {alloc.id}"
        
        try:
            review = PeerReviewService.submit_peer_review(alloc.id, score, comment)
            print(f"[OK] {alloc.reviewer.username} gave score {score} to {alloc.chart.user.username}")
            
            # Verify chart review stats
            chart = alloc.chart
            chart.refresh_from_db()
            print(f"    Chart reviews: {chart.review_count}/8, Average: {chart.average_score:.1f}")
        except Exception as e:
            print(f"[ERROR] Submission failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # View reviews for one chart (anonymous)
    chart = allocations[0].chart
    reviews = PeerReview.objects.filter(chart=chart)
    print(f"\nReviews for chart {chart.id} (anonymous):")
    for review in reviews:
        print(f"  - Score: {review.score}, Comment: {review.comment}")
    
    return True


def test_rankings(round_obj):
    """Test ranking generation"""
    print_section("Step 6: Test ranking generation")
    
    charts = Chart.objects.filter(
        bidding_round=round_obj,
        review_count__gt=0
    ).order_by('-average_score', '-total_score')
    
    print(f"Ranking information (based on available reviews):\n")
    for idx, chart in enumerate(charts[:10], 1):
        print(f"  {idx}. {chart.user.username} - {chart.song.title}")
        print(f"     Average: {chart.average_score:.1f}, Total: {chart.total_score}, Reviews: {chart.review_count}")
    
    return True


def test_serializers():
    """Test serializers"""
    print_section("Step 7: Test serializers")
    
    # Get test objects
    chart = Chart.objects.first()
    if not chart:
        print("[ERROR] No chart objects for testing")
        return False
    
    try:
        # Test ChartSerializer
        serializer = ChartSerializer(chart)
        print("[OK] ChartSerializer validated")
        print(f"  Sample data: {serializer.data}")
    except Exception as e:
        print(f"[ERROR] ChartSerializer failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        # Test ChartDetailSerializer
        serializer = ChartDetailSerializer(chart)
        print("[OK] ChartDetailSerializer validated")
    except Exception as e:
        print(f"[ERROR] ChartDetailSerializer failed: {e}")
        return False
    
    # Test PeerReviewAllocation
    alloc = PeerReviewAllocation.objects.first()
    if alloc:
        try:
            serializer = PeerReviewAllocationSerializer(alloc)
            print("[OK] PeerReviewAllocationSerializer validated")
        except Exception as e:
            print(f"[ERROR] PeerReviewAllocationSerializer failed: {e}")
            return False
    
    return True


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print("         Peer Review System Complete Test")
    print("=" * 60)
    
    try:
        # Step 1: Create test data
        users, round_obj, songs_list = create_test_data()
        
        # Step 2: Test bidding and allocation
        if not test_bidding_phase(users, round_obj, songs_list):
            print("\n[ERROR] Bidding phase test failed")
            return False
        
        # Step 3: Test chart submission
        charts = test_chart_submission(users, round_obj)
        if not charts:
            print("\n[ERROR] Chart submission test failed")
            return False
        
        # Step 4: Test peer review allocation
        if not test_peer_review_allocation(charts, round_obj):
            print("\n[ERROR] Peer review allocation test failed")
            return False
        
        # Step 5: Test peer review submission
        if not test_peer_review_submission(round_obj):
            print("\n[ERROR] Peer review submission test failed")
            return False
        
        # Step 6: Test ranking
        if not test_rankings(round_obj):
            print("\n[ERROR] Ranking test failed")
            return False
        
        # Step 7: Test serializers
        if not test_serializers():
            print("\n[ERROR] Serializer test failed")
            return False
        
        # SUCCESS!
        print_section("[OK] All tests passed!")
        print("\nTest Summary:")
        print(f"  - [OK] Create test data")
        print(f"  - [OK] Bidding and allocation")
        print(f"  - [OK] Chart submission")
        print(f"  - [OK] Peer review allocation (balance verification)")
        print(f"  - [OK] Peer review submission")
        print(f"  - [OK] Ranking generation")
        print(f"  - [OK] Serializers")
        print("\nPeer review system is ready!")
        return True
        
    except Exception as e:
        print_section("[ERROR] Test interrupted")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
