import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any

class NaverPlaceCrawler:
    """
    네이버 플레이스 크롤러: 검색/진입 후, JSON 요약 정보와 함께 방문자 리뷰 내용을 추출합니다.
    """
    def __init__(self, headless=True):
        self.options = webdriver.ChromeOptions()
        if headless:
            # 브라우저 창을 띄우지 않고 백그라운드에서 실행
            self.options.add_argument('headless')
            self.options.add_argument('window-size=1920x1080')
            
        self.options.add_argument('disable-gpu')
        self.options.add_argument('lang=ko_KR')
        self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36')
        
        # Chrome Driver 자동 설치 및 서비스 시작
        # NOTE: 이 코드는 실행 환경에 Chrome과 인터넷 연결이 필요합니다.
        self.service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        
        # 명시적 대기 설정
        self.wait = WebDriverWait(self.driver, 10)
        
    def close(self):
        """명시적으로 웹 드라이버를 종료하는 메서드"""
        try:
            self.driver.quit()
        except Exception as e:
            print(f"   ⚠️ 드라이버 종료 중 오류 발생: {e}")

    def __del__(self: object) -> None:
        """클래스 소멸 시 드라이버 종료"""
        try:
            self.driver.quit()
        except:
            pass

    def crawl(self, place_name, target_region, max_reviews=500):
        """전체 크롤링 프로세스 실행: 검색 -> 상세 정보 추출 -> 리뷰 수집"""
        print(f"\n🔍 [NAVER] '{target_region} {place_name}' 크롤링 시작...")
        
        # 1. 장소 검색 및 상세 페이지 진입
        if not self.search_place(place_name, target_region):
            return []
        
        # 2. 상세 페이지 요약 정보 추출 (JSON 실패 시 CSS 수동 추출로 변경)
        summary_data = self.get_place_info(target_region)
        
        if not summary_data:
            # 수동 추출도 실패하면 크롤링 중단
            print("   ❌ 상세 정보 수동 추출에도 실패했습니다. 크롤링을 중단합니다.")
            return []
        
        # 3. 개별 리뷰 내용 추출 (평점 및 텍스트)
        reviews = self._extract_visitor_reviews(max_reviews)
        
        if not reviews:
            print("   ℹ️ 추출된 개별 리뷰 내용이 없습니다.")
            return []
            
        # 4. 결과 통합 (업체 정보 + 개별 리뷰)
        final_results = []
        for review in reviews:
            # 개별 리뷰 데이터에 요약 정보를 합칩니다.
            result = summary_data.copy()
            result.update(review)
            final_results.append(result)
        
        print(f"   ✅ 최종 데이터 추출 완료: {summary_data['업체명']}, 수집 리뷰수: {len(final_results)}개")
        return final_results

    def search_place(self, place_name, target_region):
        """네이버에서 장소 검색 후, 해당 지역 업체의 상세 페이지로 진입"""
        
        full_search_query = f"{target_region} {place_name}"
        search_url = f"https://map.naver.com/p/search/{full_search_query}"
        self.driver.get(search_url)
        
        # 3초 대기: URL이 검색 결과 또는 상세 페이지로 변경되는 시간 확보
        time.sleep(3) 

        # 1. 상세 페이지(entryIframe)로 바로 진입 시도 (가장 흔한 경우)
        try:
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it('entryIframe')
            )
            print("   ℹ️ 상세 페이지로 바로 진입했습니다. (entryIframe)")
            return True

        except TimeoutException:
            # entryIframe 진입 실패 -> 검색 결과 리스트 페이지에 머물러 있는 경우
            print("   ℹ️ 상세 정보 iframe 진입 실패. 검색 결과 리스트 페이지를 확인합니다.")

            try:
                # 2. 검색 결과 리스트 iframe으로 전환
                self.driver.switch_to.default_content() # 메인 페이지로 돌아와서

                # 최신 검색 결과 iframe selector (title="search result" 사용)
                search_iframe_selector = (By.CSS_SELECTOR, 'iframe[title*="search result"]')
                
                self.wait.until(
                    EC.frame_to_be_available_and_switch_to_it(search_iframe_selector)
                )

                # 리스트 아이템을 찾아 첫 번째 '광주' 업체를 클릭
                # ⚠️ 네이버 구조 변경 시 가장 먼저 확인해야 하는 부분입니다.
                result_item_selector = 'li.UEEoT' 
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, result_item_selector))
                )

                items = self.driver.find_elements(By.CSS_SELECTOR, result_item_selector)
                
                for item in items:
                    try:
                        name_link = item.find_element(By.CSS_SELECTOR, 'a.place_bluelink')
                        address_text = item.find_element(By.CSS_SELECTOR, 'div.O0pIe').text
                        
                        # ⭐️ 지역 필터링
                        if address_text.startswith(target_region):
                            print(f"   ✅ 리스트에서 '{target_region}' 업체 확인 후 클릭: {name_link.text}")
                            name_link.click()
                            time.sleep(2) # 클릭 후 URL이 변경되기를 기다림

                            # 다시 default_content로 돌아가서 entryIframe으로 전환
                            self.driver.switch_to.default_content() 
                            self.wait.until(EC.frame_to_be_available_and_switch_to_it('entryIframe'))
                            return True
                            
                    except NoSuchElementException:
                        continue 
                        
                print(f"   ❌ 리스트에서 '{target_region}' 주소를 가진 업체를 찾을 수 없습니다.")
                return False 
                
            except TimeoutException:
                print("   ❌ 검색 결과 리스트 로딩 실패. CSS 선택자 또는 검색어를 확인해주세요.")
                return False
                
            except Exception as e:
                print(f"   ❌ 리스트 페이지 처리 중 예상치 못한 오류 발생: {e}")
                return False
            
        except Exception as e:
            print(f"   ❌ 장소 검색 또는 iframe 전환 실패: Message: {e}")
            return False

    def get_place_info(self, target_region): 
        """
        JSON 추출 실패로 인해 CSS 선택자를 이용해 업체 상세 정보를 수동으로 파싱하도록 로직 변경.
        (Place ID 추출 로직을 추가하여 안정성 향상)
        """
        
        # 1. Place ID 추출 (JSON/CSS 추출과 관계없이 URL에서 먼저 추출 시도)
        self.driver.switch_to.default_content()
        current_url = self.driver.current_url
        
        place_id = 'ID 추출 실패'
        # URL에서 place ID 추출 로직 (예: /place/12345678?...)
        try:
            if '/place/' in current_url:
                start_index = current_url.find('/place/') + len('/place/')
                end_index = current_url.find('?', start_index)
                if end_index == -1: # ?가 없는 경우
                    end_index = len(current_url)
                place_id = current_url[start_index:end_index].strip('/')
        except Exception:
            pass # ID 추출 실패는 무시하고 진행
            
        # entryIframe으로 복귀
        try:
             self.wait.until(EC.frame_to_be_available_and_switch_to_it('entryIframe'))
        except:
             print("   ⚠️ Place ID 추출 후 entryIframe 복귀 실패. 수동 추출을 시도합니다.")
             
        
        # 2. JSON 추출 시도
        try:
            self.driver.switch_to.default_content()
            apollo_state_json = self.driver.execute_script("return window.__APOLLO_STATE__;")
            self.wait.until(EC.frame_to_be_available_and_switch_to_it('entryIframe')) # 복귀
            
            if apollo_state_json:
                place_key = next((k for k in apollo_state_json if k.startswith("PlaceDetailBase:")), None)
                if place_key:
                    place_data = apollo_state_json[place_key]
                    print("   ✅ 상세 정보 JSON 추출 성공.")
                    return {
                        '플랫폼': '네이버 플레이스',
                        '업체명': place_data.get('name', '업체명 없음'),
                        '주소': place_data.get('roadAddress', '주소 정보 없음'),
                        '평점(방문자)_총점': place_data.get('visitorReviewsScore', '평점 없음'),
                        '리뷰수(방문자)_총개': place_data.get('visitorReviewsTotal', 0),
                        '출처_URL': current_url,
                        'Place_ID': place_id 
                    }
            # JSON 추출에 실패했거나 데이터가 없는 경우, 아래 수동 추출 로직으로 넘어감
            print("   ⚠️ JSON 추출 실패. CSS 선택자를 이용한 수동 추출을 시도합니다.")

        except Exception as e:
            # JSON 시도 중 오류가 발생했더라도, 아래 수동 추출 로직을 시도하기 위해 예외를 무시하고 진행
            print(f"   ⚠️ JSON 정보 추출 중 예외 발생: {e}")
            
            # JSON 시도 후 default_content로 나가있을 수 있으므로 다시 entryIframe으로 복귀 시도
            self.driver.switch_to.default_content()
            try:
                 self.wait.until(EC.frame_to_be_available_and_switch_to_it('entryIframe'))
            except:
                 pass
            
        # --- 3. CSS 선택자를 이용한 수동 정보 추출 ---
        try:
            # 현재 프레임이 entryIframe인지 확인하고 전환 (2단계에서 이미 시도했으므로 빠르게 진행)
            self.driver.switch_to.default_content()
            self.wait.until(EC.frame_to_be_available_and_switch_to_it('entryIframe'))
            
            # 1. 업체명 추출
            # ⚠️ 업체명 선택자 (h1 태그)
            name_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.Fc1rA')))
            name = name_element.text
            
            # 2. 주소 추출
            # ⚠️ 주소 선택자
            address_element = self.driver.find_element(By.CSS_SELECTOR, 'span.addr')
            road_address = address_element.text
            
            # 3. 평점(총점) 및 리뷰 개수 추출
            # ⚠️ 평점 컨테이너 선택자
            score_container_element = self.driver.find_element(By.CSS_SELECTOR, '.PXMot')
            
            # 평점 총점 추출 (aria-label 사용)
            score_text = score_container_element.find_element(By.CSS_SELECTOR, '._3t1yS > em').text
            visitor_reviews_score = score_text if score_text else '평점 없음'

            # 리뷰 개수 추출 (텍스트에서 숫자만 추출)
            reviews_text = score_container_element.find_element(By.CSS_SELECTOR, '.PXMot > a:nth-child(2) > span:nth-child(1)').text
            # '방문자 리뷰 1,234' -> '1,234' -> 1234
            visitor_reviews_total = int(reviews_text.replace('방문자 리뷰', '').strip().replace(',', '')) if reviews_text else 0
            
            # 4. 주소 필터링 (최종 확인)
            if not road_address.startswith(target_region):
                print(f"   ❌ 추출된 주소({road_address})가 요청 지역({target_region})과 일치하지 않습니다.")
                return None

            # 5. 결과 반환
            print("   ✅ 상세 정보 CSS 수동 추출 성공.")
            return {
                '플랫폼': '네이버 플레이스',
                '업체명': name,
                '주소': road_address,
                '평점(방문자)_총점': visitor_reviews_score,
                '리뷰수(방문자)_총개': visitor_reviews_total,
                '출처_URL': current_url,
                'Place_ID': place_id 
            }

        except Exception as e:
            print(f"   ❌ 상세 정보 수동 추출 실패. CSS 선택자를 다시 확인해야 합니다. 오류: {e}")
            return None


    def _extract_visitor_reviews(self, max_reviews: int) -> List[Dict[str, Any]]:
        """entryIframe 내부에서 방문자 리뷰 탭으로 이동하여 리뷰 내용, 평점, 날짜를 수집합니다."""
        
        # 현재 entryIframe 내부에 있다고 가정합니다.
        
        # 1. '리뷰' 탭 클릭
        try:
            # ⚠️ 리뷰 탭 선택자 (최신 Naver Place 기준)
            review_tab_selector = By.XPATH, '//a[contains(text(), "리뷰")]'
            review_tab = self.wait.until(EC.element_to_be_clickable(review_tab_selector))
            review_tab.click()
            time.sleep(2) # 리뷰 탭 로딩 대기
            
            # '방문자 리뷰' 탭으로 한 번 더 전환 (리뷰 탭 안에 여러 종류의 리뷰가 있을 수 있음)
            # ⚠️ '방문자 리뷰' 버튼 선택자를 확인해야 합니다.
            # visitor_review_button_selector = By.XPATH, '//a[contains(text(), "방문자 리뷰")]' # 이 선택자는 최근에 사라지거나 XPath가 변경됨
            # 대신 리뷰 탭 클릭 후 바로 리뷰 리스트 로드를 시도합니다.
            
        except TimeoutException:
            print("   ❌ 리뷰 탭을 찾을 수 없습니다. (선택자 확인 필요)")
            return []
        except Exception:
            print("   ❌ 리뷰 탭 클릭 중 오류 발생. (해당 업체에 리뷰가 없을 수 있음)")
            return []

        # 2. '더보기' 클릭을 통한 리뷰 로드
        review_count = 0
        while review_count < max_reviews:
            try:
                # ⚠️ '더보기' 버튼 선택자 (가장 흔한 XPath)
                more_button_selector = By.XPATH, '//a[text()="더보기"]'
                # 더보기 버튼이 로드될 때까지 기다림
                more_button = self.wait.until(EC.element_to_be_clickable(more_button_selector))
                
                # 버튼을 클릭 (스크롤링 방지 및 안정적인 클릭을 위해 JS 사용)
                self.driver.execute_script("arguments[0].click();", more_button)
                time.sleep(1) # 리뷰 로드 대기
                
                # 현재 로드된 리뷰 개수 확인 
                # ID를 활용하여 안정적으로 선택: ul#review_list > li
                review_count = len(self.driver.find_elements(By.CSS_SELECTOR, '#review_list > li')) 
                print(f"   🔄 리뷰 로드 중... 현재 {review_count}개")
                
            except TimeoutException:
                # 더보기 버튼이 없으면 모든 리뷰를 로드한 것으로 간주
                print(f"   ✅ '더보기' 버튼 모두 클릭 완료. 총 {review_count}개 로드됨.")
                break
            except Exception as e:
                print(f"   ⚠️ '더보기' 클릭 중 예외 발생: {e}")
                break

        # 3. 개별 리뷰 데이터 추출
        all_reviews = []
        # ID를 활용하여 안정적으로 선택: ul#review_list > li
        review_items = self.driver.find_elements(By.CSS_SELECTOR, '#review_list > li') 
        
        for item in review_items[:max_reviews]:
            try:
                # ⚠️ 텍스트 선택자
                # '더보기'로 숨겨진 텍스트를 모두 가져오기 위해 JavaScript 사용
                text_element = item.find_element(By.CSS_SELECTOR, 'div.pui__vn15t2') 
                text = self.driver.execute_script("return arguments[0].textContent;", text_element).strip()
                
                # ⚠️ 별점 선택자 (별점 5점 만점에 몇 점인지 텍스트로 표시되는 요소)
                # aria-label="별점 5점 만점에 4.5점" 형태
                rating_text = item.find_element(By.CSS_SELECTOR, 'span.hS-y0').get_attribute('aria-label')
                # 텍스트에서 숫자 부분만 추출 (예: '4.5')
                rating_value = float(rating_text.split(' ')[2]) if rating_text and len(rating_text.split(' ')) > 2 else None
                
                # ⚠️ 작성일 선택자
                date_text = item.find_element(By.CSS_SELECTOR, '.qPoVg time').text
                
                all_reviews.append({
                    '리뷰_내용': text,
                    '평점(방문자)_개별': rating_value,
                    '작성일': date_text
                })

            except NoSuchElementException:
                # 텍스트, 평점, 날짜 중 하나가 없는 리뷰는 건너뜁니다.
                continue
            except Exception as e:
                print(f"   ⚠️ 개별 리뷰 파싱 중 오류 발생: {e}")
                continue
        
        return all_reviews


