# stocks
Realtime stock tracking program


(1) 프로그램 개요

포함된 파일
  1. dbstart.py         :   sqlite3 db를 구축하는 파일 (최초 1회만 실행)
  2. Realtime_stock.py  :   실시간 주식 tracking 프로그램 (main 프로그램)

필요 파일
  1. 키움증권 api 관련
    1-1. KOAStudioSA
    1-2. KOALoader.dll
  2. 가상환경 관련
    2-1. anaconda 32bit 가상환경
    2-2. python version >= 3.7
  3. 인덱스 파일
    3-1. index.csv (수정 방법은 후술)

필요 패키지
  1. pandas
  2. numpy
  3. pyqt, pyqt5
  4. plotly


(2) 프로그램 실행법

  1. 용형 개인 노트북
  시작메뉴 -> anaconda prompt 실행

  <아래와 같이 입력>
  conda activate py38_32
  cd PycharmProjects/stocks-main/stocks-main
  python Realtime_stock.py

  2. 회사 공용 pc
  시작메뉴 -> anaconda prompt 실행

  <아래와 같이 입력>
  cd desktop/stocks-main
  python Realtime_stock.py


(3) index.csv 수정법
  index.csv : 인덱스 (섹터 구분)이 담긴 csv 파일(엑셀로 편집 가능)
  각 열이 1개 섹터입니다.
  각 열의 첫번째 행 : sector 대분류
  각 열의 두번재 행 : sector 세부 분류
  각 열의 세번째 행 ~ : 각 종목명
  종목명이 다를 시, 에러가 나거나 화면에 출력이 안될 수 있으니, 꼭 종목명 확인 부탁드립니다.

  ex)
  배터리   배터리   
  전체     셀
  A1       B1
  A2       B2
  A3       B3

  여기서 A1을 삭제하고, A4를 새로 추적하고 싶음

  배터리   배터리   
  전체     셀
  A2       B1
  A3       B2
  A4       B3

  디스플레이 섹터를 추가하고 싶음

  배터리   배터리  디스플레이
  전체     셀      OLED장비
  A2       B1      C1
  A3       B2      C2
  A4       B3      C3

  배터리 / 셀 을 삭제하고 싶음

  배터리   디스플레이
  전체     OLED장비
  A2       C1
  A3       C2
  A4       C3

  중간에 빈 셀이 없도록 부탁드립니다! 빈셀이 있을 시 에러가 발생할 수도 있습니다.


(4) 에러 발생시

  버전 업데이트 등으로 프로그램에 에러가 생길 수도 있습니다.
  에러 발생 시, 에러 메세지 (anaconda prompt에 출력됨)을 복사해서,
  제 연락처 (010-3801-8287)로 주시면, 확인해서 조치해 드리겠습니다.
