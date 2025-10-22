import time
import pandas as pd
import tempfile
import atexit
import shutil
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class GoogleMapsCrawler:
    def __init__(self, headless=True):
        """구글 맵 크롤러 초기화 (Naver와 동일한 설정 사용)"""
        options = webdriver.ChromeOptions()
        
        self.temp_dir = tempfile.mkdtemp()
        options.add_argument(f'--user-data-dir={self.temp_dir}')
        atexit.register(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))
        
        if headless:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def search_place(self, place_name):
        """구글 맵에서 장소 검색 및 상세 페이지 진입"""
        # 구글 맵의 검색 URL 구조는 안정적
        search_url = f"https://www.google.com/maps/search/{place_name}"
        self.driver.get(search_url)
        
        try:
            # 검색 결과를 기다립니다. (클릭 가능한 첫 번째 항목)
            first_result_link = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="main"] a[aria-label]'))
            )
            first_result_link.click()
            time.sleep(2) # 상세 페이지 로딩 대기
            
            return True
        except TimeoutException:
            print(f"   ❌ 장소 검색 결과가 없습니다: '{place_name}'")
            return False
        except Exception as e:
            print(f"   ❌ 구글 맵 검색 실패: {e}")
            return False

    def get_place_info(self):
        """업체 기본 정보 추출"""
        try:
            place_url = self.driver.current_url
            
            # 구글 맵의 CSS 선택자는 자주 바뀝니다. 현재 기준으로 작성합니다.
            name = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.DUwDvf.lfPIob'))).text
            
            # 주소는 특정 버튼 아래에 숨겨져 있거나, 여러 정보가 혼재되어 있을 수 있습니다.
            try: 
                address_element = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]')
                address = address_element.text
            except: 
                address = "주소 정보 없음"

            # 평점 및 리뷰 수
            try: 
                rating_text = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span.a3BCt').text
                review_count_text = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span.eR5EKb').text
                rating = rating_text.split()[0]
                # 예: "(300)" -> 300
                review_count = review_count_text.strip('()').replace(',', '') 
            except: 
                rating = "평점 없음"
                review_count = "0"

            return {
                '플랫폼': '구글 맵',
                '업체명': name,
                '평점': rating,
                '리뷰수': review_count,
                '주소': address,
                '출처_URL': place_url
            }
        except Exception as e:
            print(f"   ⚠️ 업체 정보 추출 실패: {e}")
            return None
            
    def crawl(self, place_name):
        """전체 프로세스 실행 및 데이터 반환"""
        print(f"\n🔍 [GOOGLE] '{place_name}' 크롤링 시작...")
        
        if not self.search_place(place_name):
            return []
        
        place_info = self.get_place_info()
        if not place_info:
            return []
        
        print(f"   📍 {place_info['업체명']} (평점: {place_info['평점']}, 주소: {place_info['주소']})")
        
        return [place_info] # 일단 기본 정보만 반환하도록 간소화
        
    def close(self):
        """브라우저 종료"""
        self.driver.quit()