import sqlite3

conn = sqlite3.connect("practice.db")
cur = conn.cursor()
conn.execute('DROP TABLE IF EXISTS STOCK_INFO')
conn.execute('DROP TABLE IF EXISTS PROGRAM_INFO')
conn.execute('CREATE TABLE STOCK_INFO(\
             code INTEGER,\
             name TEXT,\
             date TEXT,\
             shares INTEGER,\
             ytd_price INTEGER,\
             market_cap INTEGER,\
             market TEXT\
            )')
conn.execute('CREATE TABLE PROGRAM_INFO(\
             code INTEGER,\
             name TEXT,\
             date TEXT,\
             time TEXT,\
             price INTEGER,\
             d2d_price INTEGER,\
             d2d_percentage REAL,\
             acc_vol INTEGER,\
             net_vol INTEGER,\
             net_buy INTEGER,\
             net_buy_cap REAL\
            )')
conn.commit()
cur.close()
conn.close()