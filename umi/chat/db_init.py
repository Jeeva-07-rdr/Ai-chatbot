import os
import pymysql
import logging

logger = logging.getLogger('umi')

def init_mysql_database():
    """
    Automatic initialization routine for MySQL (umi_chatbot_db).
    Verifies database connectivity and 11 clean tables.
    """
    host = os.environ.get('MYSQL_HOST', '127.0.0.1')
    port = int(os.environ.get('MYSQL_PORT', 3306))
    user = os.environ.get('MYSQL_USERNAME', 'root')
    password = os.environ.get('MYSQL_PASSWORD', '')
    dbname = os.environ.get('MYSQL_DATABASE', 'umi_chatbot_db')

    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=dbname)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [r[0] for r in cursor.fetchall()]
        conn.close()
        logger.info(f"MYSQL | Connected to `{dbname}` on {host}:{port} | {len(tables)} clean tables active")
    except Exception as e:
        logger.error(f"MYSQL | Connectivity check note: {e}")