def run_crawler_and_save(target_places: List[str], region: str, max_reviews: int, output_filename: str = 'naver_place_reviews.csv', headless: bool = True):
    """
    네이버 플레이스 크롤링을 실행하고 결과를 CSV 파일로 저장하는 메인 함수입니다.
    
    Args:
        target_places (List[str]): 크롤링할 업체명 리스트.
        region (str): 필터링할 지역명 (예: "광주").
        max_reviews (int): 업체당 수집할 최대 리뷰 개수.
        output_filename (str): 결과를 저장할 CSV 파일명.
        headless (bool): 크롬을 백그라운드에서 실행할지 여부.
    """
    all_results = []
    naver_crawler = NaverPlaceCrawler(headless=headless) 
    
    try:
        for name in target_places:
            # 변수명 일치를 위해 `region` 대신 `REGION`을 사용할 수 있지만, 함수 내부에서는 인수로 받은 `region`을 사용합니다.
            data = naver_crawler.crawl(name, target_region=region, max_reviews=max_reviews)
            all_results.extend(data)
    except WebDriverException as we:
        print(f"\n🚫 크롤링 환경 오류 발생 (Selenium/WebDriver): {we}")
    except Exception as e:
        print(f"\n🚫 예상치 못한 오류 발생: {e}")
    finally:
        naver_crawler.close() # 드라이버 종료

    # 결과 CSV 파일로 저장
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n--- 최종 저장 완료 ---")
        print(f"총 {len(df)}개의 리뷰 데이터가 {output_filename}에 저장되었습니다.")
        print("이 데이터를 활용하여 긍정/부정 라벨을 생성할 수 있습니다.")
    else:
        print("\n--- 크롤링 결과 없음 ---")


