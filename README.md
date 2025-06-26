# Alfred 中英翻译工具

一个用于Alfred的中文到英文翻译工具，支持口语化翻译和语音朗读功能。

## 功能特性

- 中文到英文翻译，输出口语化、自然的英文表达
- 支持语音朗读翻译结果
- 翻译结果缓存，提高响应速度
- 可配置的翻译提示词和模型选择
- 支持OpenAI API和兼容接口

## 系统要求

- macOS 10.10 或更高版本
- Alfred 4 或更高版本（需要Powerpack）
- 有效的OpenAI API密钥或兼容的API服务

## 安装方法

### 方法一：下载Release版本
1. 前往 [Releases页面](https://github.com/zivan80/koufan-alfredworkflow/releases)
2. 下载最新版本的 `.alfredworkflow` 文件
3. 双击文件自动安装到Alfred

### 方法二：手动安装
1. 克隆或下载此仓库
2. 将 `src` 目录中的所有文件复制到Alfred Workflow目录
3. 在Alfred中导入workflow

## 配置

### 基础配置
使用关键词 `tset` 打开配置界面：

1. **API密钥设置**：输入您的OpenAI API密钥
2. **API地址配置**：默认使用OpenAI官方接口，可修改为其他兼容接口
3. **模型选择**：支持gpt-3.5-turbo、gpt-4等模型

### 高级配置
- **翻译提示词**：自定义翻译风格和要求
- **模型管理**：从API获取可用模型列表并选择

## 使用方法

### 基本翻译
1. 激活Alfred（默认快捷键：⌘+Space）
2. 输入 `t` 后跟要翻译的中文文本
3. 按回车键复制翻译结果到剪贴板

### 语音朗读
1. 在翻译结果界面按住 `⌘` 键
2. 按回车键朗读翻译结果

### 示例
```
t 你好世界
→ Hello world

t 这个功能很实用
→ This feature is really useful
```

## 命令列表

| 命令 | 功能 |
|------|------|
| `t [中文文本]` | 翻译中文到英文 |
| `tset` | 打开设置界面 |

## 配置文件

配置文件存储在：
```
~/Library/Application Support/Alfred/Workflow Data/com.translator.alfred/config.json
```

默认配置：
```json
{
  "api_url": "https://api.openai.com/v1/chat/completions",
  "api_key": "",
  "model": "gpt-3.5-turbo",
  "prompt": "请将以下中文翻译成自然、口语化的英文，适合在聊天、论坛等非正式场合使用。保持原意的同时，让表达更加地道和自然："
}
```

## 缓存机制

- 翻译结果会缓存24小时
- 缓存文件位置：`~/Library/Application Support/Alfred/Workflow Data/com.translator.alfred/translation_cache.json`
- 相同文本在缓存期内会直接返回结果，无需重新调用API

## 故障排除

### 常见问题

**翻译失败**
- 检查网络连接
- 确认API密钥正确
- 验证API地址可访问

**无法朗读**
- 确保macOS语音功能正常
- 检查系统音量设置

**配置丢失**
- 重新运行 `tset` 命令配置
- 检查配置文件权限

## 开发

### 项目结构
```
src/
├── handle_action.py      # 处理翻译结果和语音朗读
├── info.plist           # Alfred workflow配置
├── settings.py          # 设置界面和配置管理
├── translate.py         # 基础翻译功能
└── translate_filter_v2.py # 翻译过滤器和缓存
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

