# 주식 전종목 틱 저장 레코딩
import sqlite3
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QEventLoop
from PyQt5.QAxContainer import *
from datetime import datetime
from collections import namedtuple
import pandas as pd
import copy as cp
import plotly.express as px
import time
import numpy as np

class Function:
    def __init__(self):
        self.reg = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')
        self.acc_no = ""
        self.set_signal_slots()
        self.set_screen()
        self.conn = sqlite3.connect("practice.db")
        self.switch_real = False
        self.stock_tuple = namedtuple("stock", "code, name, date, shares, ytd_price, market_cap, key")
        self.program_tuple = namedtuple("program", "code, name, date, time, price, d2d_price, d2d_percentage,acc_vol,\
         net_vol, net_buy, net_buy_cap")
        """
        self.cache1 : stock record 들을 받아서 임시저장. 2**10 (1024개 가 되면 flush)
        self.cache2 : program record 들을 받아서 임시저장. 다 차면 flush
        self.cache3_0 : {name : (sector1, sector2)}
        self.cache3 : {item_code : (name, market_cap, sector1, sector2)} dictionary 
        """
        self.cache1 = []
        self.cache2 = []
        self.cache3_0 = {}
        self.cache3 = {}
        """
        self.dashboard : {item_code : { name : xxx, market_cap : ppp, net_buy_cap : yyy, sector1 : zzz, sector2 : www,\
         current_% : ppp}}
        """
        self.dashboard = {}
        """
        self.cnt : 프로그램 매매 틱 counter
        """
        self.cnt = 0
        
    #######################################################################################################
    # Basic Setting
    #######################################################################################################

    def set_signal_slots(self):
        self.reg.OnEventConnect.connect(self.receive_login)
        self.reg.OnReceiveRealData.connect(self.receive_RealData)
        self.reg.OnReceiveMsg.connect(self.receive_msg)

    def set_screen(self):
        self.screen_order = 1000
        self.screen_tr = 4000  # Tr type screen number
        self.screen_real = 5000  # Real type screen number / increased by 1

    def set_stock_list(self):
        kospi = self.reg.dynamicCall("GetCodeListByMarket(QString)", 0)
        kosdaq = self.reg.dynamicCall("GetCodeListByMarket(QString)", 10)
        all_list = kospi.split(';')[:-1] + kosdaq.split(';')[:-1]
        print("kospi + kosdaq 종목수 : %s" % len(all_list))

        # 0. sector 분류 생성
        df = pd.read_csv("index.csv")
        df = df.dropna(axis="columns", how="all")

        nr, nc = df.shape
        for i in range(nc):
            sector1 = list(df.columns)[i].split(".")[0]
            sector2 = df.iloc[0, i]
            for j in range(nr):
                self.cache3_0[df.iloc[j, i]] = (sector1, sector2)

        # A. 마스터 리스트 등록
        for i, code in enumerate(all_list):
            info = self.reg.dynamicCall("KOA_Functions(QString, QString)", "GetMasterStockInfo", code)
            info = info.replace("|", ";")
            info = info.split(";")

            name = str(self.reg.dynamicCall("GetMasterCodeName(QString)", code))
            shares = int(self.reg.dynamicCall("GetMasterListedStockCnt(QString)", code))
            ytd_price = int(self.reg.dynamicCall("GetMasterLastPrice(QString)", code))
            market_cap = int(shares * ytd_price / 100000000)

            if not code == "" and "스팩" not in info and "ETN" not in info and "ETF" not in info and \
                    "ETN" not in name and "스팩" not in name:
                market = None
                if code in kospi:
                    market = 'kospi'
                elif code in kosdaq:
                    market = 'kosdaq'
                else:
                    pass
                stock = self.stock_tuple
                date = datetime.now().strftime("%Y%m%d")

                # store in cache1
                self.cache1.append(stock(code, name, date, shares, ytd_price, market_cap, market))

                # find sector1, sector2
                if name in self.cache3_0:
                    sector1, sector2 = self.cache3_0[name]
                    # store in cache3
                    self.cache3[code] = (name, market_cap, sector1, sector2)

                    # store in dashboard
                    if market_cap >= 5000:
                        self.dashboard.update(
                            {code: {'name': name, 'market_cap': market_cap, 'net_buy_cap': None, 'current_price': None,
                                    'current_%': None, 'sector1': sector1, 'sector2': sector2}}
                        )

        # flush to db
        cur = self.conn.cursor()
        cur.executemany(
            'INSERT INTO STOCK_INFO VALUES (?, ?, ?, ?, ?, ?, ?)',
            self.cache1
        )
        cur.close()
        self.conn.commit()
        print("stock list completed")

    def set_real(self):
        cnt = 1
        screen_no = int(self.screen_real)
        print("screen_no : ", screen_no)

        # Program Request
        for item_code in self.cache3.keys():
            if (cnt % 99) == 0:
                screen_no += 1

            # FID 131 : 시간외 매도호가 총잔량
            data = [str(screen_no), item_code, 131, "1"]
            self.req_RealData(data)
            cnt += 1

        # Execution Request
        for item_code in self.cache3.keys():
            if (cnt % 99) == 0:
                screen_no += 1

            # FID 20 : 체결시간
            data = [str(screen_no), item_code, 20, "1"]
            self.req_RealData(data)
            cnt += 1

        # TX Request
        for item_code in self.cache3.keys():
            if (cnt % 99) == 0:
                screen_no += 1

            # FID 141 : 주식당일거래원
            data = [str(screen_no), item_code, 141, "1"]
            self.req_RealData(data)
            cnt += 1

        self.switch_real = True
        print('Complete set_real')

    #######################################################################################################
    # Real Data
    #######################################################################################################

    def req_RealData(self, data):
        [screenNo, codes, fids, realRegType] = data
        self.reg.dynamicCall("SetRealReg(QString, QString, QString, QString)", [screenNo, codes, fids, realRegType])

    def receive_RealData(self, item_code, realType, realData):
        if realType == "주식체결" and self.switch_real is True:
            pass

        elif realType == "종목프로그램매매" and self.switch_real is True:
            self.get_ProgramData(item_code, realType, realData)

        elif realType == "주식당일거래원" and self.switch_real:
            pass

        elif realType == "주식예상체결":
            pass

    def get_ProgramData(self, item_code, realType, realData):

        try:
            RealList = realData.split()

            # store in cache2
            program = self.program_tuple
            self.cache2.append(program(
                code=item_code,
                name=self.cache3[item_code][0],
                date=datetime.now().strftime("%Y%m%d"),
                time=RealList[0],
                price=abs(int(RealList[1])),
                d2d_price=int(RealList[3]),
                d2d_percentage=float(RealList[4]),
                acc_vol=abs(int(RealList[5])),
                net_vol=abs(int(RealList[10])),
                net_buy=int(RealList[11]),
                net_buy_cap=int(RealList[11]) / self.cache3[item_code][1]
            ))
            if len(self.cache2) == 1024:
                self.flush_cache2()
                print("flush finished")

            # store in dashboard
            if item_code in self.dashboard.keys():
                self.dashboard[item_code]['net_buy_cap'] = int(RealList[11]) / self.cache3[item_code][1]
                self.dashboard[item_code]['current_price'] = abs(int(RealList[1]))
                self.dashboard[item_code]['current_%'] = float(RealList[4])

        except:
            pass

        # display
        self.cnt += 1
        if self.cnt % 10240 == 0:
            self.display()
        elif self.cnt % 10240 == 2560:
            print('collecting...25%')
        elif self.cnt % 10240 == 5120:
            print('collecting...50%')
        elif self.cnt % 10240 == 7680:
            print('collecting...75%')

    #######################################################################################################
    # flush
    #######################################################################################################

    def flush_cache2(self):
        To_update = cp.deepcopy(self.cache2)
        cur = self.conn.cursor()
        try:
            cur.executemany(
                'INSERT INTO PROGRAM_INFO VALUES (? ,?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                To_update
            )
        except Exception as e:
            print(e)
        cur.close()
        self.conn.commit()
        self.cache2.clear()

    ###########################################d############################################################
    # display
    #######################################################################################################

    def display(self):
        start = time.time()
        pd.set_option('display.max_rows', None)
        board = cp.deepcopy(self.dashboard)
        display = pd.DataFrame(board).transpose().dropna()
        display = display.sort_values('net_buy_cap', ascending=False)
        print(display)
        display[['net_buy_cap', 'current_price', 'market_cap', 'current_%']] \
            = display[['net_buy_cap', 'current_price', 'market_cap', 'current_%']].apply(pd.to_numeric)
        try:
            fig1 = px.treemap(display,
                              path=["sector1", "sector2", "name"],
                              values='market_cap',
                              color='net_buy_cap',
                              hover_data=['net_buy_cap'],
                              color_continuous_scale='RdBu_r',
                              color_continuous_midpoint=np.average(display['net_buy_cap'], weights=display['market_cap'])
                              )
            fig1.update_layout(margin=dict(t=50, l=25, r=25, b=25))
            fig1.update_layout(title="면적 : 시총 // 색상 : 시총대비 프로그램 순매수")
            fig1.show()

            display['net_buy_cap'] += 2
            fig2 = px.treemap(display,
                              path=["sector1", "sector2", "name"],
                              values='net_buy_cap',
                              color='current_%',
                              hover_data=['current_%'],
                              color_continuous_scale='RdBu_r',
                              color_continuous_midpoint=np.average(display['current_%'], weights=display['net_buy_cap'])
                              )
            fig2.update_layout(margin=dict(t=50, l=25, r=25, b=25))
            fig2.update_layout(title="면적 : 시총대비 프로그램 순매수 // 색상 : 전일대비")
            fig2.show()


        except Exception as e:
            print(e)
        print(f"Elpased time : {time.time() - start}")

    #######################################################################################################
    # Login
    #######################################################################################################

    def req_login(self):
        self.reg.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def receive_login(self, err_code):
        now = datetime.today().strftime("%H:%M:%S")
        if err_code == 0:
            value = self.reg.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
            user_id = self.reg.GetLoginInfo("USER_ID")
            user_name = self.reg.GetLoginInfo("USER_NAME")
            if value == "1":
                gubun = "Mock Trading Server"
            else:
                gubun = "Real Trading Server"

            print(gubun, "connected", user_id, user_name)

            text = "Kiwoom API " + gubun + " Login \n" + now + " " + user_id + " " + user_name
            print(text)

        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_connect_state(self):
        ret = self.reg.dynamicCall("GetConnectState()")
        return ret

    # 계좌 정보 반환
    def get_account_info(self, rqname):
        ret = self.reg.dynamicCall("GetLoginInfo(QString)", [rqname])
        return ret

    def receive_msg(self, screen_no, rqname, trcode, msg):
        pass


class MainControl(Function):
    cnt_req = 0

    def main_setting(self):
        # Login and Account Information
        self.req_login()
        account_num = int(self.get_account_info("ACCOUNT_CNT"))
        accounts = self.get_account_info("ACCNO")
        account_list = accounts.split(';')[0:account_num]
        print("내 계좌번호 :", account_list)

        # Register Stock list
        self.set_stock_list()

        # Request Stock Real LOB Data
        self.set_real()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = MainControl()
    main.main_setting()
    app.exec_()