# if __name__ == '__main__':
#     # ------------------------------------------------------------------
#     # 🚨 실행 전 필수 확인 사항 🚨
#     # 1. 크롤링할 업체명을 리스트에 정확히 입력하세요.
#     # 2. Chrome 브라우저가 설치되어 있어야 합니다.
#     # 3. 네이버 플레이스의 HTML 구조는 자주 변경되므로,
#     #    코드가 작동하지 않으면 주석(⚠️) 부분의 CSS 선택자를
#     #    개발자 도구(F12)로 확인하여 수정해야 합니다.
#     # ------------------------------------------------------------------
    
#     # main_run.py 등 외부 파일에서 사용할 변수명과 동일하게 설정
#     target_places = ["위더스 웨딩홀", "아베끄 웨딩", "엔조최재훈"] 
#     REGION = "광주" 
#     MAX_REVIEWS_PER_PLACE = 50 
    
#     # 출력 파일명을 REGION과 수집 개수에 맞게 동적으로 설정
#     OUTPUT_FILE = f'naver_place_reviews_{REGION}_{MAX_REVIEWS_PER_PLACE*len(target_places)}_items.csv'

#     # headless=False로 변경하면 브라우저 동작을 볼 수 있어 디버깅에 유리합니다.
#     run_crawler_and_save(
#         target_places=target_places, 
#         region=REGION, 
#         max_reviews=MAX_REVIEWS_PER_PLACE, 
#         output_filename=OUTPUT_FILE,
#         headless=True # 배포 시에는 True 권장, 디버깅 시에는 False 권장
#     )
