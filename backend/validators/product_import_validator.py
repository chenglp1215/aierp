"""
产品导入数据校验器

支持的 Excel 列结构（必须严格匹配）：
  - 行号
  - 产品编号
  - 产品名称
  - 产品图片
  - 规格编号
  - 产品分类
  - 品牌
  - 包装
  - 包装单位
  - 价格(中文)

列名不匹配则报错不导入。
"""
from typing import Dict, Any, List, Optional, Tuple


# 期望的列名（严格匹配）
EXPECTED_COLUMNS = [
    "行号",
    "产品编号",
    "产品名称",
    "产品图片",
    "规格编号",
    "产品分类",
    "品牌",
    "包装",
    "包装单位",
    "价格(中文)",
]

# 必填字段（对应的列必须有数据）
REQUIRED_FIELDS = ["产品编号", "产品名称", "品牌", "产品分类"]


def validate_excel_headers(headers: Tuple) -> Tuple[bool, Optional[str]]:
    """
    校验 Excel 表头（严格匹配）

    Args:
        headers: 第一行数据（表头）

    Returns:
        (是否通过, 错误信息)
    """
    if not headers:
        return False, "无法读取表头"

    # 转换为字符串列表
    actual_columns = []
    for h in headers:
        if h is None:
            actual_columns.append("")
        else:
            actual_columns.append(str(h).strip())

    # 检查每个期望列名是否存在
    missing = []
    for expected in EXPECTED_COLUMNS:
        if expected not in actual_columns:
            missing.append(expected)

    if missing:
        return False, f"缺少必填列: {', '.join(missing)}"

    return True, None


def build_header_index_map(headers: Tuple) -> Dict[str, int]:
    """
    构建表头名称到列索引的映射

    Args:
        headers: 表头行数据

    Returns:
        {标准列名: 列索引} 映射
    """
    result = {}

    for col_idx, header in enumerate(headers):
        if header is None:
            continue
        col_name = str(header).strip()
        if col_name in EXPECTED_COLUMNS:
            result[col_name] = col_idx

    return result


def get_cell_value(row_data: Tuple, col_idx: int) -> Any:
    """安全获取单元格值"""
    if col_idx is None or col_idx >= len(row_data):
        return None
    return row_data[col_idx]


def validate_row(
    row_data: Tuple,
    row_num: int,
    header_map: Dict[str, int]
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    校验单行数据

    Args:
        row_data: Excel 行数据元组
        row_num: 行号（用于错误提示）
        header_map: 表头映射

    Returns:
        (是否通过, 解析后的数据字典, 错误信息)
    """
    if not row_data or all(cell is None for cell in row_data):
        return False, None, "空行"

    parsed: Dict[str, Any] = {}
    errors: List[str] = []

    # 解析产品编号（必填）
    col_idx = header_map.get("产品编号")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        parsed["product_code"] = str(value).strip() if value else ""
        if not parsed["product_code"]:
            errors.append("产品编号不能为空")
    else:
        errors.append("缺少产品编号列")

    # 解析产品名称（必填）
    col_idx = header_map.get("产品名称")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        parsed["name"] = str(value).strip() if value else ""
        if not parsed["name"]:
            errors.append("产品名称不能为空")
    else:
        errors.append("缺少产品名称列")

    # 解析品牌名称（必填）
    col_idx = header_map.get("品牌")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        parsed["brand_name"] = str(value).strip() if value else ""
        if not parsed["brand_name"]:
            errors.append("品牌不能为空")
    else:
        errors.append("缺少品牌列")

    # 解析分类名称（必填）
    col_idx = header_map.get("产品分类")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        parsed["category_name"] = str(value).strip() if value else ""
        if not parsed["category_name"]:
            errors.append("产品分类不能为空")
    else:
        errors.append("缺少产品分类列")

    # 解析规格编号（可选）
    col_idx = header_map.get("规格编号")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        if value is not None:
            str_value = str(value).strip()
            # 规格编号不能是布尔值
            if str_value.lower() in ("是", "否", "true", "false", "yes", "no"):
                parsed["spec_code"] = None
            elif str_value:
                parsed["spec_code"] = str_value
            else:
                parsed["spec_code"] = None
        else:
            parsed["spec_code"] = None
    else:
        parsed["spec_code"] = None

    # 解析产品图片（可选）
    col_idx = header_map.get("产品图片")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        parsed["image_url"] = str(value).strip() if value else None
    else:
        parsed["image_url"] = None

    # 解析包装（可选）
    col_idx = header_map.get("包装")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        parsed["packaging"] = str(value).strip() if value else None
    else:
        parsed["packaging"] = None

    # 解析包装单位（可选）
    col_idx = header_map.get("包装单位")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        parsed["sales_spec"] = str(value).strip() if value else None
    else:
        parsed["sales_spec"] = None

    # 解析价格（可选）
    col_idx = header_map.get("价格(中文)")
    if col_idx is not None:
        value = get_cell_value(row_data, col_idx)
        try:
            parsed["price"] = float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            parsed["price"] = 0.0
    else:
        parsed["price"] = 0.0

    # 默认值
    parsed["cas_number"] = None
    parsed["is_active"] = True

    if errors:
        return False, None, "; ".join(errors)

    return True, parsed, None
