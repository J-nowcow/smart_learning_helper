# 📚 스마트 학습 도우미

온라인 강의 사이트에서 강의를 자동으로 연속 학습하는 프로그램입니다.

## 🚀 사용 방법

### 실행파일 사용 (추천)
1. **`python build_executable.py`** 실행
2. 생성된 **`스마트_학습_도우미_v1.0`** 폴더를 압축해서 배포
3. 사용자는 **`스마트_학습_도우미`** 더블클릭으로 실행

### GitHub Actions 빌드
- GitHub에 push하면 자동으로 Windows `.exe` + macOS `.app` 빌드
- Actions → Build Executables → Artifacts에서 다운로드

## 📋 필요 사항
- **Chrome 브라우저** 설치 필요
- **인터넷 연결** 필요

## 🎬 프로그램 사용법
1. 프로그램 실행
2. 브라우저에서 온라인 강의 로그인
3. GUI에서 "로그인 완료" 버튼 클릭
4. 학습 시작!

## ⚠️ 주의사항
- 강의가 100% 재생된 후 10초 버퍼를 두고 다음 강의로 이동
- 네트워크 연결이 불안정하면 일시정지될 수 있음
- 브라우저를 닫으면 학습이 중단됨

## 📁 파일 구성
- `ktedu_gui.py` - 메인 GUI 프로그램
- `ktedu_auto_player.py` - 학습 엔진
- `browser_manager.py` - 브라우저 관리 모듈
- `video_player.py` - 동영상 플레이어 모듈
- `requirements.txt` - 필요한 패키지 목록
- `build_executable.py` - 실행파일 빌드 스크립트