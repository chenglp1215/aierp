"""
统一响应处理装饰器
"""
import functools
import logging
from typing import Callable, Any, Union, Tuple
from typing_extensions import TypeVar, ParamSpec

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def success_response(message: str = "操作成功", result: Any = None) -> dict:
    """成功响应"""
    return {"status": "success", "message": message, "result": result}


def error_response(message: str, result: Any = None, validation_errors: Any = None) -> dict:
    """错误响应

    Args:
        message: 错误消息
        result: 结果数据（通常为None）
        validation_errors: 验证错误列表（可选）
    """
    response = {"status": "error", "message": message, "result": result}
    if validation_errors is not None:
        response["validation_errors"] = validation_errors
    return response


def handle_result(
    result: Union[bool, tuple, dict, None],
    success_msg: str = "操作成功",
    error_msg: str = "操作失败"
) -> dict:
    """处理操作结果，返回统一响应格式

    Args:
        result: 操作结果
            - bool: True成功 False失败
            - tuple: (success: bool, message: str)
            - tuple: (success: bool, message: str, validation_errors: list)
            - dict: 直接返回的字典数据（视为成功）
            - None: 视为失败
        success_msg: 成功时的消息
        error_msg: 失败时的默认消息
    """
    if result is None:
        return error_response(error_msg)

    if isinstance(result, bool):
        if result:
            return success_response(success_msg)
        return error_response(error_msg)

    if isinstance(result, tuple):
        if len(result) == 3:
            success, msg, validation_errors = result
            if success:
                return success_response(msg or success_msg)
            return error_response(msg or error_msg, validation_errors=validation_errors)
        if len(result) == 2:
            success, msg = result
            if success:
                return success_response(msg or success_msg)
            return error_response(msg or error_msg)

    if isinstance(result, dict):
        return success_response(success_msg, result)

    return error_response(error_msg)


def validation_error(errors: list, message: str = "数据验证失败") -> dict:
    """验证错误响应

    Args:
        errors: 验证错误列表
        message: 错误消息
    """
    return error_response(message, validation_errors=errors)
