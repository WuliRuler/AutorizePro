#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File   : authorization.py
@Author : sule01u
@Date   : 2024/10/10
@Desc   : 
"""

import sys
import re
import datetime
import time
import hashlib
import json
from java.net import URL, HttpURLConnection
from java.io import BufferedReader, InputStreamReader, OutputStreamWriter, EOFException, IOException
from java.lang import StringBuilder
from javax.swing import SwingUtilities
from javax.net.ssl import SSLHandshakeException, SSLSocketFactory
from java.net import SocketException
from javax.swing.event import DocumentListener
from threading import Lock

reload(sys)

if (sys.version_info[0] == 2):
    sys.setdefaultencoding('utf8')

sys.path.append("..")

from helpers.http import (
    get_authorization_header_from_message,
    get_cookie_header_from_message,
    isStatusCodesReturned,
    makeMessage,
    makeRequest,
    getRequestBody,
    getResponseBody,
    IHttpRequestResponseImplementation
)

from gui.table import LogEntry, UpdateTableEDT

CODE_BLOCK_PATTERN = re.compile(r'```(?:json)?(.*?)```', re.DOTALL)
RES_FIELD_PATTERN = re.compile(r'[\'\"]res[\'\"]:\s*[\'\"](\w+)[\'\"]', re.IGNORECASE)
JSON_RES_PATTERN = re.compile(r'"res":\s*"(\w+)"')
ESCAPED_JSON_RES_PATTERN = re.compile(r'\\"res\\":\s*\\"(\w+)\\"')
NESTED_RES_PATTERN = re.compile(r'"content":\s*".*?[\'\"]res[\'\"]:\s*[\'\"](\w+)[\'\"].*?"', re.DOTALL)
MARKDOWN_JSON_PATTERN = re.compile(r'"content":\s*"{\\?"res\\?":\s*\\?"(\w+)\\?"')
CHOICES_CONTENT_PATTERN = re.compile(r'"choices":\s*\[\s*{.*?"message":\s*{.*?"content":\s*".*?res.*?(\w+).*?"', re.DOTALL)
HUNYUAN_PATTERN = re.compile(r'"content"\s*:\s*"```json\\\\n{\\\\"res\\\\":\\\\"(\w+)\\\\"')
QIANWEN_PATTERN = re.compile(r'content.*?```.*?res.*?[\'"](\w+)[\'"].*?```', re.DOTALL)
GLM_PATTERN = re.compile(r'content.*?res.*?[\'"](\w+)[\'"]', re.DOTALL)
LOOSE_PATTERN = re.compile(r'[\'"]res[\'"]:\s*[\'"](\w+)[\'"]|"res":\s*"(\w+)"|\\+"res\\+":\s*\\+"(\w+)\\+"', re.IGNORECASE | re.DOTALL)
HUNYUAN_CONTENT_PATTERN = re.compile(r'"choices":\s*\[\s*{\s*"index":\s*\d+,\s*"message":\s*{\s*"role":\s*"assistant",\s*"content":\s*"(.*?)"', re.DOTALL)

ai_analysis_cache = {}
MAX_CACHE_SIZE = 100
cache_lock = Lock()
logged_html_urls = set()
logged_urls_lock = Lock()
cache_access_order = []

def tool_needs_to_be_ignored(self, toolFlag):
    for i in range(0, self.IFList.getModel().getSize()):
        if self.IFList.getModel().getElementAt(i).split(":")[0] == "Ignore spider requests":
            if toolFlag == self._callbacks.TOOL_SPIDER:
                return True
        if self.IFList.getModel().getElementAt(i).split(":")[0] == "Ignore proxy requests":
            if toolFlag == self._callbacks.TOOL_PROXY:
                return True
        if self.IFList.getModel().getElementAt(i).split(":")[0] == "Ignore target requests":
            if toolFlag == self._callbacks.TOOL_TARGET:
                return True
    return False


def capture_last_cookie_header(self, messageInfo):
    cookies = get_cookie_header_from_message(self, messageInfo)
    if cookies:
        self.lastCookiesHeader = cookies
        self.fetchCookiesHeaderButton.setEnabled(True)


def capture_last_authorization_header(self, messageInfo):
    authorization = get_authorization_header_from_message(self, messageInfo)
    if authorization:
        self.lastAuthorizationHeader = authorization
        self.fetchAuthorizationHeaderButton.setEnabled(True)


def valid_tool(self, toolFlag):
    return (toolFlag == self._callbacks.TOOL_PROXY or
            (toolFlag == self._callbacks.TOOL_REPEATER and
             self.interceptRequestsfromRepeater.isSelected()))


def handle_304_status_code_prevention(self, messageIsRequest, messageInfo):
    should_prevent = False

    if self.prevent304.isSelected():
        if messageIsRequest:
            requestHeaders = list(self._helpers.analyzeRequest(messageInfo).getHeaders())
            newHeaders = []

            for header in requestHeaders:
                if "If-None-Match:" not in header and "If-Modified-Since:" not in header:
                    newHeaders.append(header)
                    should_prevent = True

        if should_prevent:
            requestInfo = self._helpers.analyzeRequest(messageInfo)
            bodyBytes = messageInfo.getRequest()[requestInfo.getBodyOffset():]

            bodyStr = self._helpers.bytesToString(bodyBytes)

            messageInfo.setRequest(self._helpers.buildHttpMessage(newHeaders, bodyStr))


def message_not_from_autorize(self, messageInfo):
    return self.replaceString.getText() not in self._helpers.analyzeRequest(messageInfo).getHeaders()


def no_filters_defined(self):
    return self.IFList.getModel().getSize() == 0


def message_passed_interception_filters(self, messageInfo):
    urlString = str(self._helpers.analyzeRequest(messageInfo).getUrl())
    reqInfo = self._helpers.analyzeRequest(messageInfo)
    reqBodyBytes = messageInfo.getRequest()[reqInfo.getBodyOffset():]
    bodyStr = self._helpers.bytesToString(reqBodyBytes)

    resInfo = self._helpers.analyzeResponse(messageInfo.getResponse())
    resBodyBytes = messageInfo.getResponse()[resInfo.getBodyOffset():]
    resStr = self._helpers.bytesToString(resBodyBytes)

    message_passed_filters = True
    rule_count = self.IFList.getModel().getSize()
    
    if rule_count == 0:
        return True
    
    for i in range(0, rule_count):
        interceptionFilter = self.IFList.getModel().getElementAt(i)
        
        # 提取过滤器标题和用户定义的规则
        filter_parts = interceptionFilter.split(":", 1)
        interceptionFilterTitle = filter_parts[0].strip()
        filter_content = filter_parts[1].strip() if len(filter_parts) > 1 else ""
        
        rule_matched = True  # 假设规则匹配
        
        if interceptionFilterTitle == "Scope items only":
            currentURL = URL(urlString)
            if not self._callbacks.isInScope(currentURL):
                rule_matched = False

        if interceptionFilterTitle == "URL Contains (simple string)":
            if filter_content not in urlString:
                rule_matched = False

        if interceptionFilterTitle == "URL Contains (regex)":
            if re.search(filter_content, urlString, re.IGNORECASE) is None:
                rule_matched = False

        if interceptionFilterTitle == "URL Not Contains (simple string)":
            if filter_content in urlString:
                rule_matched = False

        if interceptionFilterTitle == "URL Not Contains (regex)":
            if not re.search(filter_content, urlString, re.IGNORECASE) is None:
                rule_matched = False

        if interceptionFilterTitle == "Request Body contains (simple string)":
            if filter_content not in bodyStr:
                rule_matched = False

        if interceptionFilterTitle == "Request Body contains (regex)":
            if re.search(filter_content, bodyStr, re.IGNORECASE) is None:
                rule_matched = False

        if interceptionFilterTitle == "Request Body NOT contains (simple string)":
            if filter_content in bodyStr:
                rule_matched = False

        if interceptionFilterTitle == "Request Body Not contains (regex)":
            if not re.search(filter_content, bodyStr, re.IGNORECASE) is None:
                rule_matched = False

        if interceptionFilterTitle == "Response Body contains (simple string)":
            if filter_content not in resStr:
                rule_matched = False

        if interceptionFilterTitle == "Response Body contains (regex)":
            if re.search(filter_content, resStr, re.IGNORECASE) is None:
                rule_matched = False

        if interceptionFilterTitle == "Response Body NOT contains (simple string)":
            if filter_content in resStr:
                rule_matched = False

        if interceptionFilterTitle == "Response Body Not contains (regex)":
            if not re.search(filter_content, resStr, re.IGNORECASE) is None:
                rule_matched = False

        if interceptionFilterTitle == "Header contains":
            for header in list(resInfo.getHeaders()):
                if filter_content in header:
                    rule_matched = False
                    break

        if interceptionFilterTitle == "Header doesn't contain":
            for header in list(resInfo.getHeaders()):
                if not filter_content in header:
                    rule_matched = False
                    break

        if interceptionFilterTitle == "Only HTTP methods (newline separated)":
            filterMethods = filter_content.split("\n")
            filterMethods = [x.lower() for x in filterMethods]
            reqMethod = str(self._helpers.analyzeRequest(messageInfo).getMethod())
            if reqMethod.lower() not in filterMethods:
                rule_matched = False

        if interceptionFilterTitle == "Ignore HTTP methods (newline separated)":
            filterMethods = filter_content.split("\n")
            filterMethods = [x.lower() for x in filterMethods]
            reqMethod = str(self._helpers.analyzeRequest(messageInfo).getMethod())
            if reqMethod.lower() in filterMethods:
                rule_matched = False

        if interceptionFilterTitle == "Ignore OPTIONS requests":
            reqMethod = str(self._helpers.analyzeRequest(messageInfo).getMethod())
            if reqMethod == "OPTIONS":
                rule_matched = False
        
        # 规则匹配and关系
        if not rule_matched:
            message_passed_filters = False
            break
    
    return message_passed_filters


def handle_message(self, toolFlag, messageIsRequest, messageInfo):
    if tool_needs_to_be_ignored(self, toolFlag):
        return

    capture_last_cookie_header(self, messageInfo)
    capture_last_authorization_header(self, messageInfo)

    if (self.intercept and valid_tool(self, toolFlag)) or toolFlag == "AUTORIZEPRO":
        handle_304_status_code_prevention(self, messageIsRequest, messageInfo)

        if not messageIsRequest:
            if message_not_from_autorize(self, messageInfo):
                if self.ignore304.isSelected():
                    if isStatusCodesReturned(self, messageInfo, ["304", "204"]):
                        return
                if no_filters_defined(self):
                    checkAuthorization(self, messageInfo,
                                       self._helpers.analyzeResponse(messageInfo.getResponse()).getHeaders(),
                                       self.doUnauthorizedRequest.isSelected())
                else:
                    if message_passed_interception_filters(self, messageInfo):
                        checkAuthorization(self, messageInfo,
                                           self._helpers.analyzeResponse(messageInfo.getResponse()).getHeaders(),
                                           self.doUnauthorizedRequest.isSelected())


def send_request_to_autorize(self, messageInfo):
    if messageInfo.getResponse() is None:
        message = makeMessage(self, messageInfo, False, False)
        requestResponse = makeRequest(self, messageInfo, message)
        checkAuthorization(self, requestResponse,
                           self._helpers.analyzeResponse(requestResponse.getResponse()).getHeaders(),
                           self.doUnauthorizedRequest.isSelected())
    else:
        request = messageInfo.getRequest()
        response = messageInfo.getResponse()
        httpService = messageInfo.getHttpService()
        newHttpRequestResponse = IHttpRequestResponseImplementation(httpService, request, response)
        newHttpRequestResponsePersisted = self._callbacks.saveBuffersToTempFiles(newHttpRequestResponse)
        checkAuthorization(self, newHttpRequestResponsePersisted,
                           self._helpers.analyzeResponse(messageInfo.getResponse()).getHeaders(),
                           self.doUnauthorizedRequest.isSelected())


def auth_enforced_via_enforcement_detectors(self, filters, requestResponse, andOrEnforcement):
    response = requestResponse.getResponse()
    analyzedResponse = self._helpers.analyzeResponse(response)
    auth_enforced = False
    if andOrEnforcement == "And":
        andEnforcementCheck = True
        auth_enforced = True
    else:
        andEnforcementCheck = False
        auth_enforced = False

    for filter in filters:
        filter = self._helpers.bytesToString(bytes(filter))
        filter_kv = filter.split(":", 1)
        inverse = "NOT" in filter_kv[0]
        filter_kv[0] = filter_kv[0].replace(" NOT", "")
        filter = ":".join(filter_kv)

        if filter.startswith("Status code equals: "):
            statusCode = filter[20:]
            filterMatched = inverse ^ isStatusCodesReturned(self, requestResponse, statusCode)

        elif filter.startswith("Headers (simple string): "):
            filterMatched = inverse ^ (filter[25:] in self._helpers.bytesToString(
                requestResponse.getResponse()[0:analyzedResponse.getBodyOffset()]))

        elif filter.startswith("Headers (regex): "):
            regex_string = filter[17:]
            p = re.compile(regex_string, re.IGNORECASE)
            filterMatched = inverse ^ bool(p.search(
                self._helpers.bytesToString(requestResponse.getResponse()[0:analyzedResponse.getBodyOffset()])))

        elif filter.startswith("Body (simple string): "):
            filterMatched = inverse ^ (filter[22:] in self._helpers.bytesToString(
                requestResponse.getResponse()[analyzedResponse.getBodyOffset():]))

        elif filter.startswith("Body (regex): "):
            regex_string = filter[14:]
            p = re.compile(regex_string, re.IGNORECASE)
            filterMatched = inverse ^ bool(
                p.search(self._helpers.bytesToString(requestResponse.getResponse()[analyzedResponse.getBodyOffset():])))

        elif filter.startswith("Full response (simple string): "):
            filterMatched = inverse ^ (filter[31:] in self._helpers.bytesToString(requestResponse.getResponse()))

        elif filter.startswith("Full response (regex): "):
            regex_string = filter[23:]
            p = re.compile(regex_string, re.IGNORECASE)
            filterMatched = inverse ^ bool(p.search(self._helpers.bytesToString(requestResponse.getResponse())))

        elif filter.startswith("Full response length: "):
            filterMatched = inverse ^ (str(len(response)) == filter[22:].strip())

        if andEnforcementCheck:
            if auth_enforced and not filterMatched:
                auth_enforced = False
        else:
            if not auth_enforced and filterMatched:
                auth_enforced = True

    return auth_enforced


def pre_check(self, oldStatusCode, newStatusCode, oldContent, newContent, modifyFlag, oriUrl="Unknown URL", request_type="modified"):
    """
    优化过的前置检查函数，用于判断请求是否需要进一步处理
    
    Args:
        oldStatusCode: 原始请求的状态码
        newStatusCode: 修改请求的状态码
        oldContent: 原始响应内容
        newContent: 修改后的响应内容
        modifyFlag: 是否对请求进行了修改
        oriUrl: 原始URL，用于日志记录
        request_type: 请求类型（modified/unauthorized）
    
    Returns:
        bool: 是否通过前置检查
    """
    try:
        if not oldStatusCode or not newStatusCode:
            return False
            
        allowed_status_codes = {"200", "201", "202", "204"}
        redirect_status_codes = {"301", "302", "303", "307", "308"}
        
        all_allowed_codes = allowed_status_codes.union(redirect_status_codes)
            
        try:
            status_parts = newStatusCode.split(" ", 2)
            if len(status_parts) >= 2:
                statusCode = status_parts[1].strip()
            else:
                statusCode = newStatusCode
        except (IndexError, AttributeError) as e:
            return False
            
        if statusCode not in all_allowed_codes:
            return False
            
        if not modifyFlag:
            return False
            
        content_type_check = False
        try:
            old_type_valid = detect_response_type(self, oldContent, oriUrl)
            if old_type_valid:
                new_type_valid = detect_response_type(self, newContent, oriUrl)
                if new_type_valid:
                    content_type_check = True
        except Exception as e:
            return False
            
        if not content_type_check:
            with logged_urls_lock:
                if oriUrl not in logged_html_urls:
                    logged_html_urls.add(oriUrl)
                    if len(logged_html_urls) > 1000:
                        oldest_urls = list(logged_html_urls)[:200]
                        for old_url in oldest_urls:
                            logged_html_urls.remove(old_url)
            return False
            
        MIN_CONTENT_SIZE = 10
        if len(oldContent) < MIN_CONTENT_SIZE or len(newContent) < MIN_CONTENT_SIZE:
            return False
            
        return True
    except Exception as e:
        return False


def checkBypass(self, oriUrl, oriBody, oldStatusCode, newStatusCode, oldContent, newContent, filters, requestResponse,
                andOrEnforcement, isAuthorized):
    AI_res = ""
    if isAuthorized and self.apiKeyEnabledCheckbox.isSelected():
        if newStatusCode == oldStatusCode and 50 < len(oldContent) < 7000:
            # 改进缓存键生成机制，减少哈希碰撞风险
            try:
                # 为URL生成一个哈希值
                url_hash = str(hash(oriUrl))
                
                # 计算内容的4个采样点（前部、1/3处、2/3处、尾部）
                old_len = len(oldContent)
                new_len = len(newContent)
                
                old_third = old_len // 3
                new_third = new_len // 3
                
                old_samples = [
                    oldContent[:50],
                    oldContent[old_third:old_third+50] if old_len > 150 else "",
                    oldContent[2*old_third:2*old_third+50] if old_len > 300 else "",
                    oldContent[-50:] if old_len > 50 else ""
                ]
                
                new_samples = [
                    newContent[:50],
                    newContent[new_third:new_third+50] if new_len > 150 else "",
                    newContent[2*new_third:2*new_third+50] if new_len > 300 else "",
                    newContent[-50:] if new_len > 50 else ""
                ]
                
                hasher = hashlib.md5()
                hasher.update(url_hash.encode('utf-8'))
                hasher.update(str(oldStatusCode).encode('utf-8'))
                hasher.update(str(newStatusCode).encode('utf-8'))
                hasher.update(str(old_len).encode('utf-8'))
                hasher.update(str(new_len).encode('utf-8'))
                
                for sample in old_samples + new_samples:
                    if sample:
                        try:
                            hasher.update(sample.encode('utf-8'))
                        except UnicodeDecodeError:
                            hasher.update(str(hash(sample)).encode('utf-8'))
                
                cache_key = hasher.hexdigest()
                
            except Exception as e:
                cache_key = str(hash(oriUrl))
                print("Error generating cache key: " + str(e))
            
            # 使用锁保护缓存访问操作
            cache_hit = False
            with cache_lock:
                if cache_key in ai_analysis_cache:
                    AI_res = ai_analysis_cache[cache_key]
                    if cache_key in cache_access_order:
                        cache_access_order.remove(cache_key)
                    cache_access_order.append(cache_key)
                    cache_hit = True
                    cache_hit_json = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "action": "cache_hit",
                        "url": str(oriUrl),  # 确保转换为字符串
                        "result": AI_res
                    }
                    print("Cache Hit: " + json.dumps(cache_hit_json, ensure_ascii=False))

            # 只有在缓存未命中时才执行API调用
            if not cache_hit:
                apiKey = self.apiKeyField.getText()
                try:
                    modelName = self.aiModelTextField.getText()
                except:
                    modelName = None
                    
                if apiKey and modelName:
                    api_result_mapping = {
                        "true": self.BYPASSSED_STR,
                        "false": self.ENFORCED_STR,
                        "unknown": self.IS_ENFORCED_STR
                    }
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    api_request_json = {
                        "timestamp": timestamp,
                        "action": "api_request",
                        "url": str(oriUrl),
                        "model": modelName
                    }
                    print("API Request: " + json.dumps(api_request_json, ensure_ascii=False))
                    
                    AI_result = call_dashscope_api(self, apiKey, modelName, oriUrl, oriBody, oldContent, newContent)
                    AI_res = api_result_mapping.get(AI_result, AI_result)
                    
                    api_result_json = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "action": "api_result",
                        "url": str(oriUrl),
                        "result": AI_result,
                        "mapped_value": AI_res
                    }
                    print("API Result: " + json.dumps(api_result_json, ensure_ascii=False))
                    
                    # 缓存结果时获取锁
                    if AI_res:  # 只在有结果时缓存
                        with cache_lock:
                            ai_analysis_cache[cache_key] = AI_res
                            if cache_key in cache_access_order:
                                cache_access_order.remove(cache_key)
                            cache_access_order.append(cache_key)
                            
                            if len(ai_analysis_cache) > MAX_CACHE_SIZE:
                                try:
                                    if cache_access_order:
                                        oldest_key = cache_access_order.pop(0)
                                        if oldest_key in ai_analysis_cache:
                                            ai_analysis_cache.pop(oldest_key)
                                except Exception as e:
                                    print("Error managing cache: " + str(e))

    auth_enforced = False
    if filters:
        auth_enforced = auth_enforced_via_enforcement_detectors(self, filters, requestResponse, andOrEnforcement)

    if auth_enforced:
        return self.ENFORCED_STR, AI_res
    elif len(oldContent) == len(newContent):
        return self.BYPASSSED_STR, AI_res
    else:
        return self.IS_ENFORCED_STR, AI_res


def detect_response_type(self, content, current_url="unknown"):
    """
    检测响应内容类型，确定是否为JSON或XML格式
    优化过的函数，增强了对二进制数据的检测，提高处理效率
    """
    if content is None or len(content) == 0:
        return False
    
    try:
        if isinstance(content, (bytes, bytearray)):
            # 检测常见二进制文件头部特征
            if len(content) > 8:
                binary_signatures = {
                    b'%PDF': "PDF binary data",
                    b'\x89PNG': "PNG image",
                    b'\xff\xd8\xff': "JPEG image",
                    b'GIF8': "GIF image",
                    b'PK\x03\x04': "ZIP/Office document",
                    b'\x50\x4b\x03\x04': "ZIP/Office document",
                    b'BM': "BMP image",
                    b'\x7fELF': "ELF binary",
                    b'MZ': "PE/EXE binary",
                    b'\x1f\x8b': "GZIP archive",
                    b'Rar!': "RAR archive",
                    b'SQLite': "SQLite database",
                    b'\xd0\xcf\x11\xe0': "MS Office document"
                }
                
                for signature, file_type in binary_signatures.items():
                    if content.startswith(signature):
                        return False
                
                if len(content) >= 100:
                    unprintable_count = sum(1 for b in content[:100] if b < 32 or b > 126)
                    if unprintable_count > 30:
                        return False
        
        content_type_detected = False
        try:
            if hasattr(content, 'lower'):
                content_lower = content.lower()
                content_type_match = re.search(r'content-type:\s*([^\r\n]+)', content_lower[:500])
                if content_type_match:
                    content_type = content_type_match.group(1).strip()
                    
                    json_types = ['application/json', 'text/json', 'application/ld+json', 'application/problem+json']
                    xml_types = ['application/xml', 'text/xml', 'application/xhtml+xml', 'application/soap+xml']
                    
                    if any(jtype in content_type for jtype in json_types):
                        return True
                    
                    if any(xtype in content_type for xtype in xml_types):
                        return True
                    
                    if 'text/html' in content_type:
                        with logged_urls_lock:
                            if current_url not in logged_html_urls:
                                logged_html_urls.add(current_url)
                                # 限制集合大小
                                if len(logged_html_urls) > 1000:
                                    logged_html_urls.clear()
                        return False
                    
                    # 快速过滤明显的二进制内容类型
                    binary_types = ['image/', 'audio/', 'video/', 'application/pdf', 'application/zip', 
                                   'application/octet-stream', 'application/x-msdownload', 
                                   'application/vnd.ms-', 'application/x-gzip', 'font/', 
                                   'application/java-archive', 'application/x-shockwave-flash']
                    if any(btype in content_type for btype in binary_types):
                        return False
                    
                    content_type_detected = True
        except Exception as ct_error:
            pass
            
        # 如果无法通过Content-Type确定，再尝试规范化内容并检测特征
        try:
            if isinstance(content, (str, unicode)):
                norm_content = content.strip()
            else:
                encodings = ['utf-8', 'latin-1', 'gbk', 'gb2312', 'gb18030']
                norm_content = None
                
                try:
                    norm_content = str(content).strip()
                except:
                    for encoding in encodings:
                        try:
                            if hasattr(content, 'decode'):
                                norm_content = content.decode(encoding).strip()
                                break
                        except:
                            continue
                
                if norm_content is None:
                    return False
                            
        except (AttributeError, TypeError, UnicodeDecodeError) as e:
            return False
        
        if not content_type_detected and len(norm_content) > 10:
            sample = norm_content[:1000]
            unprintable_count = sum(1 for c in sample if not (32 <= ord(c) <= 126))
            unprintable_ratio = float(unprintable_count) / len(sample)
            
            if unprintable_ratio > 0.3:
                return False
        
        if not norm_content:
            return False
        
        # 基于特征的快速预检测
        if (norm_content.startswith("{") and norm_content.endswith("}")) or (norm_content.startswith("[") and norm_content.endswith("]")):
            if (":" in norm_content) or ("," in norm_content):
                return True
                
        if norm_content.startswith("<?xml") or (norm_content.startswith("<") and "<xml" in norm_content[:100]):
            return True
            
        if "<html" in norm_content.lower()[:1000] or "<body" in norm_content.lower()[:1000]:
            with logged_urls_lock:
                if current_url not in logged_html_urls:
                    logged_html_urls.add(current_url)
                    if len(logged_html_urls) > 1000:
                        logged_html_urls.clear()
            return False
        
        if not content_type_detected:
            if "{" in norm_content and "}" in norm_content and (":" in norm_content or "," in norm_content):
                try:
                    open_chars = {'{': 0, '[': 0}
                    close_chars = {'}': '{', ']': '['}
                    stack = []
                    
                    for char in norm_content:
                        if char in open_chars:
                            stack.append(char)
                        elif char in close_chars:
                            if not stack or stack[-1] != close_chars[char]:
                                break
                            stack.pop()
                    
                    json_brackets_balanced = (len(stack) == 0 and 
                                             (norm_content.count('{') > 0 or norm_content.count('[') > 0))
                    
                    if json_brackets_balanced:
                        return True
                except:
                    pass
        
        return False
            
    except Exception as e:
        return False


def escape_special_characters(self, input_string):
    return input_string.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r").replace(
        "\t", "")


def read_response(self, stream):
    reader = None
    try:
        try:
            reader = BufferedReader(InputStreamReader(stream, "UTF-8"))
            response = StringBuilder()
            
            line = reader.readLine()
            while line is not None:
                response.append(line)
                response.append("\n")
                line = reader.readLine()
            
            return response.toString()
        except Exception as e:
            for encoding in ["UTF-8-SIG", "ISO-8859-1", "GBK", "GB2312", "GB18030"]:
                try:
                    if reader is not None:
                        reader.close()
                    reader = BufferedReader(InputStreamReader(stream, encoding))
                    response = StringBuilder()
                    
                    line = reader.readLine()
                    while line is not None:
                        response.append(line)
                        response.append("\n")
                        line = reader.readLine()
                    
                    return response.toString()
                except Exception as e2:
                    continue
            
            try:
                if reader is not None:
                    reader.close()
                
                from java.io import ByteArrayOutputStream
                buffer = ByteArrayOutputStream()
                from jarray import zeros
                from java.lang import Byte
                byte_array = zeros(4096, Byte)
                
                bytes_read = stream.read(byte_array, 0, 4096)
                while bytes_read != -1:
                    buffer.write(byte_array, 0, bytes_read)
                    bytes_read = stream.read(byte_array, 0, 4096)
                
                return ""
            except Exception as e2:
                return ""
    except Exception as e:
        return ""
    finally:
        if reader is not None:
            try:
                reader.close()
            except Exception as e:
                pass


def extract_res_value(self, response_string):
    try:
        if not response_string or response_string.strip() == "":
            return ""
            
        code_block_match = CODE_BLOCK_PATTERN.search(response_string)
        if code_block_match:
            content_to_process = code_block_match.group(1).strip()
            res_in_block = RES_FIELD_PATTERN.search(content_to_process)
            if res_in_block:
                print("Complete AI Analysis: " + content_to_process)
                return res_in_block.group(1).lower()
        else:
            content_to_process = response_string
        
        patterns = [
            JSON_RES_PATTERN,
            JSON_RES_PATTERN,
            ESCAPED_JSON_RES_PATTERN,
            NESTED_RES_PATTERN,
            MARKDOWN_JSON_PATTERN,
            CHOICES_CONTENT_PATTERN,
            HUNYUAN_PATTERN,
            QIANWEN_PATTERN,
            GLM_PATTERN
        ]
        
        for pattern in patterns:
            match = pattern.search(content_to_process)
            if match:
                try:
                    json_start = content_to_process.rfind('{', 0, match.start())
                    json_end = content_to_process.find('}', match.end())
                    
                    if json_start >= 0 and json_end >= 0:
                        json_obj = content_to_process[json_start:json_end+1]
                        try:
                            parsed_json = json.loads(json_obj)
                            if 'res' in parsed_json and 'reason' in parsed_json:
                                print("Complete AI Analysis: " + json_obj)
                        except:
                            pass
                except:
                    pass
                
                return match.group(1).lower()
        
        hunyuan_match = HUNYUAN_CONTENT_PATTERN.search(content_to_process)
        if hunyuan_match:
            content = hunyuan_match.group(1)
            content = content.replace('\\n', '\n').replace('\\\"', '\"').replace('\\\\', '\\')
            res_in_content = RES_FIELD_PATTERN.search(content)
            if res_in_content:
                print("Complete AI Analysis: " + content)
                return res_in_content.group(1).lower()
            
        loose_match = LOOSE_PATTERN.search(content_to_process)
        if loose_match:
            context_start = max(0, loose_match.start() - 50)
            context_end = min(len(content_to_process), loose_match.end() + 50)
            context = content_to_process[context_start:context_end]
            print("AI Analysis Context: " + context)
            # 由于修改了正则表达式，现在有多个捕获组，需要找到第一个非None的捕获组
            for i in range(1, len(loose_match.groups()) + 1):
                if loose_match.group(i):
                    return loose_match.group(i).lower()
            
        return ""
    except Exception as e:
        print("Error in extract_res_value: " + str(e))
        return ""


def generate_prompt(self, modelName, system_prompt, user_prompt):
    if modelName.lower().startswith("gemini"):
        return u"""
        {
            "model": "%s",
            "reasoning_effort": "none",
            "messages": [
                {
                    "role": "system",
                    "content": "%s"
                },
                {
                    "role": "user", 
                    "content": "%s"
                }
            ]
        }
            """ % (modelName, system_prompt, user_prompt)
    else:
        return u"""
        {
            "model": "%s",
            "messages": [
                {
                    "role": "system",
                    "content": "%s"
                },
                {
                    "role": "user", 
                    "content": "%s"
                }
            ]
        }
            """ % (modelName, system_prompt, user_prompt)


def call_dashscope_api(self, apiKey, modelName, oriUrl, oriBody, res1, res2):
    if apiKey is None:
        return "unknown"

    if self.replaceQueryParam.isSelected():
        res_system_prompt = """**角色描述**：**角色描述**：你是一个判断是否存在越权的分析机器人，通过对比两个 HTTP 请求响应数据包的相似性，判断是否存在越权漏洞，并根据要求给出判断结果。
            **输入介绍**：用户提供了两个响应内容：
            - **响应 A**：账号 A 使用自己的 Cookie 请求自己资源接口返回的响应。
            - **响应 B**：账号 A 使用自己的 Cookie 请求他人资源接口返回的响应。

            **分析要求**：
            1. **对比响应内容**：
               - 忽略动态字段（如时间戳、traceID、会话 ID 等每次请求可能变化的字段）。
               - 重点对比响应 A 和 B 的 **非动态字段的结构和内容差异**。

            2. **判断依据**：
               - **越权成功（true）**：
                 - 若响应 A 和 B 的非动态字段结构完全一致，且 A 中有值的字段在 B 中有值或为null(因为b可能确实没数据，不代表越权失败)，内容不同但符合同类型数据规则，皆判定为越权成功。
                 - 若响应 B 包含响应 A 中业务数据对应的字段结构，但字段内容变为与他人资源有关（如他人资源的 ID、名称等）的值 或 字段内容值为null(因为b可能确实没数据，不代表越权失败)，皆判定为越权成功。。
                 - 若响应 A 和 B 中都存在 `success` 字段且值为 `true`，结构一致且响应内容较短无公开接口信息，则可能为操作接口成功，判定越权成功。
               - **越权失败（false）**：
                 - 若响应 B 明确返回错误信息（如"权限不足"、"资源不可访问"或 HTTP 状态码 403/401 等），判定为越权失败。
                 - 若响应 A 和 B 的非动态字段结构、字段值完全一致，判定越权失败。
                 - 若响应 A 和 B 的字段结构显著不同（如字段数量、层级、命名等差异），尤其是 B 的内容与 A 的响应中的类型明显不相关，判定为越权失败。
                 - 若响应 B 包含字段跟响应 A 中的业务字段完全无关，判定为越权失败。
               - **其他情况（unknown）**：
                 - 若响应 B 包含与资源 A 无关的业务数据字段和值，无法明确判断是否越权，则返回未知（unknown）。
                 - 若响应 A 和 B 的差异难以判断是否符合越权条件，则返回未知（unknown）。

            3. **输出格式**：
               - 返回 JSON 格式的结果：`res` 字段值为字符串格式，只能是 `'true'`、`'false'` 或 `'unknown'`。
               - 示例：`{"res":"true", "reason":"不超过50字的判断原因"}`。
               - `reason` 字段说明判断原因，不能超过 50 字。

            **注意事项**：
            1. 仅输出 JSON 格式的结果，不添加任何额外文本或解释。
            2. 确保 JSON 格式正确，以便于后续处理。
            3. 保持客观中立，仅根据提供的响应内容进行分析。

            **总体流程**：
            1. 接收并理解响应 A 和 B。
            2. 忽略动态字段，重点对比非动态字段的结构和内容差异。
            3. 逐步进行分析，严格按照前面的判断依据得出结论并输出指定 JSON 格式的结果。"""
        res_user_prompt = "Response A: %s, Response B: %s" % (res1, res2)
        request_body = generate_prompt(self, modelName, escape_special_characters(self, res_system_prompt),
                                       escape_special_characters(self, res_user_prompt))
        AI_res = request_dashscope_api(self, apiKey, modelName, oriUrl, request_body)
        return AI_res
    else:
        res_system_prompt = """**角色描述**：你是一个判断是否存在越权的分析机器人，通过对比两个 HTTP 请求响应数据包的相似性，判断是否存在越权漏洞，并根据要求给出判断结果。
            **输入介绍**：用户提供了两个响应内容:
            - **响应 A**：账号 A 的身份请求接口返回的响应。
            - **响应 B**：将账号 A 的 Cookie 替换为账号 B 的 Cookie 后重新请求获得的响应。

            **分析要求**：
            1. **对比响应内容**:
               - 重要！忽略动态字段（如时间戳、traceID、requestID 等每次请求可能变化的字段）,动态字段通常包括时间戳、会话 ID、trace ID、requestID 等字段。
               - 只对比响应 A 和 B 的非动态字段结构和内容，判断相似性。

            2. **判断依据**：
               - **越权成功（true）**：
                 - 若响应 B 的结构和内容与响应 A 完全一致(所有非动态字段)，判定为越权成功。
                 - 若响应 B 中包含响应 A 中的资源数据或账号数据，且非动态字段与 A 的内容高度一致，也判定为越权成功。
                 - 若响应 A 和 B 中都存在 `success` 字段且值为 `true`，结构一致且响应内容较短无公开信息，也判定越权成功。
               - **越权失败（false）**：
                 - 若响应 B 与响应 A 的结构和内容明显不同，尤其是结构不一致，判定为越权失败。
                 - 若响应 B 包含"权限不足"或"需要登录"等错误信息，判定为越权失败。
                 - 若响应 A 和 B 的结构一致，但账号特征字段（如用户名、邮箱、userid 等）中的值显示为账号 B 的信息而非账号 A 的信息，判定为越权失败。
               - **其他情况（unknown）**：
                 - 若响应 B 包含与账号 A 无关的业务数据或敏感数据，但无法明确判断是否越权，则返回未知（unknown）。
                 - 若响应 A 和 B 的差异难以判断为越权成功或失败，则返回未知（unknown）。

            3. **输出格式**：
               - 返回 JSON 格式的结果：`res` 字段值为字符串格式，只能是 `'true'`、`'false'` 或 `'unknown'`。
               - 示例：`{"res":"true", "reason":"不超过50字的判断原因"}`。
               - `reason` 字段说明判断原因，不能超过 50 字。

            **注意事项**：
            1. 仅输出 JSON 格式的结果，不添加任何额外文本或解释。
            2. 确保 JSON 格式正确，以便于后续处理。
            3. 保持客观中立，仅根据提供的响应内容进行分析。

            **总体流程**：
            1. 接收并理解响应 A 和 B。
            2. 忽略动态字段，重点对比非动态字段的结构和内容差异。
            3. 逐步的进行分析，得出结论输出指定 JSON 格式的结果。"""
        res1 = escape_special_characters(self, res1)
        res2 = escape_special_characters(self, res2)
        res_user_prompt = "Response A: %s, Response B: %s" % (res1, res2)
        request_body = generate_prompt(self, modelName, escape_special_characters(self, res_system_prompt),
                                       escape_special_characters(self, res_user_prompt))
        AI_res = request_dashscope_api(self, apiKey, modelName, oriUrl, request_body)
        return AI_res


def request_dashscope_api(self, api_key, modelName, orgUrl, request_body):
    max_retries = 3
    retry_count = 0
    retry_delay = 2  # 基础延迟（秒）
    jitter_factor = 0.25  # 抖动因子（最大抖动为基础延迟的25%）
    
    # 创建线程局部变量保存URL，避免多线程干扰
    thread_local_url = str(orgUrl)  # 确保转换为字符串
    
    api_endpoints = {
        "deepseek": "https://api.deepseek.com/v1/chat/completions",
        "gpt": "https://api.openai.com/v1/chat/completions",
        "glm": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "hunyuan": "https://api.hunyuan.cloud.tencent.com/v1/chat/completions",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "default": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    }
    
    api_url = api_endpoints["default"]
    for prefix, endpoint in api_endpoints.items():
        if modelName.lower().startswith(prefix):
            api_url = endpoint
            break
    
    while retry_count < max_retries:
        connection = None
        outputStream = None
        writer = None
        inputStream = None
        errorStream = None
        
        try:
            if retry_count > 0:
                from java.util import Random
                rand = Random()
                base_delay = retry_delay * (2 ** (retry_count - 1))
                jitter = rand.nextFloat() * base_delay * jitter_factor * 2 - base_delay * jitter_factor
                actual_delay = base_delay + jitter
                
                time.sleep(actual_delay)
                
            url = URL(api_url)
            
            # 创建连接并配置
            connection = url.openConnection()
            connection.setRequestMethod("POST")
            connection.setDoOutput(True)
            connection.setConnectTimeout(30000)  # 30秒连接超时
            connection.setReadTimeout(60000)     # 60秒读取超时

            # 配置SSL
            if hasattr(connection, 'setSSLSocketFactory'):
                connection.setSSLSocketFactory(SSLSocketFactory.getDefault())
                connection.setHostnameVerifier(lambda hostname, session: True)

            # 设置通用请求头
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            connection.setRequestProperty("Authorization", "Bearer " + api_key)
            
            outputStream = connection.getOutputStream()
            writer = OutputStreamWriter(outputStream, "UTF-8")
            writer.write(request_body)
            writer.flush()

            responseCode = connection.getResponseCode()

            if responseCode == HttpURLConnection.HTTP_OK or responseCode == HttpURLConnection.HTTP_CREATED:
                inputStream = connection.getInputStream()
                AI_res = read_response(self, inputStream)
                res_value = extract_res_value(self, AI_res)
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                json_log = '{\n' \
                           '\t"timestamp": "%s",\n ' \
                           '\t"orig_url": "%s",\n ' \
                           '\t"ai_api_status": "%s",\n ' \
                           '\t"ai_analysis_result": "%s",\n ' \
                           '\t"ai_original_response": "%s"\n ' \
                           '}\n' % (
                               timestamp,
                               str(orgUrl),
                               str(responseCode),
                               str(res_value),
                               str(AI_res) if str(AI_res) else 'N/A'
                           )

                print(json_log)
                
                if res_value:
                    return res_value
                return ""
            else:
                errorStream = connection.getErrorStream()
                if errorStream is not None:
                    error_response = read_response(self, errorStream)

                    error_response = fix_chinese_encoding(error_response)
                    
                    retriable_errors = {
                        'rate_limit': ['rate limit', 'ratelimit', 'too many requests', 
                                      'too_many_requests', '429', 'throttl', 
                                      'frequency', '频率', '次数超限', '请求过于频繁', 
                                      '稍后重试', '请求频率', '频率超限', 'qps'],
                        'timeout': ['timeout', '超时', 'timed out'],
                        'server_error': ['500', '502', '503', '504', 'server error', 
                                       'unavailable', 'maintenance', '服务不可用']
                    }
                    
                    error_type = None
                    error_response_lower = error_response.lower()
                    
                    for error_category, indicators in retriable_errors.items():
                        if any(indicator in error_response_lower for indicator in indicators):
                            error_type = error_category
                            break
                            
                    if not error_type and (429 <= responseCode < 500 or 500 <= responseCode < 600):
                        if 429 == responseCode:
                            error_type = 'rate_limit'
                        elif responseCode >= 500:
                            error_type = 'server_error'
                    
                    if error_type:
                        retry_count += 1
                        if retry_count < max_retries:
                            base_delay = retry_delay * (2 ** (retry_count - 1))
                            if error_type == 'rate_limit':
                                base_delay *= 2
                                
                            from java.util import Random
                            rand = Random()
                            jitter = rand.nextFloat() * base_delay * jitter_factor * 2 - base_delay * jitter_factor
                            wait_time = base_delay + jitter
                            
                            time.sleep(wait_time)
                            continue
                    
                    return ""
                else:
                    return ""
                
        except SSLHandshakeException as e:
            retry_count += 1
            if retry_count == max_retries:
                return ""
            continue
            
        except EOFException as e:
            retry_count += 1
            if retry_count == max_retries:
                return ""
            continue
            
        except SocketException as e:
            retry_count += 1
            if retry_count == max_retries:
                return ""
            continue
            
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                return ""
            continue
        finally:
            # 确保所有资源都被正确关闭
            resources = [writer, outputStream, inputStream, errorStream]
            for resource in resources:
                if resource is not None:
                    try:
                        resource.close()
                    except Exception as e:
                        pass
            
    return ""


def fix_chinese_encoding(text):
    """修复中文编码问题"""
    if not text:
        return text
        
    try:
        # 缓存原始文本以便比较
        original_text = text
        
        # 1. 检测和修复Unicode转义序列 (如 \u4e2d\u6587)
        if '\\u' in text:
            # 尝试使用JSON解析修复Unicode转义
            try:
                # 检查是否是有效的JSON格式
                if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
                    parsed = json.loads(text)
                    fixed = json.dumps(parsed, ensure_ascii=False)
                    if fixed != text:
                        return fixed
                
                # 如果不是完整JSON，尝试将文本包装在JSON结构中再解析
                wrapped = '"%s"' % text.replace('"', '\\"')
                try:
                    parsed = json.loads(wrapped)
                    if isinstance(parsed, basestring) and parsed != text:
                        return parsed
                except:
                    pass
            except:
                pass
                
            # 尝试直接解码Unicode转义序列
            try:
                decoded = text.decode('unicode_escape')
                # 验证结果是否包含有效的中文字符
                if any(0x4e00 <= ord(c) <= 0x9fff for c in decoded):
                    return decoded
            except:
                try:
                    # 尝试另一种转义序列解码方法
                    decoded = text.decode('string_escape').decode('utf-8')
                    if decoded != text:
                        return decoded
                except:
                    pass
        
        # 2. 检测和修复UTF-8编码被误解为Latin-1的情况
        # 检查是否有可能是被错误编码的UTF-8字节
        has_suspect_bytes = False
        for c in text:
            code = ord(c)
            # 检查是否包含可能被错误解码的UTF-8标记
            if 0x80 <= code <= 0xFF:
                has_suspect_bytes = True
                break
                
        if has_suspect_bytes:
            # 常见的中文相关编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
            
            for source_encoding in ['latin-1', 'cp1252']:
                try:
                    # 先将文本编码为源编码的字节流
                    bytes_data = text.encode(source_encoding)
                    
                    # 然后尝试以不同的编码解码
                    for target_encoding in encodings:
                        try:
                            decoded = bytes_data.decode(target_encoding)
                            # 验证结果是否包含中文字符
                            if any(0x4e00 <= ord(c) <= 0x9fff for c in decoded):
                                return decoded
                        except:
                            continue
                except:
                    continue
                    
        # 3. 尝试处理JSON中的中文
        if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
            try:
                # 尝试解析和重新序列化，以处理JSON内部的编码问题
                parsed = json.loads(text)
                fixed = json.dumps(parsed, ensure_ascii=False)
                if fixed != original_text:
                    return fixed
            except:
                pass
                
        # 4. 检测混合编码问题（部分UTF-8，部分GBK等）
        if len(text) > 10 and has_suspect_bytes:
            # 尝试分段处理，可能存在不同编码混合的情况
            sections = []
            current = ""
            
            for c in text:
                code = ord(c)
                if 0x80 <= code <= 0xFF:
                    # 遇到可能的多字节字符
                    if current:
                        sections.append(current)
                        current = ""
                    sections.append(c)
                else:
                    current += c
                    
            if current:
                sections.append(current)
                
            # 尝试对每个部分单独处理
            fixed_sections = []
            changed = False
            
            for section in sections:
                if len(section) == 1 and 0x80 <= ord(section[0]) <= 0xFF:
                    # 尝试修复单个可能错误编码的字符
                    for encoding in encodings:
                        try:
                            fixed = section.encode('latin-1').decode(encoding)
                            if fixed != section:
                                fixed_sections.append(fixed)
                                changed = True
                                break
                        except:
                            continue
                    else:
                        fixed_sections.append(section)
                else:
                    fixed_sections.append(section)
                    
            if changed:
                return ''.join(fixed_sections)
                
    except Exception as e:
        pass
        
    return text


def checkAuthorization(self, messageInfo, originalHeaders, checkUnauthorized):
    oriUrl, reqMethod, oriBody = getRequestBody(self, messageInfo)

    if checkUnauthorized:
        messageUnauthorized, _ = makeMessage(self, messageInfo, True, False)
        requestResponseUnauthorized = makeRequest(self, messageInfo, messageUnauthorized)
        unauthorizedResponse = requestResponseUnauthorized.getResponse()
        analyzedResponseUnauthorized = self._helpers.analyzeResponse(unauthorizedResponse)
        statusCodeUnauthorized = analyzedResponseUnauthorized.getHeaders()[0]
        contentUnauthorized = getResponseBody(self, requestResponseUnauthorized)

    message, modifyFlag = makeMessage(self, messageInfo, True, True)
    requestResponse = makeRequest(self, messageInfo, message)
    newResponse = requestResponse.getResponse()
    analyzedResponse = self._helpers.analyzeResponse(newResponse)

    oldStatusCode = originalHeaders[0]
    newStatusCode = analyzedResponse.getHeaders()[0]
    oldContent = getResponseBody(self, messageInfo)
    newContent = getResponseBody(self, requestResponse)

    EDFilters = self.EDModel.toArray()

    if pre_check(self, oldStatusCode, newStatusCode, oldContent, newContent, modifyFlag, oriUrl, "modified"):
        impression, AI_res = checkBypass(self, oriUrl, oriBody, oldStatusCode, newStatusCode, oldContent, newContent,
                                         EDFilters, requestResponse,
                                         self.AndOrType.getSelectedItem(), True)
    else:
        impression, AI_res = self.ENFORCED_STR, ""

    if checkUnauthorized:
        if pre_check(self, oldStatusCode, statusCodeUnauthorized, oldContent, contentUnauthorized, modifyFlag=True, oriUrl=oriUrl, request_type="unauthorized"):
            EDFiltersUnauth = self.EDModelUnauth.toArray()
            impressionUnauthorized, _ = checkBypass(self, oriUrl, oriBody, oldStatusCode, statusCodeUnauthorized,
                                                    oldContent, contentUnauthorized,
                                                    EDFiltersUnauth, requestResponseUnauthorized,
                                                    self.AndOrTypeUnauth.getSelectedItem(), False)
        else:
            impressionUnauthorized = self.ENFORCED_STR

    self._lock.acquire()
    try:
        row = self._log.size()
        method = self._helpers.analyzeRequest(messageInfo.getRequest()).getMethod()

        if checkUnauthorized:
            self._log.add(
                LogEntry(self.currentRequestNumber, self._callbacks.saveBuffersToTempFiles(requestResponse), method,
                         self._helpers.analyzeRequest(requestResponse).getUrl(), messageInfo, impression,
                         self._callbacks.saveBuffersToTempFiles(requestResponseUnauthorized), impressionUnauthorized,
                         AI_res))

        else:
            self._log.add(
                LogEntry(self.currentRequestNumber, self._callbacks.saveBuffersToTempFiles(requestResponse), method,
                         self._helpers.analyzeRequest(requestResponse).getUrl(), messageInfo, impression, None, "Disabled",
                         AI_res))

        SwingUtilities.invokeLater(UpdateTableEDT(self, "insert", row, row))
        self.currentRequestNumber += 1
    finally:
        self._lock.release()


def checkAuthorizationV2(self, messageInfo):
    checkAuthorization(self, messageInfo,
                       self._extender._helpers.analyzeResponse(messageInfo.getResponse()).getHeaders(),
                       self._extender.doUnauthorizedRequest.isSelected())


def retestAllRequests(self):
    self.logTable.setAutoCreateRowSorter(True)
    for i in range(self.tableModel.getRowCount()):
        logEntry = self._log.get(self.logTable.convertRowIndexToModel(i))
        handle_message(self, "AUTORIZEPRO", False, logEntry._originalrequestResponse)
