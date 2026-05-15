-- 移除 sales_order_items 表中的冗余字段
-- 注意：先添加外键列（如果不存在），再删除冗余字段

-- 1. 确保 product_id, spec_id, brand_id, warehouse_id 列存在且有索引
-- (这些列应该已存在)

-- 2. 删除冗余字段
ALTER TABLE sales_order_items
DROP COLUMN IF EXISTS product_name,
DROP COLUMN IF EXISTS brand_name,
DROP COLUMN IF EXISTS warehouse_name;

-- 3. 添加外键约束（可选，根据需要）
-- ALTER TABLE sales_order_items
-- ADD CONSTRAINT fk_sales_order_item_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
-- ADD CONSTRAINT fk_sales_order_item_spec FOREIGN KEY (spec_id) REFERENCES product_specs(id) ON DELETE SET NULL,
-- ADD CONSTRAINT fk_sales_order_item_brand FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
-- ADD CONSTRAINT fk_sales_order_item_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL;
