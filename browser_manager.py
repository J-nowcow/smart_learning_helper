"""
브라우저 관리 모듈
Chrome 드라이버 설정 및 초기화를 담당합니다.
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
try:
    from webdriver_manager.chrome import ChromeDriverManager
    _WDM_AVAILABLE = True
except ImportError:
    _WDM_AVAILABLE = False

class BrowserManager:
    def __init__(self, headless=False, log_callback=None):
        """
        브라우저 관리자 초기화
        
        Args:
            headless (bool): 브라우저를 숨김 모드로 실행할지 여부
            log_callback (function): 로그 출력 콜백 함수
        """
        self.driver = None
        self.headless = headless
        self.log_callback = log_callback
        
    def log(self, message):
        """로그 출력"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def setup_driver(self):
        """Chrome 드라이버 설정 및 초기화"""
        self.log("🔧 ChromeDriver 설정 시작...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            self.log("👻 헤드리스 모드 활성화")
        
        # 일반적인 브라우저처럼 보이게 설정
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent 설정
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
        
        # Wine 환경에서 Chrome 경로 설정
        if os.name == 'nt':  # Windows 환경 (Wine 포함)
            self._setup_chrome_path(chrome_options)
        
        self.log("✅ Chrome 옵션 설정 완료")
        
        # 1순위: webdriver-manager로 자동 다운로드/캐시 사용
        if _WDM_AVAILABLE:
            try:
                self.log("🔄 webdriver-manager로 현재 Chrome에 맞는 드라이버 자동 설치 중...")
                wdm_path = ChromeDriverManager().install()
                self.log(f"✅ 드라이버 경로: {wdm_path}")
                service = Service(wdm_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.log("✅ Chrome 브라우저 시작 완료! (webdriver-manager)")
                self._apply_stealth()
                return self.driver
            except Exception as e_wdm:
                self.log(f"⚠️ webdriver-manager 실패, selenium-manager로 재시도: {str(e_wdm)}")

        # 2순위: Selenium 내장 selenium-manager 폴백
        try:
            self.log("🔁 Selenium-manager로 ChromeDriver 자동 설치/사용 시도 중...")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.log("✅ Chrome 브라우저 시작 완료! (selenium-manager)")
            self._apply_stealth()
            return self.driver
        except Exception as e2:
            self.log(f"❌ 모든 드라이버 시도 실패: {str(e2)}")
            raise
    
    def _setup_chrome_path(self, chrome_options):
        """Wine 환경에서 Chrome 경로 설정"""
        possible_chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USER', '')),
        ]
        
        chrome_found = False
        for chrome_path in possible_chrome_paths:
            if os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
                self.log(f"✅ Chrome 경로 설정: {chrome_path}")
                chrome_found = True
                break
        
        if not chrome_found:
            self.log("⚠️ Chrome을 찾을 수 없습니다. Wine 환경에 Chrome을 설치해주세요.")
            self.log("💡 해결방법: wine chrome_installer.exe 실행하여 Chrome 설치")
    
    def _apply_stealth(self):
        """자동화 탐지 회피 스크립트 실행"""
        try:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.log("🛡️ 자동화 탐지 회피 설정 완료")
        except Exception:
            pass

    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.log("✅ 브라우저가 종료되었습니다.")
