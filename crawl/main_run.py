# main_run.py

import pandas as pd
# ⭐️ 다른 파일에서 클래스를 import 합니다. ⭐️
from naver_crawler import NaverPlaceCrawler
from google_crawler import GoogleMapsCrawler

# 크롤링할 업체명 리스트
company_names = [
    # 스튜디오
    "더써드마인드스튜디오",
    "르노브",
    "메이브",
    "테오",
    "포에버마인",
    "줄리의정원",
    "603",
    "원규",
    "비마이스튜디오",
    "그가사랑하는순간",
    "오브라픽쳐스",
    "달빛스쿠터",
    "미유스튜디오",
    # 메이크업
    "아베끄바이분장",
    "설레임",
    "다온",
    "제니스뷰티",
    "소유",
    "더블로썸",
    "라엘",
    "더샵메이크업",
    # 수트
    "벨에포크",
    "카발레로",
    "루쏘소",
    "다나베옴므",
    "바스타레",
    "아르코발레로",
    "사프토리아 마스티오",
    # 드레스
    "브라이덜공",
    "엔조최재훈",
    "시작by이명순",
    "아틀리에쿠",
    "마인포시즌스",
    "정우웨딩",
    "로브드샤",
    "메리앤코",
    "라미엔 브라이드",
    "베일즈광주",
]
REGION = "광주"

all_results = []
naver_crawler = None
google_crawler = None

try:
    # 1. 네이버 플레이스 크롤링
    naver_crawler = NaverPlaceCrawler(headless=True)
    for name in company_names:
        data = naver_crawler.crawl(name, target_region=REGION)
        all_results.extend(data)
        
    # 2. 구글 맵 크롤링
    google_crawler = GoogleMapsCrawler(headless=True)
    for name in company_names:
        data = google_crawler.crawl(name)
        all_results.extend(data)

except Exception as e:
    print(f"\n[FATAL ERROR] 크롤링 중 치명적인 오류 발생: {e}")

finally:
    # 3. 브라우저 종료 및 자원 해제
    if naver_crawler:
        naver_crawler.close()
    if google_crawler:
        google_crawler.close()

# 4. 결과 출력 및 저장
if all_results:
    df = pd.DataFrame(all_results)
    print("\n\n=== 최종 크롤링 결과 ===")
    print(df)
    df.to_csv("place_crawl_results.csv", index=False, encoding='utf-8-sig')
    print("\n✅ 데이터를 place_crawl_results.csv에 저장했습니다.")