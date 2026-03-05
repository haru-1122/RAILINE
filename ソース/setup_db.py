import mysql.connector

# 1. 自分のPC（移行元）の設定
LOCAL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root", # 自分のPCのパスワード
    "database": "hew",
    "charset": "utf8mb4"
}

# 2. Aiven（移行先）の設定
AIVEN_CONFIG = {
    "host": "railinedb-haru-270f.k.aivencloud.com",
    "user": "avnadmin",
    "password": "AVNS_MuzXZBW8I2iVk46Xknn",
    "database": "defaultdb",
    "port": 22306,
    "charset": "utf8mb4"
}

def migrate():
    try:
        # 両方に接続
        local_conn = mysql.connector.connect(**LOCAL_CONFIG)
        aiven_conn = mysql.connector.connect(**AIVEN_CONFIG)
        
        local_cur = local_conn.cursor(dictionary=True)
        aiven_cur = aiven_conn.cursor()

        # --- trainテーブルの移行 ---
        print("Transferring 'train' table...")
        local_cur.execute("SELECT * FROM train")
        rows = local_cur.fetchall()
        for row in rows:
            sql = "INSERT IGNORE INTO train (line_id, line_name) VALUES (%s, %s)"
            aiven_cur.execute(sql, (row['line_id'], row['line_name']))

        # --- stationsテーブルの移行 ---
        print("Transferring 'stations' table...")
        local_cur.execute("SELECT * FROM stations")
        rows = local_cur.fetchall()
        for row in rows:
            sql = "INSERT IGNORE INTO stations (line_id, station_name, checked) VALUES (%s, %s, %s)"
            aiven_cur.execute(sql, (row['line_id'], row['station_name'], row['checked']))

        aiven_conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'local_conn' in locals(): local_conn.close()
        if 'aiven_conn' in locals(): aiven_conn.close()

if __name__ == "__main__":
    migrate()