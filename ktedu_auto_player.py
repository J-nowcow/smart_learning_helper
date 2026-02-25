"""
KT EDU 자동재생 스크립트
분석 결과를 바탕으로 영상을 자동으로 재생하고 다음 영상으로 이동합니다.
"""

import time
import sys
import os
from browser_manager import BrowserManager
from video_player import VideoPlayer

class KTEduAutoPlayer:
    def __init__(self, headless=False, log_queue=None):
        """
        스마트 학습 도우미 초기화
        
        Args:
            headless (bool): 브라우저를 숨김 모드로 실행할지 여부
            log_queue: GUI로 로그를 전달할 큐
        """
        self.headless = headless
        self.log_queue = log_queue  # GUI로 로그 전달용 큐
        self.video_count = 0
        self.max_videos = 100  # 최대 학습할 강의 수 (무한루프 방지)
        
        # 브라우저 관리자 초기화
        self.browser_manager = BrowserManager(headless=headless, log_callback=self.log_print)
        self.driver = None
        self.video_player = None
        
    def log_print(self, message):
        """로그 출력 함수 - GUI와 터미널 모두에 출력"""
        # GUI로 로그 전달
        if self.log_queue:
            try:
                self.log_queue.put(message)
            except:
                pass
        
        # 터미널에도 출력 (Windows 호환성을 위해 인코딩 처리)
        try:
            # Windows 환경에서 안전한 출력
            import sys
            import os
            
            # Windows에서는 cp949 인코딩 사용
            if os.name == 'nt':
                try:
                    # 이모지 문자를 안전한 문자로 변환
                    safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
                    # 이모지를 제거하거나 대체
                    safe_message = safe_message.replace('🚀', '[시작]').replace('✅', '[완료]').replace('❌', '[오류]')
                    print(safe_message, flush=True)
                except:
                    # 인코딩 실패 시 이모지 제거
                    import re
                    safe_message = re.sub(r'[^\x00-\x7F]+', '[이모지]', message)
                    print(safe_message, flush=True)
            else:
                print(message, flush=True)
        except:
            # 모든 출력 실패 시 기본 메시지
            print("로그 메시지 출력됨", flush=True)
        
    def setup_driver(self):
        """Chrome 드라이버 설정 및 초기화"""
        self.driver = self.browser_manager.setup_driver()
        if self.driver:
            self.video_player = VideoPlayer(self.driver, log_callback=self.log_print)
        return self.driver
    
    def wait_for_video_ready(self, timeout=60):
        """영상 플레이어를 찾고 재생 준비"""
        if not self.video_player:
            return None, None
        return self.video_player.wait_for_video_ready(timeout)
    
    def get_video_progress(self, video_element):
        """현재 영상 재생 상태 확인"""
        if not self.video_player:
            return None
        return self.video_player.get_video_progress(video_element)
    
    def start_video_if_paused(self, video_element):
        """영상이 멈춰있으면 재생 시작"""
        if not self.video_player:
            return
        self.video_player.start_video_if_paused(video_element)
    
    def wait_for_video_end(self, video_element):
        """영상이 끝날 때까지 대기 (실시간 길이 체크)"""
        if not self.video_player:
            return False
        return self.video_player.wait_for_video_end(video_element, self.log_queue)
    
    def click_next_video(self):
        """다음 영상 버튼 클릭"""
        if not self.video_player:
            return False
        return self.video_player.click_next_video()
    
    def handle_alerts(self):
        """알림창 처리"""
        if not self.video_player:
            return False
        return self.video_player.handle_alerts()
    
    def play_videos_automatically(self, start_url=None, max_videos=None):
        """영상 자동재생 시작"""
        if max_videos:
            self.max_videos = max_videos
            
        self.log_print("🚀 스마트 학습을 시작합니다!")
        self.log_print(f"📊 최대 학습 강의 수: {self.max_videos}개")
        
        try:
            # 드라이버가 초기화되지 않았다면 초기화
            if not self.driver:
                self.log_print("🔧 드라이버 초기화 중...")
                self.setup_driver()
            
            if start_url:
                self.log_print(f"📱 시작 URL로 이동: {start_url}")
                self.driver.get(start_url)
                self.log_print("⏳ 페이지 로딩 대기 중... (5초)")
                time.sleep(5)
                self.log_print(f"🔍 페이지 로딩 완료, 현재 URL: {self.driver.current_url}")
                self.log_print(f"🔍 페이지 제목: {self.driver.title}")
                self.log_print("🔐 브라우저에서 로그인을 완료한 후 GUI의 '로그인 완료' 버튼을 클릭하세요!")
                self.log_print("⏳ 로그인 완료 대기 중... (무기한 대기)")
                return  # 로그인 완료를 기다리기 위해 여기서 대기
            
            while self.video_count < self.max_videos:
                self.video_count += 1
                self.log_print(f"\n🎬 === 강의 #{self.video_count} 학습 시작 ===")
                
                # 알림창 처리
                self.handle_alerts()
                
                video_element, _ = self.wait_for_video_ready()
                if not video_element:
                    self.log_print("❌ 강의 플레이어를 찾을 수 없습니다. 다음 강의로 이동...")
                    if not self.click_next_video():
                        self.log_print("❌ 더 이상 학습할 강의가 없습니다.")
                        break
                    continue

                # 영상 재생 완료까지 모니터링
                if video_element:
                    success = self.wait_for_video_end(video_element)
                    if success:
                        self.log_print(f"✅ 강의 #{self.video_count} 학습 완료!")
                    else:
                        self.log_print(f"⚠️ 강의 #{self.video_count} 학습 중단됨")
                
                # 다음 영상으로 이동
                if not self.click_next_video():
                    self.log_print("❌ 더 이상 학습할 강의가 없습니다.")
                    break
                    
                # 잠시 대기
                time.sleep(3)
                
        except KeyboardInterrupt:
            self.log_print("\n⏹️ 사용자에 의해 중단되었습니다.")
        except Exception as e:
            self.log_print(f"❌ 학습 중 오류 발생: {str(e)}")
        finally:
            self.log_print(f"📊 총 학습한 강의 수: {self.video_count}개")
    
    def close(self):
        """드라이버 종료"""
        if self.browser_manager:
            self.browser_manager.close()

