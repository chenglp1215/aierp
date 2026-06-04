"""
产品批量导入服务
"""
import os
import logging
import traceback
from typing import Dict, Any, List
from datetime import datetime

import openpyxl

from models_mysql.product import Product, ProductSpec, Brand, Category
from services.import_task_service import import_task_service
from validators.product_import_validator import validate_row, validate_excel_headers, build_header_index_map

# 配置日志 - 确保输出到控制台
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 如果没有 handler，添加一个
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 批量提交大小
BATCH_SIZE = 500


class ProductBatchImportService:
    """产品批量导入服务"""

    async def execute_import(self, task_id: int, file_path: str) -> None:
        """
        执行导入任务（后台任务调用）

        Args:
            task_id: 任务ID
            file_path: Excel 文件路径
        """
        from config import settings

        errors: List[Dict[str, Any]] = []
        total_rows = 0
        success_count = 0
        update_count = 0
        error_count = 0

        # 品牌和分类缓存
        brand_cache: Dict[str, int] = {}
        category_cache: Dict[str, int] = {}

        # 已处理的规格编号集合（避免重复）
        processed_spec_codes: set = set()

        wb = None
        try:
            logger.info(f"[任务{task_id}] 开始执行导入，文件: {file_path}")

            # 更新任务状态为处理中
            await import_task_service.update_task(task_id, status="processing")
            logger.info(f"[任务{task_id}] 状态更新为 processing")

            # 使用 read_only 模式打开 Excel
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            logger.info(f"[任务{task_id}] Excel 文件打开成功")

            # 读取表头（第一行）
            header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
            if not header_row:
                logger.error(f"[任务{task_id}] 无法读取表头")
                errors.append({"row": 1, "product_code": "", "field": "header", "message": "无法读取表头"})
                await import_task_service.update_task(task_id, status="failed")
                return

            logger.info(f"[任务{task_id}] 表头读取成功: {list(header_row)[:10]}")

            # 校验表头
            valid, err = validate_excel_headers(header_row)
            if not valid:
                logger.error(f"[任务{task_id}] 表头校验失败: {err}")
                errors.append({"row": 1, "product_code": "", "field": "header", "message": err})
                await import_task_service.update_task(task_id, status="failed")
                return

            # 构建表头映射
            header_map = build_header_index_map(header_row)
            logger.info(f"[任务{task_id}] 表头映射: {header_map}")

            # 先统计总行数
            total_rows = sum(1 for _ in ws.iter_rows(min_row=2))
            await import_task_service.update_task(task_id, total_rows=total_rows)
            logger.info(f"[任务{task_id}] 总行数: {total_rows}")

            # 重置读取位置
            wb.close()
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            logger.info(f"[任务{task_id}] 重新打开文件，开始逐行处理")

            # 逐行处理
            row_num = 1
            processed = 0

            for row in ws.iter_rows(min_row=2, values_only=True):
                row_num += 1

                # 校验数据
                valid, parsed, error_msg = validate_row(row, row_num, header_map)

                if not valid:
                    error_count += 1
                    # 尝试从行数据中获取产品编号
                    product_code = ""
                    if "product_code" in header_map:
                        col_idx = header_map["product_code"]
                        if col_idx < len(row) and row[col_idx]:
                            product_code = str(row[col_idx]).strip()
                    errors.append({
                        "row": row_num,
                        "product_code": product_code,
                        "field": "-",
                        "message": error_msg or "数据校验失败",
                    })
                    processed += 1
                    continue

                if not parsed:
                    processed += 1
                    continue

                try:
                    # 获取或创建品牌
                    brand_name = parsed["brand_name"]
                    if brand_name not in brand_cache:
                        brand = await Brand.filter(name=brand_name).first()
                        if brand:
                            brand_cache[brand_name] = brand.id
                        else:
                            brand = await Brand.create(name=brand_name, is_active=True)
                            brand_cache[brand_name] = brand.id
                    brand_id = brand_cache[brand_name]

                    # 获取或创建分类
                    category_name = parsed["category_name"]
                    if category_name not in category_cache:
                        category = await Category.filter(name=category_name).first()
                        if category:
                            category_cache[category_name] = category.id
                        else:
                            category = await Category.create(name=category_name)
                            category_cache[category_name] = category.id
                    category_id = category_cache[category_name]

                    # 处理产品
                    product_code = parsed["product_code"]
                    product = await Product.filter(product_code=product_code).first()

                    if product:
                        # 更新产品
                        product.name = parsed["name"]
                        product.brand_id = brand_id
                        product.category_id = category_id
                        if parsed.get("image_url"):
                            product.image_url = parsed["image_url"]
                        await product.save()
                        update_count += 1
                    else:
                        # 新建产品
                        product = await Product.create(
                            product_code=product_code,
                            name=parsed["name"],
                            brand_id=brand_id,
                            category_id=category_id,
                            image_url=parsed.get("image_url"),
                            is_active=True,
                        )
                        success_count += 1

                    # 处理规格
                    spec_code = parsed.get("spec_code")
                    if spec_code:
                        # 检查是否已处理过该规格编号
                        if spec_code in processed_spec_codes:
                            error_count += 1
                            errors.append({
                                "row": row_num,
                                "product_code": product_code,
                                "field": "spec_code",
                                "message": f"规格编号 '{spec_code}' 在文件中重复",
                            })
                        else:
                            processed_spec_codes.add(spec_code)

                            # 检查规格是否已存在
                            spec = await ProductSpec.filter(spec_code=spec_code).first()
                            if spec:
                                # 更新规格
                                spec.product_id = product.id
                                spec.packaging = parsed.get("packaging")
                                spec.sales_spec = parsed.get("sales_spec")
                                spec.price = parsed.get("price", 0.0)
                                spec.cas_number = parsed.get("cas_number")
                                spec.is_active = parsed.get("is_active", True)
                                await spec.save()
                            else:
                                # 创建新规格
                                await ProductSpec.create(
                                    product_id=product.id,
                                    spec_code=spec_code,
                                    packaging=parsed.get("packaging"),
                                    sales_spec=parsed.get("sales_spec"),
                                    price=parsed.get("price", 0.0),
                                    cas_number=parsed.get("cas_number"),
                                    is_active=parsed.get("is_active", True),
                                )

                except Exception as e:
                    error_count += 1
                    errors.append({
                        "row": row_num,
                        "product_code": parsed.get("product_code", ""),
                        "field": "system",
                        "message": str(e),
                    })
                    logger.error(f"导入行 {row_num} 失败: {e}\n{traceback.format_exc()}")

                processed += 1

                # 每处理 BATCH_SIZE 行更新进度
                if processed % BATCH_SIZE == 0:
                    logger.info(f"[任务{task_id}] 进度: {processed}/{total_rows}, 成功={success_count}, 更新={update_count}, 错误={error_count}")
                    await import_task_service.update_task(
                        task_id,
                        processed_rows=processed,
                        success_count=success_count,
                        update_count=update_count,
                        error_count=error_count,
                    )

            # 生成错误文件
            error_file_path = None
            if errors:
                error_file_path = await self._generate_error_file(task_id, errors)
                logger.info(f"[任务{task_id}] 错误文件已生成: {error_file_path}")

            # 更新任务完成状态
            await import_task_service.update_task(
                task_id,
                status="completed",
                processed_rows=total_rows,
                success_count=success_count,
                update_count=update_count,
                error_count=error_count,
                error_file_path=error_file_path,
            )
            logger.info(f"[任务{task_id}] 导入完成! 总数={total_rows}, 新建={success_count}, 更新={update_count}, 错误={error_count}")

        except Exception as e:
            logger.error(f"[任务{task_id}] 导入失败: {e}\n{traceback.format_exc()}")
            await import_task_service.update_task(task_id, status="failed")

        finally:
            # 确保 Excel 文件关闭
            if wb:
                try:
                    wb.close()
                except Exception:
                    pass

            # 删除临时文件（带重试）
            self._safe_delete_file(file_path)

    def _safe_delete_file(self, file_path: str, max_retries: int = 3) -> None:
        """安全删除文件，带重试机制"""
        import time

        for attempt in range(max_retries):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # 等待文件释放
                else:
                    logger.warning(f"无法删除临时文件 {file_path}，将在稍后清理")
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")
                return

    async def _generate_error_file(self, task_id: int, errors: List[Dict[str, Any]]) -> str:
        """生成错误详情 Excel 文件"""
        from config import settings

        # 确保上传目录存在
        upload_dir = os.path.join(settings.UPLOAD_DIR, "import_errors")
        os.makedirs(upload_dir, exist_ok=True)

        # 生成文件名
        filename = f"import_errors_{task_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        file_path = os.path.join(upload_dir, filename)

        # 创建 Excel 文件
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "错误详情"

        # 写入表头
        ws.append(["行号", "产品编号", "错误字段", "错误信息"])

        # 写入数据
        for error in errors:
            ws.append([
                error.get("row", ""),
                error.get("product_code", ""),
                error.get("field", ""),
                error.get("message", ""),
            ])

        wb.save(file_path)
        wb.close()

        return file_path


# 服务实例
product_batch_import_service = ProductBatchImportService()
