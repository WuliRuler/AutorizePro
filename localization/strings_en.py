#!/usr/bin/env python3
# coding: utf-8

"""
@File   : strings_en.py
@Author : sule01u
@Date   : 2024/10/10
@Desc   : 英语选项卡文字
"""

# Main UI strings
STRINGS = {
    # Extension name and tabs
    "extension_name": "AutorizePro",
    "tab_results": "Request/Response Viewers",
    "tab_configuration": "Configuration",
    
    # Configuration tab
    "config_title": "Configuration",
    "config_desc": "Configure which headers will be modified by AutorizePro",
    "injected_header_label": "Insert injected header here:",
    "fetch_cookie_button": "Fetch Cookies header",
    "fetch_authorization_button": "Fetch Authorization header",
    "check_unauthenticated": "Check unauthenticated",
    "check_unauthenticated_tooltip": "Adds an additional request without authorization header (completely unauthenticated)",
    "intercept_from_repeater": "Intercept requests from Repeater",
    "autoresponder": "Auto Responder",
    "autorize_is_off": "AutorizePro is off",
    "autorize_is_on": "AutorizePro is on",
    "clear_button": "Clear List",
    "auto_scroll": "Auto Scroll",
    "ignore_304": "Ignore 304/204 status code responses",
    "prevent_304": "Prevent 304 Not Modified status code",
    "replace_query_params": "Replace query params",
    "from_last_request": "From last request:",
    "expand": "Expand",
    "collapse": "Collapse",
    
    # Table headers
    "table_url": "URL",
    "table_method": "Method",
    "table_status": "Authz. Status",
    "table_length": "Length",
    "table_time": "Time",
    "table_originals": "Original Request",
    "table_modified": "Modified Request",
    "table_modified_response": "Modified Response",
    "table_unauthorized": "Unauthorized Request",
    "table_unauthorized_response": "Unauthorized Response",
    "table_originals_response": "Original Response",
    "table_ai_analyzer": "AI Analyzer",
    "table_originals_len": "Orig. Len",
    "table_modified_len": "Modif. Len",
    "table_unauthorized_len": "Unauth. Len",
    "table_unauthorized_status": "Unauth. Status",
    
    # Status messages
    "status_bypassed": "Bypassed!",
    "status_enforced": "Enforced!",
    "status_is_enforced": "Is enforced???",
    
    # Enforcement detector
    "enforcement_detector": "Privilege Enforcement Rules",
    "enforcement_detector_unauthorized": "Unauthorized Enforcement Rules",
    "enforcement_detector_tooltip": "Indicate how to identify a failed authorization",
    "detector_options": "Options",
    "detector_strings": "Strings",
    "detector_content_length": "Content Length",
    "detector_status_code": "Status Code",
    
    # Match/Replace
    "match_replace": "Match/Replace",
    "match_replace_tooltip": "Define rules for modifying requests",
    "match_string": "Match String",
    "replace_string": "Replace String",
    
    # Interception filters
    "interception_filters": "Interception Filters",
    "interception_filters_tooltip": "Configure which domains to test",
    "filter_type": "Filter Type",
    "filter_string": "Filter String",
    
    # Save/Restore
    "save_restore": "Save/Restore",
    "save_button": "Save Current Config",
    "restore_button": "Import Saved Config",
    "export_button": "Export",
    "export_results_section": "Export Test Results",
    "config_section": "Configuration Management",
    "export_file_type": "File Type:",
    "export_statuses": "Statuses:",
    "remove_duplicates": "Remove Duplicates",
    "table_filter": "Table Filter",
    "filter_modified": "Modified:",
    "filter_unauthenticated": "Unauthenticated:",
    "filter_ai_analyzed": "AI.Analyzed:",
    "filter_disabled": "Disabled",
    "all_statuses": "All Statuses",
    "as_table_filter": "As table filter",
    
    # Export related strings
    "export_no_entries": "No entries to export",
    "export_no_matches": "No entries match the filter criteria",
    "export_failed": "Export Failed",
    "export_empty": "Export Empty",
    "export_success": "Export Success",
    "export_error": "Export Error",
    "export_success_message": "Successfully exported ",
    "export_entries": " entries",
    "export_error_message": "Failed to export report: ",
    
    # AI analyzer
    "ai_analyzer": "AI Analyzer",
    "ai_key": "API Key",
    "ai_model": "Model",
    "ai_api_url": "API URL (Optional)",
    "ai_api_url_label": "URL:",
    "ai_api_url_placeholder": "http://localhost:11434/v1/chat/completions",
    "ai_api_url_tooltip": "Leave empty to use default API endpoint. Set custom URL for private model deployment (e.g., http://localhost:11434/v1/chat/completions for Ollama).",
    "enable_ai": "Enable AI",
    
    # Authentication headers
    "auth_headers_label": "Authentication Headers:",
    "auth_headers_tooltip": "Comma-separated list of authentication header names",
    "update_auth_headers": "Update",
    "auth_headers_updated": "Authentication headers updated successfully",
    "auth_headers_reset": "Reset to default authentication headers",
    
    # Language settings
    "language_settings": "Language Settings:",
    "language_select": "Select Language",
    "language_en": "English",
    "language_zh": "Chinese",
    "language_toggle": u"EN/中",
    "language_changed": "Language changed successfully.",
    "apply_language": "Apply",
    
    # Model validation
    "model_empty": "Model name cannot be empty",
    "unsupported_model": "Unsupported model vendor, please contact developer",
    "warning": "Warning"
} 