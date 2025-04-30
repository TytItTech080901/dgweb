import mysql.connector
from config import DB_CONFIG

def test_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 测试查询
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("现有数据表：", tables)
        
        cursor.close()
        conn.close()
        print("数据库连接测试成功！")
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")

if __name__ == "__main__":
    test_connection()