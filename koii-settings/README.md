# Koii Settings

Koii Settings 是 Koii OS 的中央配置應用程序，提供對 AI 代理、語義驅動瀏覽器、任務系統和系統安全的全面控制。

## 功能特性

- **Agent 總覽**: 實時監控和管理 AI 代理的狀態、任務進度
- **AI Browser 設定**: 配置語義驅動瀏覽功能和隱私偏好
- **任務系統管理**: 創建、監控和管理 AI 驅動的任務
- **系統設定**: 調整代理主動性、資源分配和核心參數
- **安全與日誌**: 查看審計日誌和安全事件

## 技術架構

### 前端
- **GTK4**: 現代 UI 工具包
- **libadwaita**: GNOME 風格的 UI 組件
- **Python 3**: 主要編程語言
- **GSettings**: 配置持久化

### 後端整合
- 連接到 Koii OS 核心系統 (`/opt/aios`)
- 與語義驅動 Agent 系統通信
- 實時狀態監控和控制

## 項目結構

```
koii-settings/
├── meson.build              # 主構建配置
├── data/                    # 數據文件
│   ├── org.koii.Settings.gschema.xml      # GSettings schema
│   ├── org.koii.Settings.desktop.in       # Desktop 文件
│   ├── org.koii.Settings.metainfo.xml.in  # AppStream 元數據
│   └── icons/               # 應用程序圖標
├── src/                     # 源代碼
│   ├── main.py             # 應用程序入口
│   ├── window.py           # 主窗口
│   ├── config.py           # 配置管理
│   ├── pages/              # 設置頁面
│   │   ├── base_page.py    # 頁面基類
│   │   ├── agents_page.py  # Agent 總覽
│   │   ├── browser_page.py # AI Browser 設定
│   │   ├── tasks_page.py   # 任務系統
│   │   ├── system_page.py  # 系統設定
│   │   └── security_page.py # 安全與日誌
│   └── backend/            # 後端整合
└── po/                     # 國際化
```

## 構建和安裝

### 依賴項

```bash
# Ubuntu 24.04
sudo apt install \
    meson \
    python3 \
    python3-gi \
    libgtk-4-dev \
    libadwaita-1-dev \
    glib-2.0-dev
```

### 構建

```bash
meson setup build
meson compile -C build
```

### 安裝

```bash
sudo meson install -C build
```

### 開發模式運行

```bash
# 從源代碼目錄運行
./src/koii-settings.in
```

## 配置

所有配置通過 GSettings 管理，schema ID: `org.koii.Settings`

### 主要配置項

- **initiative-level**: Agent 主動性等級 (passive/balanced/highly-initiative)
- **initiative-score-threshold**: 主動性分數閾值 (0.0-1.0)
- **enable-reflexion**: 啟用反思機制
- **browser-semantic-mode**: 啟用語義驅動瀏覽
- **task-auto-planning**: 自動任務規劃
- **enable-audit-log**: 啟用審計日誌

## 開發狀態

### ✅ 已完成
- [x] 項目結構和構建系統
- [x] GSettings schema
- [x] 主窗口和導航系統
- [x] 配置管理
- [x] 頁面基類和 UI 組件

### 🚧 進行中
- [ ] 5 個設置頁面實現
- [ ] 後端整合模塊
- [ ] 語義驅動 Agent 系統增強

### 📋 待完成
- [ ] 圖標設計
- [ ] 安裝腳本
- [ ] ISO 整合
- [ ] 文檔和測試

## 語義驅動 Agent 系統

Koii Settings 的核心特性是管理語義驅動的 AI 代理系統，包括：

### Initiative Score (主動性分數)
- 計算 Agent 是否應該主動提問或推進任務
- 範圍: 0.0 (完全被動) 到 1.0 (高度主動)
- 基於上下文、任務複雜度和用戶偏好

### Semantic Loop (語義循環)
每次 Agent 輸出包含三部分：
1. **Thought**: 內部思考過程
2. **Initiative Action**: 主動行動決策
3. **Response to User**: 用戶響應

### Reflexion (反思機制)
- Agent 自我評估和改進
- 從錯誤中學習
- 優化未來決策

### 架構模式
- **ReAct**: Reasoning + Acting
- **Plan-and-Execute**: 規劃後執行
- **Reflexion**: 自我反思和改進

## 與 Koii OS 整合

Koii Settings 與 Koii OS 核心系統深度整合：

```python
# 連接到 Koii OS 核心
from koii_os.core.kernel import KernelRuntime
from koii_os.agents.base import BaseAgent
from koii_os.llm.registry import LLMRegistry

# 通過 Settings 控制 Agent 行為
kernel.set_initiative_level('highly-initiative')
kernel.enable_reflexion(True)
```

## GNOME 整合

應用程序自動出現在 GNOME 設置面板中：
- Desktop 文件包含 `X-GNOME-Settings-Panel=koii-settings`
- 可通過系統設置訪問
- 支持搜索關鍵詞: AI, Agent, Browser, Koii, LLM, Semantic

## 貢獻

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳情。

## 許可證

GPL-3.0-or-later

## 聯繫方式

- 網站: https://koii.network
- 問題追蹤: https://github.com/koii-network/koii-os/issues
- 開發團隊: dev@koii.network

---

**注意**: 這是一個正在開發中的項目。某些功能可能尚未完全實現。