-- 创建数据库
CREATE DATABASE IF NOT EXISTS bs_project CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE bs_project;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用户搜索历史表
-- CREATE TABLE IF NOT EXISTS search_history (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id INT NOT NULL,
--     keyword VARCHAR(255) NOT NULL,
--     platform VARCHAR(20) NOT NULL,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     INDEX idx_user_id (user_id),
--     INDEX idx_created_at (created_at)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用户收藏表
-- CREATE TABLE IF NOT EXISTS favorites (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id INT NOT NULL,
--     item_id VARCHAR(100) NOT NULL,
--     platform VARCHAR(20) NOT NULL,
--     title VARCHAR(255) NOT NULL,
--     price DECIMAL(10,2) NOT NULL,
--     image_url TEXT,
--     item_url TEXT,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     UNIQUE KEY unique_user_item (user_id, item_id, platform),
--     INDEX idx_user_id (user_id),
--     INDEX idx_created_at (created_at)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用户设置表
-- CREATE TABLE IF NOT EXISTS user_settings (
--     user_id INT PRIMARY KEY,
--     default_platform VARCHAR(20) DEFAULT 'both',
--     items_per_page INT DEFAULT 20,
--     price_alert BOOLEAN DEFAULT FALSE,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建价格追踪表
-- CREATE TABLE IF NOT EXISTS price_tracking (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id INT NOT NULL,
--     item_id VARCHAR(100) NOT NULL,
--     platform VARCHAR(20) NOT NULL,
--     target_price DECIMAL(10,2) NOT NULL,
--     current_price DECIMAL(10,2) NOT NULL,
--     title VARCHAR(255) NOT NULL,
--     image_url TEXT,
--     item_url TEXT,
--     is_active BOOLEAN DEFAULT TRUE,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     UNIQUE KEY unique_user_item (user_id, item_id, platform),
--     INDEX idx_user_id (user_id),
--     INDEX idx_is_active (is_active)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建平台表
CREATE TABLE IF NOT EXISTS platforms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建商品基本信息表
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform_id INT NOT NULL,
    item_id VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    image_url TEXT,
    item_url TEXT,
    brand VARCHAR(100),
    category VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE,
    UNIQUE KEY unique_platform_item (platform_id, item_id),
    INDEX idx_item_id (item_id),
    INDEX idx_title (title),
    INDEX idx_brand (brand),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建商品价格历史表
CREATE TABLE IF NOT EXISTS price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),
    discount_info VARCHAR(255),
    sales_count INT,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id),
    INDEX idx_recorded_at (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入基础平台数据
INSERT INTO platforms (name, description) 
VALUES ('taobao', '淘宝平台');

INSERT INTO platforms (name, description) 
VALUES ('jd', '京东平台');

-- 添加一些测试数据（可选，建议在开发环境使用）
-- INSERT INTO users (username, email, password) VALUES 
-- ('test_user', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNZoLv.KEJ.Oa');  -- 密码：test123

-- 添加触发器，在更新价格追踪表时检查是否达到目标价格
-- DELIMITER //
-- CREATE TRIGGER check_price_target
-- AFTER UPDATE ON price_tracking
-- FOR EACH ROW
-- BEGIN
--     IF NEW.current_price <= NEW.target_price AND NEW.is_active = TRUE THEN
--         -- 这里可以添加通知逻辑，比如插入到通知表中
--         -- 或者设置一个标志位
--         SET NEW.is_active = FALSE;
--     END IF;
-- END;//
-- DELIMITER ;
