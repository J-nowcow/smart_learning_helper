#!/usr/bin/env python3
"""
스마트 학습 도우미 실행파일 빌드 스크립트
PyInstaller를 사용하여 Python 설치 없이 실행 가능한 파일을 만듭니다.
"""

import os
import sys
import subprocess
import shutil

def install_pyinstaller():
    """PyInstaller 설치"""
    print("📦 PyInstaller 설치 중...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller==6.3.0"])
        print("✅ PyInstaller 설치 완료!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller 설치 실패: {e}")
        return False

def build_executable():
    """실행파일 빌드"""
    print("🔨 실행파일 빌드 중...")
    
    # PyInstaller 명령어 구성
    cmd = [
        "pyinstaller",
        "--onefile",  # 단일 실행파일로 생성
        "--windowed",  # 콘솔 창 숨기기 (GUI만 표시)
        "--name=스마트_학습_도우미",
        "--add-data=chromedriver_140:.",  # chromedriver 포함
        "ktedu_gui.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ 실행파일 빌드 완료!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        return False

def create_distribution():
    """배포용 폴더 생성"""
    print("📁 배포용 폴더 생성 중...")
    
    # dist 폴더가 있는지 확인
    if not os.path.exists("dist"):
        print("❌ dist 폴더를 찾을 수 없습니다. 빌드를 먼저 실행하세요.")
        return False
    
    # 배포용 폴더 생성
    dist_folder = "스마트_학습_도우미_v1.0"
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    os.makedirs(dist_folder)
    
    # 실행파일 복사
    exe_name = "스마트_학습_도우미.exe" if os.name == 'nt' else "스마트_학습_도우미"
    exe_path = os.path.join("dist", exe_name)
    if os.path.exists(exe_path):
        shutil.copy2(exe_path, dist_folder)
        print(f"✅ 실행파일 복사 완료: {exe_name}")
    else:
        print(f"❌ 실행파일을 찾을 수 없습니다: {exe_path}")
        return False
    
    # 사용법 가이드 복사
    if os.path.exists("사용법_가이드.md"):
        shutil.copy2("사용법_가이드.md", dist_folder)
        print("✅ 사용법 가이드 복사 완료")
    
    # README 생성
    readme_content = """# 📚 스마트 학습 도우미 v1.0

## 🚀 사용 방법
1. **스마트_학습_도우미.exe** (Windows) 또는 **스마트_학습_도우미** (Mac/Linux) 더블클릭
2. 브라우저에서 온라인 강의 로그인
3. GUI에서 "로그인 완료" 버튼 클릭
4. 학습 시작!

## ⚠️ 주의사항
- Chrome 브라우저가 설치되어 있어야 합니다
- 인터넷 연결이 필요합니다
- Python 설치가 필요하지 않습니다!

## 📞 문의
문제가 발생하면 개발자에게 문의하세요.
"""
    
    with open(os.path.join(dist_folder, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✅ 배포용 폴더 생성 완료: {dist_folder}")
    return True

def main():
    """메인 함수"""
    print("📚 스마트 학습 도우미 실행파일 빌더")
    print("=" * 50)
    
    # 1. PyInstaller 설치
    if not install_pyinstaller():
        return False
    
    # 2. 실행파일 빌드
    if not build_executable():
        return False
    
    # 3. 배포용 폴더 생성
    if not create_distribution():
        return False
    
    print("\n🎉 빌드 완료!")
    print("📁 '스마트_학습_도우미_v1.0' 폴더를 다른 사람들에게 배포하세요!")
    print("💡 이 폴더 안의 실행파일은 Python 설치 없이도 실행됩니다!")

if __name__ == "__main__":
    main()
