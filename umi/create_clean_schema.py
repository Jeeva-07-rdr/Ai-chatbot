import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='', database='umi_chatbot_db')
cur = conn.cursor()

cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

tables_sql = [
    # 1. users
    """
    CREATE TABLE IF NOT EXISTS `users` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `username` VARCHAR(150) NOT NULL UNIQUE,
        `email` VARCHAR(254) NOT NULL UNIQUE,
        `password` VARCHAR(128) NOT NULL,
        `first_name` VARCHAR(150) NOT NULL DEFAULT '',
        `last_name` VARCHAR(150) NOT NULL DEFAULT '',
        `is_staff` TINYINT(1) NOT NULL DEFAULT 0,
        `is_active` TINYINT(1) NOT NULL DEFAULT 1,
        `is_superuser` TINYINT(1) NOT NULL DEFAULT 0,
        `last_login` DATETIME NULL,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 2. user_profiles
    """
    CREATE TABLE IF NOT EXISTS `user_profiles` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL UNIQUE,
        `bio` TEXT NULL,
        `avatar` VARCHAR(255) NULL,
        `role` VARCHAR(50) NOT NULL DEFAULT 'user',
        `status` VARCHAR(20) NOT NULL DEFAULT 'active',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 3. user_settings
    """
    CREATE TABLE IF NOT EXISTS `user_settings` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL UNIQUE,
        `theme` VARCHAR(20) NOT NULL DEFAULT 'light',
        `streaming` TINYINT(1) NOT NULL DEFAULT 1,
        `response_style` VARCHAR(20) NOT NULL DEFAULT 'balanced',
        `language` VARCHAR(10) NOT NULL DEFAULT 'en',
        `notifications` TINYINT(1) NOT NULL DEFAULT 1,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 4. ai_preferences
    """
    CREATE TABLE IF NOT EXISTS `ai_preferences` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `provider` VARCHAR(50) NOT NULL DEFAULT 'ollama',
        `model_name` VARCHAR(100) NOT NULL DEFAULT 'qwen2.5:0.5b',
        `temperature` FLOAT NOT NULL DEFAULT 0.7,
        `max_tokens` INT NOT NULL DEFAULT 1500,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 5. chat_sessions
    """
    CREATE TABLE IF NOT EXISTS `chat_sessions` (
        `id` VARCHAR(36) PRIMARY KEY,
        `user_id` INT NOT NULL,
        `title` VARCHAR(255) NOT NULL DEFAULT 'New Chat',
        `is_pinned` TINYINT(1) NOT NULL DEFAULT 0,
        `is_archived` TINYINT(1) NOT NULL DEFAULT 0,
        `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
        `last_activity` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 6. messages
    """
    CREATE TABLE IF NOT EXISTS `messages` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `session_id` VARCHAR(36) NOT NULL,
        `sender` VARCHAR(20) NOT NULL,
        `content` LONGTEXT NOT NULL,
        `tokens_used` INT NOT NULL DEFAULT 0,
        `processing_time_ms` INT NOT NULL DEFAULT 0,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 7. conversation_memory
    """
    CREATE TABLE IF NOT EXISTS `conversation_memory` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `session_id` VARCHAR(36) NULL,
        `memory_category` VARCHAR(50) NOT NULL DEFAULT 'general',
        `memory_content` TEXT NOT NULL,
        `importance_score` FLOAT NOT NULL DEFAULT 1.0,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 8. documents
    """
    CREATE TABLE IF NOT EXISTS `documents` (
        `id` VARCHAR(36) PRIMARY KEY,
        `user_id` INT NOT NULL,
        `session_id` VARCHAR(36) NULL,
        `file_name` VARCHAR(255) NOT NULL,
        `file_path` VARCHAR(255) NULL,
        `file_type` VARCHAR(50) NOT NULL,
        `file_size` INT NOT NULL,
        `processing_status` VARCHAR(20) NOT NULL DEFAULT 'completed',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 9. auth_sessions
    """
    CREATE TABLE IF NOT EXISTS `auth_sessions` (
        `id` VARCHAR(128) PRIMARY KEY,
        `user_id` INT NULL,
        `ip_address` VARCHAR(45) NULL,
        `user_agent` VARCHAR(255) NULL,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `expires_at` DATETIME NOT NULL,
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 10. analytics
    """
    CREATE TABLE IF NOT EXISTS `analytics` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `request_count` INT NOT NULL DEFAULT 0,
        `avg_response_time` FLOAT NOT NULL DEFAULT 0.0,
        `token_usage` INT NOT NULL DEFAULT 0,
        `error_count` INT NOT NULL DEFAULT 0,
        `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 11. runtime_logs
    """
    CREATE TABLE IF NOT EXISTS `runtime_logs` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `log_level` VARCHAR(20) NOT NULL DEFAULT 'INFO',
        `message` TEXT NOT NULL,
        `exception` TEXT NULL,
        `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
]

for sql in tables_sql:
    cur.execute(sql)

cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
conn.commit()

cur.execute("SHOW TABLES;")
clean_tables = [r[0] for r in cur.fetchall()]
print("SUCCESS! Created clean database tables:")
for t in clean_tables:
    print(" -", t)

conn.close()
