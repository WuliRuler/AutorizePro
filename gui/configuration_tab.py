#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File   : configuration_tab.py
@Author : sule01u
@Date   : 2024/10/10
@Desc   : 配置选项卡
"""

from javax.swing import DefaultComboBoxModel
from java.awt.event import ActionListener
from javax.swing import SwingUtilities
from javax.swing import JToggleButton
from javax.swing import JScrollPane
from javax.swing import JTabbedPane
from javax.swing import JOptionPane
from javax.swing import GroupLayout
from javax.swing import JSplitPane
from javax.swing import JComboBox
from javax.swing import JTextArea
from javax.swing import JCheckBox
from javax.swing import JButton
from javax.swing import JPanel
from javax.swing import JLabel
from javax.swing import JTextField
from javax.swing import ComboBoxEditor
from javax.swing import JPopupMenu, JMenuItem
from java.awt import Dimension
from javax.swing.event import DocumentListener
from java.awt.event import FocusListener

from table import UpdateTableEDT
from localization.language_manager import get_text, get_language_manager
from localization.ui_updater import update_main_ui, update_table_headers


class ConfigurationTab():
    def __init__(self, extender):
        self._extender = extender
        self.draw()
        # 移除实时验证监听器
        # self._extender.aiModelTextField.getDocument().addDocumentListener(DocumentListener(self._extender))

    def draw(self):
        """  init configuration tab
        """
        self.DEFUALT_REPLACE_TEXT = "Cookie: Insert=injected; cookie=or;\nHeader: here"
        self._extender.startButton = JToggleButton(get_text("autorize_is_off", "AutorizePro is off"), actionPerformed=self.startOrStop)
        self._extender.startButton.setBounds(10, 20, 230, 30)
        
        toggle_text = get_text("language_toggle", "EN/中")
        try:
            from java.lang import String
            toggle_text = String(toggle_text) if isinstance(toggle_text, unicode) else String(toggle_text.decode('utf-8'))
        except:
            pass
        self._extender.toggleLanguageButton = JButton(toggle_text, actionPerformed=self.toggleLanguage)
        self._extender.toggleLanguageButton.setBounds(245, 20, 60, 30)

        # 添加API Key标签和输入框
        apiKeyYPos = 100
        self._extender.apiKeyLabel = JLabel("KEY:")
        self._extender.apiKeyLabel.setBounds(10, apiKeyYPos, 40, 30)
        self._extender.apiKeyField = JTextField(15)
        self._extender.apiKeyField.setBounds(70, apiKeyYPos, 150, 30)
        # 改用文本框 + 下拉按钮组合来支持用户输入模型
        yPos = 140
        height = 25
        
        self._extender.aiModelTextField = JTextField("qwen-turbo", 7)
        self._extender.aiModelTextField.setBounds(50, yPos, 95, height)
        
        self._extender.modelSelectButton = JButton("+", actionPerformed=self.showModelOptions)
        self._extender.modelSelectButton.setBounds(145, yPos, 25, height)
        
        # 添加自定义API URL输入框和标签
        apiUrlYPos = yPos + 35
        self._extender.aiApiUrlLabel = JLabel(get_text("ai_api_url_label", "URL:"))
        self._extender.aiApiUrlLabel.setBounds(10, apiUrlYPos, 40, height)
        # 使用与API Key输入框相同的宽度（150），保持一致性
        placeholder_text = get_text("ai_api_url_placeholder", "http://localhost:11434/v1/chat/completions")
        self._extender.aiApiUrlField = JTextField(placeholder_text, 15)
        self._extender.aiApiUrlField.setBounds(50, apiUrlYPos, 150, height)
        
        # 添加"启用 AI"按钮在URL输入框右侧（与URL输入框同一行）
        self._extender.apiKeyEnabledCheckbox = JToggleButton(get_text("enable_ai", "启用 AI"), actionPerformed=self.validateModelOnKeyToggle)
        # 注意：GroupLayout会管理位置，setBounds仅作为初始位置参考
        self._extender.apiKeyEnabledCheckbox.setBounds(210, apiUrlYPos, 80, height)
        # 设置占位符文本颜色为灰色（通过设置前景色，当用户输入时会被覆盖）
        from java.awt import Color
        self._extender.aiApiUrlField.setForeground(Color.GRAY)
        # 添加焦点监听器，实现占位符效果
        self._extender.aiApiUrlField.addFocusListener(ApiUrlPlaceholderListener(self._extender, placeholder_text))
        self._extender.aiApiUrlField.setToolTipText(get_text("ai_api_url_tooltip", "Leave empty to use default API endpoint. Set custom URL for private model deployment (e.g., http://localhost:11434/v1/chat/completions for Ollama)."))
        
        self._predefinedOptions = ["qwen-turbo", "qwen-plus", "qwen-max",
                                   "deepseek-chat","deepseek-reasoner",
                                   "gpt-4o-mini", "gpt-4o",
                                   "glm-4-flash", "glm-4-air",
                                   "hunyuan-lite", "hunyuan-standard",
                                   "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
        
        # 支持的模型厂商列表
        self._supportedVendors = ["qwen", "deepseek", "gpt", "glm", "hunyuan", "gemini"]
        
        self._modelPopupMenu = JPopupMenu()

        self._extender.clearButton = JButton(get_text("clear_button", "Clear List"), actionPerformed=self.clearList)
        self._extender.clearButton.setBounds(10, 80, 100, 30)
        self._extender.autoScroll = JCheckBox(get_text("auto_scroll", "Auto Scroll"))
        self._extender.autoScroll.setBounds(145, 80, 130, 30)

        self._extender.ignore304 = JCheckBox(get_text("ignore_304", "Ignore 304/204 status code responses"))
        self._extender.ignore304.setBounds(280, 5, 300, 30)
        self._extender.ignore304.setSelected(True)

        self._extender.prevent304 = JCheckBox(get_text("prevent_304", "Prevent 304 Not Modified status code"))
        self._extender.prevent304.setBounds(280, 25, 300, 30)
        self._extender.interceptRequestsfromRepeater = JCheckBox(get_text("intercept_from_repeater", "Intercept requests from Repeater"))
        self._extender.interceptRequestsfromRepeater.setBounds(280, 45, 300, 30)

        self._extender.doUnauthorizedRequest = JCheckBox(get_text("check_unauthenticated", "Check unauthenticated"))
        self._extender.doUnauthorizedRequest.setBounds(280, 65, 300, 30)
        self._extender.doUnauthorizedRequest.setSelected(True)

        self._extender.replaceQueryParam = JCheckBox(get_text("replace_query_params", "Replace query params"), actionPerformed=self.replaceQueryHanlder)
        self._extender.replaceQueryParam.setBounds(280, 85, 300, 30)
        self._extender.replaceQueryParam.setSelected(False)

        savedHeadersTitles = self.getSavedHeadersTitles()
        self._extender.savedHeadersTitlesCombo = JComboBox(savedHeadersTitles)
        self._extender.savedHeadersTitlesCombo.addActionListener(SavedHeaderChange(self._extender))
        self._extender.savedHeadersTitlesCombo.setBounds(10, 115, 100, 30)

        self._extender.saveHeadersButton = JButton("Add", actionPerformed=self.saveHeaders)
        self._extender.saveHeadersButton.setBounds(100, 115, 80, 30)

        self._extender.removeHeadersButton = JButton("Remove", actionPerformed=self.removeHeaders)
        self._extender.removeHeadersButton.setBounds(200, 115, 80, 30)

        self._extender.replaceString = JTextArea(self.DEFUALT_REPLACE_TEXT, 5, 30)
        self._extender.replaceString.setWrapStyleWord(True)
        self._extender.replaceString.setLineWrap(True)

        scrollReplaceString = JScrollPane(self._extender.replaceString)
        scrollReplaceString.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED)
        scrollReplaceString.setBounds(10, 150, 470, 150)

        fromLastRequestLabel = JLabel(get_text("from_last_request", "From last request:"))
        fromLastRequestLabel.setBounds(10, 305, 250, 30)

        self._extender.fetchCookiesHeaderButton = JButton(get_text("fetch_cookie_button", "Fetch Cookies header"),
                                                          actionPerformed=self.fetchCookiesHeader)
        self._extender.fetchCookiesHeaderButton.setEnabled(False)
        self._extender.fetchCookiesHeaderButton.setBounds(10, 330, 220, 30)

        self._extender.fetchAuthorizationHeaderButton = JButton(get_text("fetch_authorization_button", "Fetch Authorization header"),
                                                                actionPerformed=self.fetchAuthorizationHeader)
        self._extender.fetchAuthorizationHeaderButton.setEnabled(False)
        self._extender.fetchAuthorizationHeaderButton.setBounds(260, 330, 220, 30)
        
        verticalSpacerPanel = JPanel()
        verticalSpacerPanel.setPreferredSize(Dimension(1, 20))

        # 认证头配置区域 - 位于fetchCookiesHeaderButton下方
        self._extender.authHeadersLabel = JLabel(get_text("auth_headers_label", "Authentication Headers:"))
        self._extender.authHeadersLabel.setBounds(10, 370, 300, 30)
        
        default_auth_headers = "cookie,authorization,token"
        self._extender.custom_auth_headers = default_auth_headers.split(",")
        
        self._extender.authHeadersField = JTextField(default_auth_headers)
        self._extender.authHeadersField.setBounds(10, 400, 200, 30)
        self._extender.authHeadersField.setToolTipText(get_text("auth_headers_tooltip", "Comma-separated list of authentication header names"))
        
        self._extender.updateAuthHeadersButton = JButton(get_text("update_auth_headers", "Update"), actionPerformed=self.updateAuthHeaders)
        self._extender.updateAuthHeadersButton.setBounds(400, 400, 90, 30)

        self._extender.filtersTabs = JTabbedPane()
        self._extender.filtersTabs = self._extender.filtersTabs
        self._extender.filtersTabs.addTab("Privilege Enforcement Rules", self._extender.EDPnl)
        self._extender.filtersTabs.addTab("Unauthorized Enforcement Rules", self._extender.EDPnlUnauth)
        self._extender.filtersTabs.addTab("Interception Filters", self._extender.filtersPnl)
        self._extender.filtersTabs.addTab("Match/Replace", self._extender.MRPnl)
        self._extender.filtersTabs.addTab("Table Filter", self._extender.filterPnl)
        self._extender.filtersTabs.addTab("Save/Restore", self._extender.exportPnl)

        self._extender.filtersTabs.setSelectedIndex(2)
        self._extender.filtersTabs.setBounds(0, 350, 2000, 700)

        self.config_pnl = JPanel()
        layout = GroupLayout(self.config_pnl)
        self.config_pnl.setLayout(layout)
        layout.setAutoCreateGaps(True)
        layout.setAutoCreateContainerGaps(True)

        layout.setHorizontalGroup(
            layout.createSequentialGroup()
            .addGroup(
                layout.createParallelGroup()
                .addGroup(
                    layout.createSequentialGroup()
                    .addComponent(
                        self._extender.startButton,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    .addComponent(
                        self._extender.toggleLanguageButton,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                )
                .addGroup(
                    layout.createSequentialGroup()
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.CENTER)
                    .addComponent(
                        self._extender.apiKeyLabel,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    )
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.CENTER)
                    .addComponent(
                        self._extender.apiKeyField,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    )
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.CENTER)
                    .addGroup(layout.createSequentialGroup()
                    .addComponent(
                        self._extender.aiModelTextField,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    .addComponent(
                        self._extender.modelSelectButton,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    )
                    )
                )
                .addGroup(
                    layout.createSequentialGroup()
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.CENTER)
                    .addComponent(
                        self._extender.aiApiUrlLabel,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    )
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.CENTER)
                    .addComponent(
                        self._extender.aiApiUrlField,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    )
                    .addGap(15)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.CENTER)
                    .addComponent(
                        self._extender.apiKeyEnabledCheckbox,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    )
                )
                .addComponent(
                    self._extender.clearButton,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addGroup(layout.createSequentialGroup()
                .addComponent(
                    self._extender.savedHeadersTitlesCombo,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.saveHeadersButton,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.removeHeadersButton,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                ))
                .addComponent(
                    scrollReplaceString,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    fromLastRequestLabel,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addGroup(layout.createSequentialGroup()
                .addComponent(
                    self._extender.fetchCookiesHeaderButton,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.fetchAuthorizationHeaderButton,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                )
                .addComponent(
                    verticalSpacerPanel,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.authHeadersLabel,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addGroup(layout.createSequentialGroup()
                .addComponent(
                    self._extender.authHeadersField,
                    GroupLayout.PREFERRED_SIZE,
                    380,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.updateAuthHeadersButton,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                )
            )
            .addGroup(
                layout.createParallelGroup()
                .addComponent(
                    self._extender.ignore304,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.prevent304,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.interceptRequestsfromRepeater,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.doUnauthorizedRequest,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.autoScroll,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
                .addComponent(
                    self._extender.replaceQueryParam,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
            )
        )

        layout.setVerticalGroup(
            layout.createSequentialGroup()
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
            .addComponent(
                self._extender.startButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.toggleLanguageButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.ignore304,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            )
            .addComponent(
                self._extender.prevent304,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.CENTER)
            .addComponent(
                self._extender.apiKeyLabel,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.apiKeyField,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
            .addComponent(
                self._extender.aiModelTextField,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.modelSelectButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            )
            .addComponent(
                self._extender.interceptRequestsfromRepeater,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            )
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.CENTER)
            .addComponent(
                self._extender.aiApiUrlLabel,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.aiApiUrlField,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.apiKeyEnabledCheckbox,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            )
            .addComponent(
                self._extender.doUnauthorizedRequest,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.replaceQueryParam,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
            .addComponent(
                self._extender.clearButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.autoScroll,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            )
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
            .addComponent(
                self._extender.savedHeadersTitlesCombo,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.saveHeadersButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.removeHeadersButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            )
            .addComponent(
                scrollReplaceString,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                fromLastRequestLabel,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
            .addComponent(
                self._extender.fetchCookiesHeaderButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.fetchAuthorizationHeaderButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            ))
            .addComponent(
                verticalSpacerPanel,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addComponent(
                self._extender.authHeadersLabel,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            )
            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                            .addComponent(
                    self._extender.authHeadersField,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                    GroupLayout.PREFERRED_SIZE,
                )
            .addComponent(
                self._extender.updateAuthHeadersButton,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
                GroupLayout.PREFERRED_SIZE,
            ))
        )

        self.config_pnl.setMinimumSize(Dimension(0, 0))
        self.config_pnl.setPreferredSize(Dimension(400, 200))

        self._extender.filtersTabs.setMinimumSize(Dimension(0, 0))
        self._extender.filtersTabs.setPreferredSize(Dimension(400, 400))

        self._extender._cfg_splitpane = JSplitPane(JSplitPane.VERTICAL_SPLIT)
        self._extender._cfg_splitpane.setResizeWeight(0.5)
        self._extender._cfg_splitpane.setContinuousLayout(True)
        self._extender._cfg_splitpane.setLeftComponent(self.config_pnl)
        self._extender._cfg_splitpane.setRightComponent(self._extender.filtersTabs)

    def startOrStop(self, event):
        """
        start/stop autorize
        """
        if self._extender.startButton.isSelected():
            self._extender.intercept = 1
            self._extender.startButton.setText(get_text("autorize_is_on", "AutorizePro is on"))
            self._extender.fetchCookiesHeaderButton.setEnabled(True)
            self._extender.fetchAuthorizationHeaderButton.setEnabled(True)
        else:
            self._extender.intercept = 0
            self._extender.startButton.setText(get_text("autorize_is_off", "AutorizePro is off"))
            self._extender.fetchCookiesHeaderButton.setEnabled(False)
            self._extender.fetchAuthorizationHeaderButton.setEnabled(False)

    def clearList(self, event):
        self._extender._lock.acquire()
        try:
            oldSize = self._extender._log.size()
            self._extender._log.clear()
            SwingUtilities.invokeLater(UpdateTableEDT(self._extender, "delete", 0, oldSize - 1))
        finally:
            self._extender._lock.release()

    def replaceQueryHanlder(self, event):
        if self._extender.replaceQueryParam.isSelected():
            self._extender.replaceString.setText("paramName=paramValue\npath:oldPath=newPath")
        else:
            self._extender.replaceString.setText(self.DEFUALT_REPLACE_TEXT)

    def saveHeaders(self, event):
        savedHeadersTitle = JOptionPane.showInputDialog("Please provide saved headers title:")
        self._extender.savedHeaders.append(
            {'title': savedHeadersTitle, 'headers': self._extender.replaceString.getText()})
        self._extender.savedHeadersTitlesCombo.setModel(DefaultComboBoxModel(self.getSavedHeadersTitles()))
        self._extender.savedHeadersTitlesCombo.getModel().setSelectedItem(savedHeadersTitle)

    def removeHeaders(self, event):
        model = self._extender.savedHeadersTitlesCombo.getModel()
        selectedItem = model.getSelectedItem()
        if selectedItem == "Temporary headers":
            return

        delObject = None
        for savedHeaderObj in self._extender.savedHeaders:
            if selectedItem == savedHeaderObj['title']:
                delObject = savedHeaderObj
        self._extender.savedHeaders.remove(delObject)
        model.removeElement(selectedItem)

    def getSavedHeadersTitles(self):
        titles = []
        for savedHeaderObj in self._extender.savedHeaders:
            titles.append(savedHeaderObj['title'])
        return titles

    def fetchCookiesHeader(self, event):
        if self._extender.lastCookiesHeader:
            self._extender.replaceString.setText(self._extender.lastCookiesHeader)

    def fetchAuthorizationHeader(self, event):
        if self._extender.lastAuthorizationHeader:
            self._extender.replaceString.setText(self._extender.lastAuthorizationHeader)

    def toggleLanguage(self, event):
        """实现语言切换功能，在中文和英文之间切换"""
        from localization.ui_updater import update_main_ui, update_table_headers
        
        manager = get_language_manager()
        
        # 切换语言：如果当前是英文则切换到中文，如果是中文则切换到英文
        current_language = manager.current_language
        new_language = "zh" if current_language == "en" else "en"
        
        if manager.set_language(new_language):
            # 更新按钮文本 - 特殊处理确保中文字符正确显示
            toggle_text = get_text("language_toggle", "EN/中")
            try:
                from java.lang import String
                toggle_text = String(toggle_text) if isinstance(toggle_text, unicode) else String(toggle_text.decode('utf-8'))
            except:
                pass
            self._extender.toggleLanguageButton.setText(toggle_text)
            
            try:
                from java.lang import System
                System.setProperty("file.encoding", "UTF-8")
                
                # 设置Jython默认编码为UTF-8
                import sys
                if hasattr(sys, "setdefaultencoding"):
                    reload(sys)
                    sys.setdefaultencoding('utf-8')
            except:
                pass
            
            message = get_text("language_changed", "语言已成功更改")
            title = get_text("extension_name", "AutorizePro")

            try:
                from java.lang import String
                if isinstance(message, unicode):
                    message = String(message)
                else:
                    message = String(message.decode('utf-8'))
                
                if isinstance(title, unicode):
                    title = String(title)
                else:
                    title = String(title.decode('utf-8'))
            except Exception as e:
                pass

            try:
                update_main_ui(self._extender)
            except Exception as e:
                pass
            
            try:
                update_table_headers(self._extender)
            except Exception as e:
                pass
            

            from javax.swing import JOptionPane
            JOptionPane.showMessageDialog(None, message, title, JOptionPane.INFORMATION_MESSAGE)
            
            return True
        
        return False

    def updateAuthHeaders(self, event):
        auth_headers_text = self._extender.authHeadersField.getText()
        if auth_headers_text:
            auth_headers = [h.strip() for h in auth_headers_text.split(",") if h.strip()]
            self._extender.custom_auth_headers = auth_headers
        else:
            # 如果输入的认证头为空，恢复下面的默认值
            default_auth_headers = ["cookie", "authorization", "token"]
            self._extender.custom_auth_headers = default_auth_headers
            self._extender.authHeadersField.setText("cookie,authorization,token")
        
        JOptionPane.showMessageDialog(
            None,
            get_text("auth_headers_updated", "Authentication headers updated successfully"),
            "Update Headers",
            JOptionPane.INFORMATION_MESSAGE
        )
        
    def validateModelOnKeyToggle(self, event):
        """在用户勾选 KEY 复选框时验证模型是否符合我们的限制"""
        if self._extender.apiKeyEnabledCheckbox.isSelected():
            model_name = self._extender.aiModelTextField.getText().strip()
            if not model_name:
                message = get_text("model_empty", "Model name cannot be empty")
                title = get_text("warning", "Warning")
                
                try:
                    from java.lang import String
                    if isinstance(message, unicode):
                        message = String(message)
                    else:
                        message = String(message.decode('utf-8'))
                    if isinstance(title, unicode):
                        title = String(title)
                    else:
                        title = String(title.decode('utf-8'))
                except:
                    pass
                    
                JOptionPane.showMessageDialog(
                    None,
                    message,
                    title,
                    JOptionPane.WARNING_MESSAGE
                )
                self._extender.apiKeyEnabledCheckbox.setSelected(False)
                return
            
            # 如果设置了自定义API URL，跳过模型验证（允许使用任何模型，如Ollama）
            custom_api_url = ""
            try:
                if hasattr(self._extender, "aiApiUrlField") and self._extender.aiApiUrlField is not None:
                    url_text = self._extender.aiApiUrlField.getText()
                    if url_text is not None:
                        custom_api_url = str(url_text).strip()
                        # 如果是占位符文本，视为空
                        placeholder = get_text("ai_api_url_placeholder", "http://localhost:11434/v1/chat/completions")
                        if custom_api_url == placeholder:
                            custom_api_url = ""
            except:
                pass
            
            # 如果设置了自定义API URL，允许使用任何模型
            if custom_api_url:
                return  # 跳过模型验证
                
            if not self.validateModel(model_name):
                message = get_text("unsupported_model", "Unsupported model vendor, please contact developer")
                title = get_text("warning", "Warning")
                
                try:
                    from java.lang import String
                    if isinstance(message, unicode):
                        message = String(message)
                    else:
                        message = String(message.decode('utf-8'))
                    if isinstance(title, unicode):
                        title = String(title)
                    else:
                        title = String(title.decode('utf-8'))
                except:
                    pass
                    
                JOptionPane.showMessageDialog(
                    None,
                    message,
                    title,
                    JOptionPane.WARNING_MESSAGE
                )
                self._extender.apiKeyEnabledCheckbox.setSelected(False)
                return

    def validateModel(self, model_name):
        if model_name in self._predefinedOptions:
            return True
            
        for vendor in self._supportedVendors:
            if model_name.lower().startswith(vendor):
                return True
                
        return False
        
    def showModelOptions(self, event):
        self._modelPopupMenu.removeAll()
        
        for option in self._predefinedOptions:
            menuItem = JMenuItem(option, actionPerformed=lambda e, opt=option: self.selectModel(opt))
            self._modelPopupMenu.add(menuItem)
            
        self._modelPopupMenu.show(self._extender.modelSelectButton, 0, self._extender.modelSelectButton.getHeight())
    
    def selectModel(self, model):
        self._extender.aiModelTextField.setText(model)


class ApiUrlPlaceholderListener(FocusListener):
    """实现API URL输入框的占位符效果"""
    def __init__(self, extender, placeholder):
        self._extender = extender
        self.placeholder = placeholder
        self.is_placeholder = True
        
    def focusGained(self, e):
        """获得焦点时，如果是占位符文本，清空并恢复正常颜色"""
        if self.is_placeholder:
            field = e.getSource()
            if field.getText() == self.placeholder:
                field.setText("")
                from java.awt import Color
                field.setForeground(Color.BLACK)
                self.is_placeholder = False
    
    def focusLost(self, e):
        """失去焦点时，如果为空，恢复占位符文本"""
        field = e.getSource()
        if not field.getText() or field.getText().strip() == "":
            field.setText(self.placeholder)
            from java.awt import Color
            field.setForeground(Color.GRAY)
            self.is_placeholder = True
        else:
            self.is_placeholder = False


class SavedHeaderChange(ActionListener):
    def __init__(self, extender):
        self._extender = extender

    def actionPerformed(self, e):
        selectedTitle = self._extender.savedHeadersTitlesCombo.getSelectedItem()
        headers = [x for x in self._extender.savedHeaders if x['title'] == selectedTitle]
        self._extender.replaceString.setText(headers[0]['headers'])


class DocumentListener(DocumentListener):
    def __init__(self, extender):
        self._extender = extender
        
    def changedUpdate(self, e):
        SwingUtilities.invokeLater(self.validateModel)
        
    def removeUpdate(self, e):
        SwingUtilities.invokeLater(self.validateModel)
        
    def insertUpdate(self, e):
        SwingUtilities.invokeLater(self.validateModel)
        
    def validateModel(self):
        try:
            model_name = self._extender.aiModelTextField.getText().strip()
            if not model_name:
                JOptionPane.showMessageDialog(
                    None,
                    get_text("model_empty", "模型名称不能为空"),
                    get_text("warning", "警告"),
                    JOptionPane.WARNING_MESSAGE
                )
                return
                
            if not self._extender.configurationTab.validateModel(model_name):
                JOptionPane.showMessageDialog(
                    None,
                    get_text("unsupported_model", "暂不支持该厂商模型，请联系开发者"),
                    get_text("warning", "警告"),
                    JOptionPane.WARNING_MESSAGE
                )
                # 清空无效输入
                self._extender.aiModelTextField.setText("")
        except Exception as e:
            pass

