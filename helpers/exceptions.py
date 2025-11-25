#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File   : exceptions.py
@Author : AutorizePro Team
@Date   : 2024
@Desc   : 自定义异常类和异常处理工具
"""


# ============================================================================
# 自定义异常类
# ============================================================================

class AutorizeProException(Exception):
    """AutorizePro 基础异常类"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or {}
        super(AutorizeProException, self).__init__(message)
    
    def __str__(self):
        if self.details:
            return "%s (Details: %s)" % (self.message, str(self.details))
        return self.message


class CacheException(AutorizeProException):
    """缓存操作异常"""
    pass


class AIAnalysisException(AutorizeProException):
    """AI 分析异常"""
    pass


class ConfigurationException(AutorizeProException):
    """配置异常"""
    pass


class NetworkException(AutorizeProException):
    """网络请求异常"""
    pass


class DataParsingException(AutorizeProException):
    """数据解析异常"""
    pass


# ============================================================================
# 异常处理装饰器
# ============================================================================

def safe_execute(default_return=None, log_error=True, error_prefix=""):
    """
    安全执行装饰器：捕获异常并返回默认值
    
    Args:
        default_return: 发生异常时的默认返回值
        log_error: 是否打印错误日志
        error_prefix: 错误日志前缀
    
    用法:
        @safe_execute(default_return="", log_error=True, error_prefix="Cache")
        def some_function():
            # 可能抛出异常的代码
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    error_msg = "[ERROR]"
                    if error_prefix:
                        error_msg += " [%s]" % error_prefix
                    error_msg += " Function '%s' failed: %s" % (func.__name__, str(e))
                    print(error_msg)
                return default_return
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


# ============================================================================
# 异常处理辅助函数
# ============================================================================

def handle_encoding_error(data, operation="encode", fallback_value=""):
    """
    统一处理编码/解码错误
    
    Args:
        data: 要处理的数据
        operation: 操作类型 "encode" 或 "decode"
        fallback_value: 失败时的返回值
    
    Returns:
        处理后的数据或 fallback_value
    """
    if data is None:
        return fallback_value
    
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1', 'iso-8859-1']
    
    try:
        if operation == "encode":
            # 尝试编码为 UTF-8
            try:
                if isinstance(data, unicode):
                    return data.encode('utf-8')
                elif isinstance(data, str):
                    return data
                else:
                    return str(data).encode('utf-8')
            except (UnicodeDecodeError, UnicodeEncodeError):
                # 如果失败，尝试使用哈希值
                return str(hash(data)).encode('utf-8')
        
        elif operation == "decode":
            # 尝试解码
            if isinstance(data, unicode):
                return data
            
            for encoding in encodings:
                try:
                    return data.decode(encoding)
                except (UnicodeDecodeError, AttributeError):
                    continue
            
            # 所有编码都失败，返回字符串表示
            return str(data)
    
    except Exception as e:
        print("[ENCODING ERROR] Operation '%s' failed: %s" % (operation, str(e)))
        return fallback_value


def safe_json_parse(json_string, default=None):
    """
    安全的 JSON 解析
    
    Args:
        json_string: JSON 字符串
        default: 解析失败时的默认返回值
    
    Returns:
        解析后的对象或 default
    """
    import json
    
    if not json_string or not isinstance(json_string, (str, unicode)):
        return default
    
    try:
        return json.loads(json_string)
    except ValueError as e:
        print("[JSON PARSE ERROR] Invalid JSON: %s" % str(e)[:100])
        return default
    except Exception as e:
        print("[JSON PARSE ERROR] Unexpected error: %s" % str(e))
        return default


def safe_get_text_field(text_field, default=""):
    """
    安全获取文本框内容
    
    Args:
        text_field: Swing 文本组件
        default: 获取失败时的默认值
    
    Returns:
        文本内容或 default
    """
    if text_field is None:
        return default
    
    try:
        text = text_field.getText()
        if text is None:
            return default
        return str(text).strip()
    except Exception as e:
        print("[UI ERROR] Failed to get text field value: %s" % str(e))
        return default


def log_exception(exception, context="", level="ERROR"):
    """
    统一的异常日志记录
    
    Args:
        exception: 异常对象
        context: 异常上下文描述
        level: 日志级别 (ERROR, WARNING, INFO)
    """
    import sys
    import traceback
    
    separator = "=" * 80
    print(separator)
    print("[%s] Exception occurred" % level)
    
    if context:
        print("Context: %s" % context)
    
    print("Exception Type: %s" % type(exception).__name__)
    print("Exception Message: %s" % str(exception))
    
    # 只在 ERROR 级别打印完整堆栈
    if level == "ERROR":
        try:
            # Jython 2.7 compatible traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            if exc_traceback:
                tb_lines = traceback.format_tb(exc_traceback)
                print("Traceback:")
                for line in tb_lines[-5:]:  # 只显示最后5行
                    print("  " + line.strip())
        except Exception:
            pass
    
    print(separator)


# ============================================================================
# 上下文管理器
# ============================================================================

class SuppressAndLog(object):
    """
    抑制异常并记录日志的上下文管理器
    
    用法:
        with SuppressAndLog("Cache operation", return_value=""):
            # 可能抛出异常的代码
            result = risky_operation()
    """
    def __init__(self, context="", return_value=None, log_level="WARNING"):
        self.context = context
        self.return_value = return_value
        self.log_level = log_level
        self.exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.exception = exc_val
            log_exception(exc_val, self.context, self.log_level)
            return True  # 抑制异常
        return False


# ============================================================================
# 常用异常检查函数
# ============================================================================

def is_network_error(exception):
    """判断是否为网络相关错误"""
    error_msg = str(exception).lower()
    network_indicators = [
        'connection', 'timeout', 'network', 'socket',
        'unreachable', 'refused', 'reset', 'broken pipe'
    ]
    return any(indicator in error_msg for indicator in network_indicators)


def is_encoding_error(exception):
    """判断是否为编码相关错误"""
    return isinstance(exception, (UnicodeDecodeError, UnicodeEncodeError))


def should_retry(exception, retry_count, max_retries=3):
    """
    判断异常是否应该重试
    
    Args:
        exception: 异常对象
        retry_count: 当前重试次数
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否应该重试
    """
    if retry_count >= max_retries:
        return False
    
    # 网络错误可以重试
    if is_network_error(exception):
        return True
    
    # 临时性错误可以重试
    temp_errors = ['rate limit', 'too many requests', '503', '502', '504']
    error_msg = str(exception).lower()
    
    return any(temp in error_msg for temp in temp_errors)


# ============================================================================
# 异常恢复策略
# ============================================================================

def with_fallback(primary_func, fallback_func, *args, **kwargs):
    """
    执行主函数，失败时执行降级函数
    
    Args:
        primary_func: 主函数
        fallback_func: 降级函数
        *args, **kwargs: 传递给函数的参数
    
    Returns:
        主函数结果或降级函数结果
    """
    try:
        return primary_func(*args, **kwargs)
    except Exception as e:
        print("[FALLBACK] Primary function failed, using fallback: %s" % str(e))
        try:
            return fallback_func(*args, **kwargs)
        except Exception as e2:
            print("[FALLBACK ERROR] Fallback also failed: %s" % str(e2))
            return None


# ============================================================================
# 示例用法（供其他模块参考）
# ============================================================================

if __name__ == "__main__":
    # 示例 1: 使用装饰器
    @safe_execute(default_return={}, log_error=True, error_prefix="Example")
    def risky_function():
        return {"key": "value"}
    
    # 示例 2: 使用上下文管理器
    def risky_operation():
        raise ValueError("Test error")
    
    with SuppressAndLog("Example operation"):
        risky_operation()
    
    # 示例 3: 使用编码处理
    data = u"测试数据"  # Jython 2.7: 使用 unicode 字符串
    encoded = handle_encoding_error(data, operation="encode")
    
    # 示例 4: 使用 JSON 解析
    result = safe_json_parse('{"key": "value"}', default={})