def main_with_args(url, count, headless=False, log_queue=None):
    """GUI에서 호출하는 함수"""
    def log_print(message):
        # GUI 큐로 로그 전달
        if log_queue:
            try:
                log_queue.put(message)
            except:
                pass
        
        # 터미널에도 출력
        print(message, flush=True)
    
    log_print("📚 스마트 학습 도우미")
    log_print("=" * 50)
    
    log_print(f"시작 URL: {url}")
    log_print(f"최대 학습 강의 수: {count}개")
    
    player = KTEduAutoPlayer(headless=headless, log_queue=log_queue)
    
    try:
        # 드라이버 설정 및 브라우저 열기
        log_print("🚀 브라우저를 실행하고 사이트에 접속합니다...")
        player.setup_driver()
        
        # 시작 URL로 이동
        log_print(f"📱 사이트 접속 중: {url}")
        try:
            player.driver.get(url)
            log_print("✅ 사이트 접속 완료!")
            time.sleep(3)
            
            # 페이지 로딩 확인
            log_print("🔍 페이지 로딩 상태 확인 중...")
            current_url = player.driver.current_url
            log_print(f"📍 현재 URL: {current_url}")
            
            # 페이지 제목 확인
            try:
                page_title = player.driver.title
                log_print(f"📄 페이지 제목: {page_title}")
            except Exception as e:
                log_print(f"⚠️ 페이지 제목 확인 실패: {str(e)}")
            
        except Exception as e:
            log_print(f"❌ 사이트 접속 실패: {str(e)}")
            raise
        
        # 사용자에게 로그인 안내
        log_print("\n" + "="*60)
        log_print("🔐 브라우저 창에서 KT EDU에 로그인해주세요!")
        log_print("📍 로그인 후 원하는 강의 페이지로 이동하세요.")
        log_print("✅ 준비가 되면 자동으로 감지합니다. (CLI 모드)")
        if log_queue:
            log_print("⏳ GUI에서 로그인 완료 신호를 기다리는 중...")
        log_print("="*60)
        
        # 로그인 완료 대기
        if log_queue:
            log_print("🔐 로그인 대기 상태 - GUI에서 '로그인 완료' 버튼을 클릭해주세요!")
            # GUI 모드에서는 큐를 통해 신호 대기
            while True:
                try:
                    time.sleep(0.1)
                    # 로그인 완료는 GUI에서 처리됨
                    # 브라우저가 살아있는지 확인
                    try:
                        current_url = player.driver.current_url
                        # 너무 자주 상태 확인하지 않도록 5초마다만 출력
                        if not hasattr(player, '_last_status_time') or time.time() - player._last_status_time > 5:
                            log_print(f"🔍 브라우저 상태 확인: {current_url}")
                            player._last_status_time = time.time()
                    except Exception as e:
                        log_print(f"❌ 브라우저 연결 끊어짐: {str(e)}")
                        break
                except Exception as e:
                    log_print(f"❌ 로그인 대기 중 오류: {str(e)}")
                    break
        else:
            # CLI 모드: 로그인 페이지를 벗어날 때까지 폴링
            log_print("⏳ 로그인 감지 대기 중... 로그인 완료 후 강의 페이지로 이동해주세요.")
            last_report = 0
            while True:
                try:
                    current_url = player.driver.current_url
                    page_title = player.driver.title
                    now = time.time()
                    if now - last_report > 5:
                        log_print(f"🔍 현재 상태: {page_title} | {current_url}")
                        last_report = now
                    # 로그인 페이지를 벗어나거나 강의 컨텐츠 URL로 이동하면 진행
                    if 'login.do' not in current_url and ('courseContents.do' in current_url or 'player' in current_url or 'contents' in current_url):
                        log_print("✅ 로그인 및 강의 페이지 진입 감지!")
                        break
                except Exception as e:
                    log_print(f"⚠️ 상태 확인 오류: {str(e)}")
                time.sleep(1.5)
        
        log_print("\n🎬 자동재생을 시작합니다!")
        
        # 자동재생 시작 (현재 페이지에서)
        player.play_videos_automatically(start_url=None, max_videos=count)
        
    except KeyboardInterrupt:
        log_print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        log_print(f"❌ 오류 발생: {str(e)}")
    finally:
        player.close()

def main():
    """메인 실행 함수"""
    import argparse
    
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='KT EDU 자동재생기')
    parser.add_argument('--url', default='https://ktedu.kt.com/education/courseContents.do?classId=200094625_2025_0001_01', 
                       help='시작 URL')
    parser.add_argument('--count', type=int, default=100, 
                       help='최대 재생할 영상 수')
    parser.add_argument('--headless', action='store_true', 
                       help='헤드리스 모드로 실행')
    
    args = parser.parse_args()
    
    main_with_args(args.url, args.count, args.headless)

if __name__ == "__main__":
    main()
