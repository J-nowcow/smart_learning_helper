"""
스마트 학습 도우미 - GUI 버전
개발을 모르는 사람도 마우스 클릭만으로 사용할 수 있는 GUI 애플리케이션
"""

import sys
import os
import subprocess
import time
import queue
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SmartLearningGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📚 스마트 학습 도우미")
        self.setGeometry(100, 100, 800, 900)
        self.setMinimumSize(750, 800)
        self.resize(800, 900)
        
        # 아이콘 설정
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 헤더 섹션
        self.create_header(layout)
        
        # 설정 섹션
        self.create_settings(layout)
        
        # 제어 섹션
        self.create_controls(layout)
        
        # 상태 섹션
        self.create_status(layout)
        
        # 로그 섹션
        self.create_log(layout)
        
        central_widget.setLayout(layout)
        
        # 학습 관련 변수
        self.is_running = False
        self.waiting_for_login = False
        self.player_instance = None  # 자동재생 플레이어 인스턴스
        self.log_queue = queue.Queue()  # 로그 전달용 큐
        
        # 로그 큐 처리용 타이머
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.process_log_queue)
        self.log_timer.start(100)  # 100ms마다 큐 확인
        
        # 스타일 적용
        self.apply_styles()
    
    def process_log_queue(self):
        """로그 큐에서 메시지를 가져와서 GUI에 표시"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                
                # 진행률 업데이트 신호 처리
                if message.startswith("PROGRESS_UPDATE:"):
                    progress_value = float(message.split(":")[1])
                    self.progress_bar.setValue(int(progress_value))
                    self.status_label.setText(f"학습 진행 중... ({progress_value:.1f}%)")
                else:
                    # 일반 로그 메시지
                    self.log_text.addItem(message)
                    self.log_text.scrollToBottom()
        except queue.Empty:
            pass
        
    def create_header(self, layout):
        """헤더 섹션 생성"""
        # 간단한 제목만 표시
        title = QLabel("📚 스마트 학습 도우미")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333333;
            margin: 10px 0;
            font-family: 'Arial', 'Malgun Gothic', sans-serif;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
    def create_settings(self, layout):
        """설정 섹션 생성"""
        settings_group = QGroupBox("⚙️ 설정")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2E86AB;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        settings_layout = QVBoxLayout()
        
        # URL 설정
        url_layout = QHBoxLayout()
        url_label = QLabel("시작 URL:")
        url_label.setMinimumWidth(100)
        self.url_input = QLineEdit()
        self.url_input.setText("https://ktedu.kt.com/education/courseContents.do?classId=200094625_2025_0001_01")
        self.url_input.setPlaceholderText("온라인 강의 URL을 입력하세요")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        settings_layout.addLayout(url_layout)
        
        # 영상 개수 설정
        count_layout = QHBoxLayout()
        count_label = QLabel("학습할 강의 수:")
        count_label.setMinimumWidth(100)
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(1, 1000)
        self.count_spinbox.setValue(100)
        self.count_spinbox.setSuffix("개")
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_spinbox)
        count_layout.addStretch()
        settings_layout.addLayout(count_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
    def create_controls(self, layout):
        """제어 섹션 생성"""
        controls_layout = QHBoxLayout()
        
        # 시작 버튼
        self.start_btn = QPushButton("🚀 학습 시작")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 25px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #4CAF50);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3E8E41, stop:1 #2E7D32);
            }
            QPushButton:disabled {
                background: #CCCCCC;
                color: #666666;
            }
        """)
        self.start_btn.clicked.connect(self.start_player)
        controls_layout.addWidget(self.start_btn)
        
        # 로그인 완료 버튼
        self.login_btn = QPushButton("✅ 로그인 완료")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setVisible(False)
        self.login_btn.clicked.connect(self.confirm_login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 25px;
                padding: 10px 30px;
                font-family: 'Arial', 'Malgun Gothic', sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1565C0, stop:1 #0D47A1);
            }
        """)
        self.login_btn.clicked.connect(self.confirm_login)
        controls_layout.addWidget(self.login_btn)
        
        # 중지 버튼
        self.stop_btn = QPushButton("학습 종료")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F44336, stop:1 #D32F2F);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 25px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF5722, stop:1 #F44336);
            }
            QPushButton:disabled {
                background: #CCCCCC;
                color: #666666;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_player)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
    def create_status(self, layout):
        """상태 섹션 생성"""
        status_group = QGroupBox("📊 상태")
        status_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2E86AB;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        status_layout = QVBoxLayout()
        
        # 현재 상태
        self.status_label = QLabel("준비됨")
        self.status_label.setStyleSheet("""
            font-size: 16px;
            color: #2E86AB;
            font-weight: bold;
            padding: 10px;
            background-color: #F5F5F5;
            border-radius: 5px;
        """)
        status_layout.addWidget(self.status_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #8BC34A);
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        # 영상 정보
        self.video_info = QLabel("")
        self.video_info.setStyleSheet("font-size: 14px; color: #666;")
        self.video_info.setVisible(False)
        status_layout.addWidget(self.video_info)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
    def create_log(self, layout):
        """로그 섹션 생성"""
        log_group = QGroupBox("📝 실행 로그")
        log_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2E86AB;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        log_layout = QVBoxLayout()
        
        # 로그 텍스트 - QListWidget 사용 (QTextCursor 오류 방지)
        self.log_text = QListWidget()
        self.log_text.setMinimumHeight(400)  # 150 -> 400 (3배 이상)
        self.log_text.setStyleSheet("""
            QListWidget {
                background-color: #F8F8F8;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 2px;
                border: none;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # 로그 제어 버튼
        log_controls = QHBoxLayout()
        clear_btn = QPushButton("🗑️ 로그 지우기")
        clear_btn.clicked.connect(self.log_text.clear)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        log_controls.addWidget(clear_btn)
        log_controls.addStretch()
        log_layout.addLayout(log_controls)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
    def apply_styles(self):
        """전체 스타일 적용"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FAFAFA;
                font-family: 'Arial', 'Malgun Gothic', sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                font-family: 'Arial', 'Malgun Gothic', sans-serif;
            }
            QLabel {
                font-family: 'Arial', 'Malgun Gothic', sans-serif;
            }
            QPushButton {
                font-family: 'Arial', 'Malgun Gothic', sans-serif;
            }
            QLineEdit {
                font-family: 'Arial', 'Malgun Gothic', sans-serif;
            }
            QSpinBox {
                font-family: 'Arial', 'Malgun Gothic', sans-serif;
            }
            QTextEdit {
                font-family: 'Arial', 'Malgun Gothic', sans-serif;
            }
        """)
        
    def start_player(self):
        """학습 시작"""
        if self.is_running:
            return
            
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.start_btn.setText("브라우저 실행 중...")
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.video_info.setVisible(True)
        self.status_label.setText("브라우저를 실행하고 있습니다...")
        self.progress_bar.setValue(0)
        
        # 로그 초기화
        self.log_text.clear()
        self.log_text.addItem("🚀 스마트 학습을 시작합니다!")
        self.log_text.addItem(f"📊 최대 학습 강의 수: {self.count_spinbox.value()}개")
        self.log_text.addItem("")
        
        # 즉시 로그인 버튼 표시
        self.waiting_for_login = True
        self.start_btn.setVisible(False)
        self.login_btn.setVisible(True)
        self.status_label.setText("브라우저에서 로그인을 완료한 후 '로그인 완료' 버튼을 클릭하세요")
        self.log_text.addItem("🔐 브라우저에서 로그인을 완료한 후 '로그인 완료' 버튼을 클릭하세요!")
        
        # 학습 실행
        self.run_learning_direct()
        
        
    def confirm_login(self):
        """로그인 완료 확인"""
        self.log_text.addItem("🔍 로그인 완료 버튼 클릭됨!")
        
        if self.waiting_for_login:
            self.log_text.addItem("✅ 로그인 완료 처리 시작...")
            self.waiting_for_login = False
            
            # 버튼 상태 변경
            self.log_text.addItem(f"📋 로그인 버튼 표시 상태: {self.login_btn.isVisible()}")
            self.login_btn.setVisible(False)
            self.log_text.addItem(f"📋 로그인 버튼 표시 상태 (변경 후): {self.login_btn.isVisible()}")
            
            self.log_text.addItem(f"📋 시작 버튼 표시 상태: {self.start_btn.isVisible()}")
            self.start_btn.setVisible(True)
            self.start_btn.setEnabled(True)
            self.start_btn.setText("🎬 학습 시작")
            self.log_text.addItem(f"📋 시작 버튼 표시 상태 (변경 후): {self.start_btn.isVisible()}")
            
            self.status_label.setText("학습을 시작합니다...")
            self.log_text.addItem("✅ 로그인 완료! 학습을 시작합니다...")
            self.log_text.addItem("")
            
            # 학습 시작 (별도 스레드에서 실행하여 GUI 블로킹 방지)
            self.log_text.addItem("🚀 학습 시작!")
            import threading
            learning_thread = threading.Thread(target=self.start_learning)
            learning_thread.daemon = True
            learning_thread.start()
        else:
            self.log_text.addItem("⚠️ 로그인 대기 상태가 아닙니다.")
    
    def start_learning(self):
        """로그인 완료 후 학습 시작"""
        try:
            if not self.player_instance:
                self.log_text.addItem("❌ 플레이어 인스턴스가 없습니다. 먼저 '학습 시작' 버튼을 클릭하세요.")
                return
            
            self.log_text.addItem("🎬 학습 시작!")
            
            # 기존 플레이어 인스턴스로 영상 재생 시작 (URL 이동 없이 바로 시작)
            self.player_instance.play_videos_automatically(
                start_url=None,  # URL 이동 없이 바로 시작
                max_videos=self.count_spinbox.value()
            )
            
            self.log_text.addItem("✅ 학습 완료!")
            
        except Exception as e:
            self.log_text.addItem(f"❌ 학습 오류: {str(e)}")
            import traceback
            self.log_text.addItem(f"📋 상세 오류: {traceback.format_exc()}")
        finally:
            self.log_text.scrollToBottom()
        
    def stop_player(self):
        """학습 중지"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.player_process:
            try:
                self.player_process.terminate()
                self.player_process = None
            except:
                pass
        
        # 로그 워커는 daemon 스레드이므로 자동 종료됨
        
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🚀 학습 시작")
        self.stop_btn.setEnabled(False)
        self.status_label.setText("중지됨")
        self.log_text.addItem("⏹️ 사용자에 의해 중지되었습니다.")
    
    def run_learning_direct(self):
        """실행파일에서 직접 실행 - 터미널창 없이 실행"""
        
        # 초기 로그 메시지
        self.log_text.addItem("🚀 스마트 학습 도우미 시작...")
        self.log_text.addItem(f"📱 URL: {self.url_input.text()}")
        self.log_text.addItem(f"📊 강의 수: {self.count_spinbox.value()}개")
        self.log_text.addItem("🔐 브라우저에서 로그인을 완료한 후 '로그인 완료' 버튼을 클릭하세요!")
        self.log_text.scrollToBottom()
        
        # 로그인 대기 상태로 설정
        self.waiting_for_login = True
        self.start_btn.setVisible(False)
        self.login_btn.setVisible(True)
        self.status_label.setText("브라우저에서 로그인을 완료한 후 '로그인 완료' 버튼을 클릭하세요")
        
        # 직접 모듈 import해서 실행 (터미널창 방지)
        try:
            self.log_text.addItem("🔄 학습 모듈 로딩 중...")
            self.log_text.scrollToBottom()
            
            # auto_player 모듈 직접 import
            import ktedu_auto_player
            
            # 플레이어 인스턴스 생성 및 저장
            self.player_instance = ktedu_auto_player.KTEduAutoPlayer(
                headless=False, 
                log_queue=self.log_queue,
            )
            
            self.log_text.addItem("🌐 브라우저 실행 중...")
            self.log_text.scrollToBottom()
            
            # URL로 이동하고 로그인 대기
            self.player_instance.play_videos_automatically(
                start_url=self.url_input.text(),
                max_videos=self.count_spinbox.value()
            )
            
            # 여기서는 로그인 대기 상태로 종료됨
            
        except Exception as e:
            self.log_text.addItem(f"❌ 학습 오류: {str(e)}")
            import traceback
            self.log_text.addItem(f"📋 상세 오류: {traceback.format_exc()}")
        finally:
            self.log_text.scrollToBottom()

def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("스마트 학습 도우미")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("스마트 학습")
    
    # 윈도우 생성 및 표시
    window = SmartLearningGUI()
    window.show()
    
    # 이벤트 루프 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
