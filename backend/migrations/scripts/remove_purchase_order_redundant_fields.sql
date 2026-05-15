-- 移除 purchase_orders 表中的冗余字段
-- 注意：brand_id 列保留，只删除 brand_name

-- 1. 删除 purchase_orders 表的 brand_name 字段
ALTER TABLE purchase_orders
DROP COLUMN IF EXISTS brand_name;

-- 2. 删除 purchase_order_items 表中的冗余字段
ALTER TABLE purchase_order_items
DROP COLUMN IF EXISTS brand_name,
DROP COLUMN IF EXISTS warehouse_name;

-- 3. 确保 spec_id 列存在（如果之前不存在，需要先添加）
-- ALTER TABLE purchase_order_items
-- ADD COLUMN IF NOT EXISTS spec_id INT NULL COMMENT '规格ID';

-- 4. 添加外键约束（可选，根据需要）
-- ALTER TABLE purchase_order_items
-- ADD CONSTRAINT fk_purchase_order_item_spec FOREIGN KEY (spec_id) REFERENCES product_specs(id) ON DELETE SET NULL,
-- ADD CONSTRAINT fk_purchase_order_item_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL;