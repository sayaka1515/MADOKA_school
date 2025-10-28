# 檔案: check_db.py
import sqlite3, os
print(os.path.abspath('madoka.db'))
if os.path.exists('madoka.db'):
    c=sqlite3.connect('madoka.db')
    for t in ('user','review'):
        cur=c.execute(f"PRAGMA table_info('{t}')").fetchall()
        print(t, cur)
    c.close()
else:
    print("madoka.db 不存在，啟動 run.py 會自動建立")