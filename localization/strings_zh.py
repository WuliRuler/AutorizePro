#!/usr/bin/env python3
# coding: utf-8

"""
@File   : strings_zh.py
@Author : sule01u
@Date   : 2024/10/10
@Desc   : 中文选项卡文字
"""

# 使用Unicode编码确保中文字符在Jython/Java环境中正确显示

STRINGS = {
    # 扩展名称和选项卡
    "extension_name": "AutorizePro",
    "tab_results": u"请求/响应查看器",
    "tab_configuration": u"配置",
    
    # 配置选项卡
    "config_title": u"配置",
    "config_desc": u"配置AutorizePro将修改的请求头",
    "injected_header_label": u"在此处插入注入的请求头:",
    "fetch_cookie_button": u"获取Cookie请求头",
    "fetch_authorization_button": u"获取认证请求头",
    "check_unauthenticated": u"检查未授权请求",
    "check_unauthenticated_tooltip": u"添加一个不带认证头的额外请求（完全未认证）",
    "intercept_from_repeater": u"拦截来自Repeater的请求",
    "autoresponder": u"自动响应器",
    "autorize_is_off": u"AutorizePro 已关闭",
    "autorize_is_on": u"AutorizePro 已启用",
    "clear_button": u"清空列表",
    "auto_scroll": u"结果滚动显示",
    "ignore_304": u"忽略304/204状态码响应",
    "prevent_304": u"阻止304未修改状态码",
    "replace_query_params": u"替换参数方式测试越权",
    "from_last_request": u"从最近的请求:",
    "expand": u"展开",
    "collapse": u"折叠",
    
    # 表格头
    "table_url": "URL",
    "table_method": u"方法",
    "table_status": u"认证状态",
    "table_length": u"长度",
    "table_time": u"时间",
    "table_originals": u"原始请求",
    "table_modified": u"修改后请求",
    "table_modified_response": u"修改后响应",
    "table_unauthorized": u"未授权请求",
    "table_unauthorized_response": u"未授权响应",
    "table_originals_response": u"原始响应",
    "table_ai_analyzer": u"AI分析",
    "table_originals_len": u"原始长度",
    "table_modified_len": u"修改长度",
    "table_unauthorized_len": u"未授权长度",
    "table_unauthorized_status": u"未授权状态",
    
    # 认证检测器
    "enforcement_detector": u"已鉴权验证规则",
    "enforcement_detector_unauthorized": u"未授权验证规则",
    "enforcement_detector_tooltip": u"指定如何判断授权失败的条件",
    "detector_options": u"检测选项",
    "detector_strings": u"特征字符串",
    "detector_content_length": u"响应长度",
    "detector_status_code": u"HTTP状态码",
    
    # 匹配/替换
    "match_replace": u"匹配/替换",
    "match_replace_tooltip": u"定义修改请求的规则",
    "match_string": u"匹配字符串",
    "replace_string": u"替换字符串",
    
    # 请求过滤规则
    "interception_filters": u"请求过滤规则",
    "interception_filters_tooltip": u"配置需要进行权限测试的请求条件",
    "filter_type": u"筛选条件",
    "filter_string": u"匹配内容",
    
    # 保存/恢复
    "save_restore": u"保存/恢复",
    "save_button": u"保存当前配置",
    "restore_button": u"导入历史配置",
    "export_button": u"导出",
    "export_results_section": u"导出测试结果",
    "config_section": u"插件配置管理",
    "export_file_type": u"文件类型:",
    "export_statuses": u"状态过滤:",
    "remove_duplicates": u"移除重复项",
    "table_filter": u"结果状态过滤",
    "filter_modified": u"修改请求:",
    "filter_unauthenticated": u"未授权请求:",
    "filter_ai_analyzed": u"AI分析结果:",
    "all_statuses": u"所有状态",
    "as_table_filter": u"复用结果状态过滤配置",
    
    # 导出功能相关
    "export_no_entries": u"没有可导出的测试结果",
    "export_no_matches": u"没有符合过滤条件的测试结果",
    "export_failed": u"导出失败",
    "export_empty": u"导出为空",
    "export_success": u"导出成功",
    "export_error": u"导出错误",
    "export_success_message": u"已成功导出 ",
    "export_entries": u" 条测试结果",
    "export_error_message": u"导出报告失败: ",
    "filter_disabled": u"已禁用",
    
    # AI分析器
    "ai_analyzer": u"AI分析器",
    "ai_key": u"API密钥",
    "ai_model": u"模型",
    "ai_api_url": u"API地址（可选）",
    "ai_api_url_label": u"URL:",
    "ai_api_url_placeholder": u"http://localhost:11434/v1/chat/completions",
    "ai_api_url_tooltip": u"留空使用默认API地址。设置自定义地址以支持私有大模型部署（例如：Ollama使用 http://localhost:11434/v1/chat/completions）。",
    
    # 认证头配置
    "auth_headers_label": u"认证头类型配置:",
    "auth_headers_tooltip": u"使用逗号分隔多个认证头类型名称",
    "update_auth_headers": u"更新",
    "auth_headers_updated": u"认证头类型已成功更新",
    "auth_headers_reset": u"已重置为默认认证头类型",
    
    # 语言设置
    "language_settings": u"语言设置:",
    "language_select": u"选择语言",
    "language_en": u"英文",
    "language_zh": u"中文",
    "language_toggle": u"EN/中",
    "language_changed": u"语言已成功更改",
    "apply_language": u"应用",
    
    # 模型验证相关
    "model_empty": u"模型名称不能为空",
    "unsupported_model": u"暂不支持该厂商模型，请联系开发者",
    "warning": u"警告",
    "enable_ai": u"启用AI",
} 