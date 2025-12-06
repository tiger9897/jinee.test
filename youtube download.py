import sys
import os
import requests
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QPushButton, QLabel, QMessageBox, QFrame)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, QThread, Signal
import yt_dlp

# --- 다운로드 스레드 (속도 개선 적용) ---
class DownloadThread(QThread):
    progress_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        # ★★★ 속도 개선 옵션 적용 ★★★
        ydl_opts = {
            # 1. 영상(video)과 소리(audio)를 따로 받아 합칩니다 (훨씬 빠름)
            # FFmpeg가 없으면 자동으로 일반 모드로 동작합니다.
            'format': 'bestvideo+bestaudio/best', 
            
            # 2. 최종 파일은 mp4로 합침
            'merge_output_format': 'mp4',
            
            # 3. 파일 이름 저장 형식
            'outtmpl': '%(title)s.%(ext)s',
            
            # 4. 여러 조각을 동시에 다운로드하여 속도 향상 (5개 동시)
            'concurrent_fragment_downloads': 5,
            
            # 5. 재생 목록 제외
            'noplaylist': True,
        }

        try:
            self.progress_signal.emit("🚀 고속 다운로드 시작... (FFmpeg 병합 중)")
            
            # 현재 폴더에 ffmpeg.exe가 있는지 확인하여 경로 지정
            # (환경 변수 설정 없이도 동작하게 함)
            current_folder = os.getcwd()
            if os.path.exists(os.path.join(current_folder, "ffmpeg.exe")):
                ydl_opts['ffmpeg_location'] = current_folder

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
                
            self.progress_signal.emit("✅ 다운로드 및 병합 완료!")
        except Exception as e:
            self.progress_signal.emit(f"❌ 오류 발생: {str(e)}")
        finally:
            self.finished_signal.emit()

# --- 메인 윈도우 (디자인 동일) ---
class YoutubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.video_info = {} 

    def init_ui(self):
        self.setWindowTitle("🚀 초고속 유튜브 다운로더")
        self.setGeometry(300, 300, 500, 650)
        self.setStyleSheet("background-color: #f5f5f5;")

        layout = QVBoxLayout()

        # 상단 입력창
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("링크를 붙여넣으세요")
        self.url_input.setStyleSheet("padding: 10px; font-size: 14px; background: white;")
        
        self.search_btn = QPushButton("조회")
        self.search_btn.setStyleSheet("background-color: #ff0000; color: white; padding: 10px; font-weight: bold;")
        self.search_btn.clicked.connect(self.search_video)

        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.search_btn)
        layout.addLayout(input_layout)

        # 정보 표시창
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("background-color: white; border: 1px solid #ddd; border-radius: 8px;")
        info_layout = QVBoxLayout()
        
        self.thumbnail_label = QLabel("준비됨")
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setMinimumHeight(200)
        
        self.title_label = QLabel("-")
        self.title_label.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: gray;")

        info_layout.addWidget(self.thumbnail_label)
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.stats_label)
        self.info_frame.setLayout(info_layout)
        layout.addWidget(self.info_frame)

        # 하단 버튼
        self.status_label = QLabel("FFmpeg가 폴더에 있으면 더 빨라집니다.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #005500; font-weight: bold;")
        
        self.download_btn = QPushButton("고속 다운로드 시작")
        self.download_btn.setEnabled(False) 
        self.download_btn.setStyleSheet("""
            QPushButton { background-color: #0078D7; color: white; padding: 15px; font-size: 15px; font-weight: bold; border-radius: 5px; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.download_btn.clicked.connect(self.start_download)

        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(self.download_btn)

        self.setLayout(layout)

    def search_video(self):
        url = self.url_input.text().strip()
        if not url: return

        self.status_label.setText("정보 분석 중...")
        QApplication.processEvents()

        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            
            self.video_info = {
                'title': info.get('title', 'No Title'),
                'thumbnail': info.get('thumbnail', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'url': url
            }
            self.update_ui()
            self.status_label.setText("조회 성공! 다운로드를 눌러주세요.")
            self.download_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "에러", f"링크를 확인해주세요.\n{e}")
            self.status_label.setText("조회 실패")

    def update_ui(self):
        self.title_label.setText(self.video_info['title'])
        v = f"{self.video_info['view_count']:,}"
        l = f"{self.video_info['like_count']:,}" if self.video_info['like_count'] else "0"
        self.stats_label.setText(f"조회수: {v} | 좋아요: {l}")

        if self.video_info['thumbnail']:
            try:
                data = requests.get(self.video_info['thumbnail']).content
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                self.thumbnail_label.setPixmap(pixmap.scaledToWidth(400, Qt.SmoothTransformation))
            except: pass

    def start_download(self):
        url = self.video_info.get('url')
        if not url: return

        self.download_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        
        self.thread = DownloadThread(url)
        self.thread.progress_signal.connect(self.status_label.setText)
        self.thread.finished_signal.connect(self.finish_download)
        self.thread.start()

    def finish_download(self):
        QMessageBox.information(self, "성공", "다운로드가 완료되었습니다!")
        self.download_btn.setEnabled(True)
        self.search_btn.setEnabled(True)
        self.status_label.setText("준비")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = YoutubeDownloader()
    ex.show()
    sys.exit(app.exec())