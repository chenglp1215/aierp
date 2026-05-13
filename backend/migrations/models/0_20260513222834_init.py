from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `permissions` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    `code` VARCHAR(100) NOT NULL UNIQUE COMMENT '权限编码',
    `name` VARCHAR(100) NOT NULL COMMENT '权限名称',
    `type` VARCHAR(12) NOT NULL COMMENT '权限类型',
    `path` VARCHAR(200) COMMENT '路径/路由',
    `description` VARCHAR(500) COMMENT '描述',
    `sort_order` INT NOT NULL COMMENT '排序' DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `parent_id` INT COMMENT '父权限',
    CONSTRAINT `fk_permissi_permissi_9a9dabee` FOREIGN KEY (`parent_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='权限模型';
CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '角色ID',
    `code` VARCHAR(50) NOT NULL UNIQUE COMMENT '角色编码',
    `name` VARCHAR(100) NOT NULL COMMENT '角色名称',
    `description` VARCHAR(500) COMMENT '描述',
    `is_fixed` BOOL NOT NULL COMMENT '是否固化角色' DEFAULT 0,
    `status` VARCHAR(8) NOT NULL COMMENT '角色状态' DEFAULT 'active',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='角色模型';
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `password` VARCHAR(255) NOT NULL COMMENT '密码(bcrypt hash)',
    `email` VARCHAR(100) UNIQUE COMMENT '邮箱',
    `phone` VARCHAR(20) UNIQUE COMMENT '手机号',
    `full_name` VARCHAR(100) COMMENT '全名',
    `avatar` VARCHAR(500) COMMENT '头像URL',
    `status` VARCHAR(8) NOT NULL COMMENT '用户状态' DEFAULT 'active',
    `last_login` DATETIME(6) COMMENT '最后登录时间',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='用户模型';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role_permissions` (
    `roles_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    FOREIGN KEY (`roles_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_role_permis_roles_i_cc3f1e` (`roles_id`, `permission_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_roles` (
    `users_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    FOREIGN KEY (`users_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_user_roles_users_i_c62307` (`users_id`, `role_id`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "l/Hh4GQA=="
)
