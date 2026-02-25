"""
동영상 STT(Speech-to-Text) 처리 모듈
동영상에서 오디오를 추출하고 Whisper를 사용하여 텍스트로 변환합니다.
"""

import os
import tempfile
import subprocess
import logging

# STT 관련 라이브러리는 선택적으로 설치 — 없으면 STT 기능만 비활성화
try:
    import whisper
    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False

try:
    import yt_dlp
    _YTDLP_AVAILABLE = True
except ImportError:
    _YTDLP_AVAILABLE = False

try:
    from pydub import AudioSegment
    _PYDUB_AVAILABLE = True
except ImportError:
    _PYDUB_AVAILABLE = False

class VideoSTTProcessor:
    def __init__(self, model_size="base", log_callback=None):
        """
        STT 처리기 초기화
        
        Args:
            model_size (str): Whisper 모델 크기 (tiny, base, small, medium, large)
            log_callback (function): 로그 출력 콜백 함수
        """
        self.model_size = model_size
        self.log_callback = log_callback
        self.model = None
        self.temp_dir = None
        
    def log(self, message):
        """로그 출력"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def setup_model(self):
        """Whisper 모델 로드"""
        if not _WHISPER_AVAILABLE:
            self.log("⚠️ whisper 라이브러리가 설치되지 않아 STT를 사용할 수 없습니다.")
            self.log("💡 STT 사용 시: pip install openai-whisper")
            return False
        try:
            self.log(f"🤖 Whisper 모델 로딩 중... ({self.model_size})")
            self.model = whisper.load_model(self.model_size)
            self.log("✅ Whisper 모델 로딩 완료!")
            return True
        except Exception as e:
            self.log(f"❌ 모델 로딩 실패: {str(e)}")
            return False
    
    def download_video(self, video_url, output_path=None, cookies_header: str | None = None):
        """
        동영상 다운로드
        
        Args:
            video_url (str): 동영상 URL
            output_path (str): 출력 경로 (None이면 임시 디렉토리 사용)
            
        Returns:
            str: 다운로드된 동영상 파일 경로
        """
        if not _YTDLP_AVAILABLE:
            self.log("⚠️ yt_dlp 라이브러리가 설치되지 않아 동영상 다운로드를 사용할 수 없습니다.")
            self.log("💡 STT 사용 시: pip install yt-dlp")
            return None
        try:
            self.log("📥 동영상 다운로드 시작...")
            
            # 임시 디렉토리 생성
            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp(prefix="video_stt_")
            
            if not output_path:
                output_path = os.path.join(self.temp_dir, "video.%(ext)s")
            
            # yt-dlp 옵션 설정
            ydl_opts = {
                'outtmpl': output_path,
                # 더 관대한 포맷 선택: 우선 비디오+오디오, 실패 시 단일 스트림
                'format': 'bv*+ba/b/best',
                'merge_output_format': 'mp4',
                'quiet': True,  # 로그 출력 최소화
                # HLS 사이트 호환성 향상
                'hls_use_mpegts': True,
                'hls_prefer_native': True,
            }
            # 인증이 필요한 경우 쿠키 전달
            if cookies_header:
                ydl_opts['http_headers'] = {
                    'Cookie': cookies_header
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                # 실제 다운로드된 파일 경로 찾기
                if os.path.exists(downloaded_file):
                    self.log(f"✅ 동영상 다운로드 완료: {downloaded_file}")
                    return downloaded_file, info.get('title')
                else:
                    # 확장자 없는 파일명으로 다운로드된 경우
                    for ext in ['.mp4', '.webm', '.mkv', '.avi']:
                        test_path = downloaded_file + ext
                        if os.path.exists(test_path):
                            self.log(f"✅ 동영상 다운로드 완료: {test_path}")
                            return test_path, info.get('title')
                    
                    raise FileNotFoundError("다운로드된 동영상 파일을 찾을 수 없습니다.")
                    
        except Exception as e:
            self.log(f"❌ 동영상 다운로드 실패: {str(e)}")
            return None, None
    
    def extract_audio(self, video_path, audio_path=None):
        """
        동영상에서 오디오 추출
        
        Args:
            video_path (str): 동영상 파일 경로
            audio_path (str): 출력 오디오 파일 경로 (None이면 임시 파일)
            
        Returns:
            str: 추출된 오디오 파일 경로
        """
        try:
            self.log("🎵 오디오 추출 시작...")
            
            if not audio_path:
                audio_path = os.path.join(self.temp_dir, "audio.wav")
            
            # pydub을 사용한 오디오 추출
            video = AudioSegment.from_file(video_path)
            
            # Whisper에 최적화된 설정
            audio = video.set_frame_rate(16000)  # 16kHz로 변환
            audio = audio.set_channels(1)        # 모노로 변환
            
            # WAV 파일로 저장
            audio.export(audio_path, format="wav")
            
            self.log(f"✅ 오디오 추출 완료: {audio_path}")
            return audio_path
            
        except Exception as e:
            self.log(f"❌ 오디오 추출 실패: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_path, language="ko"):
        """
        오디오를 텍스트로 변환
        
        Args:
            audio_path (str): 오디오 파일 경로
            language (str): 언어 코드 (ko, en, ja 등)
            
        Returns:
            dict: 변환 결과 (text, segments, language 등)
        """
        try:
            if not self.model:
                if not self.setup_model():
                    return None
            
            self.log("🎤 STT 처리 시작...")
            
            # Whisper로 음성 인식
            result = self.model.transcribe(
                audio_path, 
                language=language,
                verbose=False
            )
            
            self.log("✅ STT 처리 완료!")
            return result
            
        except Exception as e:
            self.log(f"❌ STT 처리 실패: {str(e)}")
            return None
    
    def process_video(self, video_url, output_dir=None, language="ko", cookies_header: str | None = None):
        """
        동영상 전체 처리 (다운로드 → 오디오 추출 → STT)
        
        Args:
            video_url (str): 동영상 URL
            output_dir (str): 출력 디렉토리 (None이면 임시 디렉토리)
            language (str): 언어 코드
            
        Returns:
            dict: 처리 결과
        """
        try:
            self.log("🚀 동영상 STT 처리 시작...")
            
            # 출력 디렉토리 설정: 프로젝트 내 stt/YYYYMMDD_HHMMSS_제목
            if not output_dir:
                base_dir = os.path.join(os.getcwd(), 'stt')
            else:
                base_dir = output_dir
            os.makedirs(base_dir, exist_ok=True)
            
            # 1. 동영상 다운로드
            video_path, title = self.download_video(video_url, cookies_header=cookies_header)
            if not video_path:
                return None
            
            # 파일 저장 하위 디렉토리명 구성
            from datetime import datetime
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = self.sanitize_filename(title) if title else 'video'
            output_dir_final = os.path.join(base_dir, f"{ts}_{safe_title}")
            os.makedirs(output_dir_final, exist_ok=True)

            # 2. 오디오 추출
            audio_path = os.path.join(output_dir_final, "audio.wav")
            audio_path = self.extract_audio(video_path, audio_path)
            if not audio_path:
                return None
            
            # 3. STT 처리
            result = self.transcribe_audio(audio_path, language)
            if not result:
                return None
            
            # 4. 결과 저장
            output_files = self.save_results(result, output_dir_final)
            
            self.log("✅ 동영상 STT 처리 완료!")
            return {
                'text': result['text'],
                'segments': result.get('segments', []),
                'language': result.get('language', language),
                'output_files': output_files
            }
            
        except Exception as e:
            self.log(f"❌ STT 처리 실패: {str(e)}")
            return None
    
    def save_results(self, result, output_dir):
        """STT 결과를 파일로 저장"""
        try:
            output_files = {}
            
            # 1. 전체 텍스트 저장
            text_file = os.path.join(output_dir, "transcript.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            output_files['text'] = text_file
            
            # 2. 시간별 구간 텍스트 저장 (SRT 형식)
            if 'segments' in result and result['segments']:
                srt_file = os.path.join(output_dir, "transcript.srt")
                with open(srt_file, 'w', encoding='utf-8') as f:
                    for i, segment in enumerate(result['segments'], 1):
                        start_time = self.format_time(segment['start'])
                        end_time = self.format_time(segment['end'])
                        text = segment['text'].strip()
                        
                        f.write(f"{i}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
                
                output_files['srt'] = srt_file
            
            self.log(f"📁 결과 파일 저장 완료: {output_dir}")
            return output_files
            
        except Exception as e:
            self.log(f"❌ 결과 저장 실패: {str(e)}")
            return {}
    
    def format_time(self, seconds):
        """초를 SRT 시간 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def cleanup(self):
        """임시 파일 정리"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                self.log("🗑️ 임시 파일 정리 완료")
        except Exception as e:
            self.log(f"⚠️ 임시 파일 정리 실패: {str(e)}")

    def sanitize_filename(self, name: str) -> str:
        """파일/폴더 이름에 사용할 수 있도록 안전하게 변환"""
        if not name:
            return 'video'
        import re
        name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
        name = name.strip().replace("\n", " ").replace("\r", " ")
        return name[:120]
    
    def __del__(self):
        """소멸자에서 임시 파일 정리"""
        self.cleanup()


def main():
    """테스트용 메인 함수"""
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python video_stt.py <동영상_URL>")
        return
    
    video_url = sys.argv[1]
    
    # STT 처리기 생성
    processor = VideoSTTProcessor(model_size="base")
    
    try:
        # 동영상 처리
        result = processor.process_video(video_url, language="ko")
        
        if result:
            print("\n=== STT 결과 ===")
            print(f"언어: {result['language']}")
            print(f"텍스트 길이: {len(result['text'])}자")
            print(f"구간 수: {len(result['segments'])}개")
            print(f"출력 파일: {result['output_files']}")
            
            print("\n=== 추출된 텍스트 (처음 500자) ===")
            print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
        else:
            print("❌ STT 처리 실패")
    
    finally:
        processor.cleanup()


if __name__ == "__main__":
    main()
