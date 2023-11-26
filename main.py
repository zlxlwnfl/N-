import requests
from PySide6 import QtCore
from PySide6.QtCore import Signal, QThread
from bs4 import BeautifulSoup
from PIL import Image
import io
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout, \
    QScrollArea, QGridLayout
from PySide6.QtGui import QPixmap, QImage
from qt_material import apply_stylesheet


class Movie:
    def __init__(self, title, genre, director, time, rating, image):
        self.title = title
        self.genre = genre
        self.director = director
        self.time = time
        self.rating = rating
        self.image = image


class CrawlingThread(QThread):
    crawlingFinished = Signal()

    def __init__(self, movies):
        super().__init__()
        self.movies = movies

    def run(self):
        # 크롤링 작업 수행
        # 검색어 설정
        query = "최신 영화"

        # 검색 결과 페이지 URL 설정
        url = f"https://search.naver.com/search.naver?query={query}"

        # GET 요청을 보내고 HTML 응답 받기
        response = requests.get(url)
        # print(response.text)

        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup.prettify())

        # 영화 정보를 담고 있는 요소 찾기
        movie_elements = soup.find_all("div", class_="card_item")

        # 결과 출력
        for movie_element in movie_elements:
            # 제목 추출
            title_element = movie_element.find_next("div", class_="title _ellipsis").find_next("a",
                                                                                               class_="this_text")
            title = title_element.text.strip()
            print("title: " + title)

            # 장르 추출
            genre_element = movie_element.find_next("dl", class_="info_group").find_next("dd")
            genre = genre_element.text.strip()
            print("genre: " + genre)

            # 상영 시간 추출
            time_element = genre_element.find_next("dd")
            time = time_element.text.strip()
            print("time: " + time)

            # 개봉일 추출
            open_element = movie_element.find_next("dl", class_="info_group").find_next("dd")
            open = open_element.text.strip()
            print("open: " + open)

            # 평균 평점 추출
            rating_element = movie_element.find_next("span", class_="num")
            rating = rating_element.text.strip()
            print("rating: " + rating)

            # 감독, 출연진 추출
            director_element = movie_element.find_next("dl", class_="info_group").find_next("span", class_="_text")
            director = director_element.text.strip()
            print("director:" + director)

            # 포스터 이미지 URL 추출
            image_element = movie_element.find("img")
            poster_url = image_element["src"]
            print("poster_url: " + poster_url)

            # 이미지 다운로드
            response = requests.get(poster_url)
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))

            # 이미지 크기 조절
            image = image.resize((100, 150))

            # Movie 객체 생성 및 리스트에 추가
            movie = Movie(title, genre, director, time, rating, image)
            self.movies.append(movie)

        # 크롤링이 완료되면 시그널 발생
        self.crawlingFinished.emit()

    def quit(self):
        exit()


class MainWindow(QMainWindow):
    # 리스트 생성
    movies = []

    def __init__(self):
        super().__init__()

        self.crawling_thread = None
        self.setWindowTitle("N사 검색 최신 영화 정보")
        self.setGeometry(100, 100, 800, 600)

        # 전체 레이아웃
        self.layout = QVBoxLayout()
        self.window_central_widget = QWidget()
        self.window_central_widget.setLayout(self.layout)
        self.setCentralWidget(self.window_central_widget)

        # 버튼
        self.crawl_button = QPushButton("크롤링 시작")
        self.crawl_button.clicked.connect(self.start_crawling)
        self.layout.addWidget(self.crawl_button)

        # 스크롤 영역
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        # 스크롤 영역에 표시될 레이아웃
        self.result_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.result_layout)

    def start_crawling(self):
        self.crawl_button.setEnabled(False)
        self.crawl_button.setText("크롤링 중입니다...")

        self.crawling_thread = CrawlingThread(self.movies)
        self.crawling_thread.crawlingFinished.connect(self.on_crawling_finished)
        self.crawling_thread.finished.connect(self.crawling_thread.deleteLater)
        self.crawling_thread.start()

        # 크롤링 스레드의 종료를 기다리면서 이벤트 처리
        while self.crawling_thread.isRunning():
            QApplication.processEvents()

        # 크롤링 스레드가 종료된 후 이어서 실행할 코드 작성
        print("크롤링 스레드 종료됨")

        for movie in self.movies:
            # 이미지 데이터를 바이트 배열로 변환
            image_data = movie.image.convert("RGBA").tobytes()

            # QImage로 변환
            qimage = QImage(image_data, movie.image.width, movie.image.height, QImage.Format_RGBA8888)

            # 이미지 표시
            pixmap = QPixmap.fromImage(qimage)
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setFixedWidth(150)

            # 결과 레이블 생성
            result_label = QLabel()
            result_label.setText(
                f"<b>제목:</b> {movie.title}<br>"
                f"<b>상영관:</b> {movie.genre}<br>"
                f"<b>상영 시간:</b> {movie.time}<br>"
                f"<b>감독/출연진:</b> {movie.director}<br>"
                f"<b>평균 평점:</b> {movie.rating}<br>"
            )

            # 결과 레이블 정렬 설정
            result_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

            # 결과 추가
            inner_result_layout = QHBoxLayout()
            inner_result_layout.addWidget(image_label)
            inner_result_layout.addWidget(result_label)
            self.result_layout.addLayout(inner_result_layout)

    def on_crawling_finished(self):
        self.crawl_button.setEnabled(True)
        self.crawl_button.setText("크롤링 시작")

    def closeEvent(self, event):
        if self.crawling_thread is not None and self.crawling_thread.isRunning():
            self.crawling_thread.quit()

        event.accept()


# Qt 애플리케이션 생성
app = QApplication([])
window = MainWindow()
apply_stylesheet(app, theme='dark_amber.xml')

# 애플리케이션 실행
window.show()
app.exec()