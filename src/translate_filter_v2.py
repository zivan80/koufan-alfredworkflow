#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import os
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import time
import hashlib

def get_workflow_data_dir():
    """获取workflow数据目录"""
    bundle_id = "com.translator.alfred"
    data_dir = os.path.expanduser(f"~/Library/Application Support/Alfred/Workflow Data/{bundle_id}")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def get_cache_file():
    """获取缓存文件路径"""
    return os.path.join(get_workflow_data_dir(), "translation_cache.json")

def load_cache():
    """加载翻译缓存"""
    cache_file = get_cache_file()
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                # 清理超过24小时的缓存
                current_time = time.time()
                cleaned_cache = {}
                for key, value in cache.items():
                    if current_time - value.get('timestamp', 0) < 86400:  # 24小时
                        cleaned_cache[key] = value
                return cleaned_cache
        except:
            pass
    return {}

def save_cache(cache):
    """保存翻译缓存"""
    cache_file = get_cache_file()
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except:
        pass

def get_cache_key(text, config):
    """生成缓存键"""
    # 使用文本、模型和提示词生成唯一键
    key_data = f"{text}|{config.get('model', '')}|{config.get('prompt', '')}"
    return hashlib.md5(key_data.encode('utf-8')).hexdigest()

def should_translate(text):
    """判断是否应该进行翻译"""
    # 过滤条件：
    # 1. 长度至少3个字符
    # 2. 包含中文字符
    # 3. 不以常见的中间标点符号结尾（避免句子未完成就翻译）
    # 4. 有足够的非标点字符
    # 5. 如果包含逗号但没有完整的句子结构，可能未完成
    
    if len(text) < 3:
        return False
    
    # 检查是否包含中文字符
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
    if not has_chinese:
        return False
    
    # 检查是否以中间标点符号结尾（表示句子可能未完成）
    incomplete_punctuation = '，、；：'
    if text.rstrip().endswith(tuple(incomplete_punctuation)):
        return False
    
    # 检查非标点字符数量
    import string
    chinese_punctuation = '，。！？；：""''（）【】《》、'
    all_punctuation = string.punctuation + chinese_punctuation
    non_punct_chars = [char for char in text if char not in all_punctuation and not char.isspace()]
    
    # 至少需要3个非标点字符
    if len(non_punct_chars) < 3:
        return False
    
    # 额外检查：如果包含逗号但句子很短且可能未完成
    # 例如："你好，世" 可能是 "你好，世界" 的一部分
    if '，' in text:
        # 如果逗号后面的内容很少，可能是未完成的句子
        comma_parts = text.split('，')
        if len(comma_parts) == 2:  # 只有一个逗号
            after_comma = comma_parts[1].strip()
            # 如果逗号后只有1-2个字符，可能未完成
            after_comma_chars = [char for char in after_comma if char not in all_punctuation and not char.isspace()]
            if len(after_comma_chars) <= 2:
                return False
    
    return True

def load_config():
    """加载配置"""
    config_file = os.path.join(get_workflow_data_dir(), "config.json")
    default_config = {
        "api_url": "https://api.openai.com/v1/chat/completions",
        "api_key": "",
        "model": "gpt-3.5-turbo",
        "prompt": "请将以下中文翻译成自然、口语化的英文，适合在聊天、论坛等非正式场合使用。保持原意的同时，让表达更加地道和自然："
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            pass
    
    return default_config

def translate_text(text, config):
    """调用API翻译文本"""
    if not config.get("api_key"):
        return "错误：请先配置API Key（使用 tset 命令）"
    
    # 检查缓存
    cache = load_cache()
    cache_key = get_cache_key(text, config)
    
    if cache_key in cache:
        return cache[cache_key]['translation']
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "Colloquial-Translator/2.1",
        "Accept": "application/json"
    }
    
    data = {
        "model": config.get("model", "gpt-3.5-turbo"),
        "messages": [
            {
                "role": "system",
                "content": config.get("prompt", "请将以下中文翻译成自然、口语化的英文：")
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        req = urllib.request.Request(
            config.get("api_url", "https://api.openai.com/v1/chat/completions"),
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in result and len(result['choices']) > 0:
                translated_text = result['choices'][0]['message']['content'].strip()
                
                # 保存到缓存
                cache[cache_key] = {
                    'translation': translated_text,
                    'timestamp': time.time()
                }
                save_cache(cache)
                
                return translated_text
            else:
                return "翻译失败：API返回格式错误"
                
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_msg)
            if 'error' in error_data:
                return f"API错误：{error_data['error'].get('message', '未知错误')}"
        except:
            pass
        return f"HTTP错误：{e.code} {e.reason}"
    except urllib.error.URLError as e:
        return f"网络错误：{e.reason}"
    except Exception as e:
        return f"翻译失败：{str(e)}"

def speak_text(text):
    """使用系统语音朗读文本"""
    try:
        # 使用macOS的say命令
        subprocess.run(["say", text], check=False)
    except:
        pass

def main():
    if len(sys.argv) < 2:
        # 返回空结果
        result = {
            "items": [
                {
                    "uid": "empty",
                    "title": "请输入要翻译的中文文本",
                    "subtitle": "输入中文后将显示翻译结果 | Cmd+回车朗读",
                    "arg": "",
                    "valid": False
                }
            ]
        }
        print(json.dumps(result, ensure_ascii=False))
        return
    
    text = sys.argv[1].strip()
    if not text:
        # 返回空结果
        result = {
            "items": [
                {
                    "uid": "empty",
                    "title": "请输入要翻译的中文文本",
                    "subtitle": "输入中文后将显示翻译结果 | Cmd+回车朗读",
                    "arg": "",
                    "valid": False
                }
            ]
        }
        print(json.dumps(result, ensure_ascii=False))
        return
    
    config = load_config()
    
    # 检查配置
    if not config.get("api_key"):
        result = {
            "items": [
                {
                    "uid": "error",
                    "title": "请先配置API Key",
                    "subtitle": "使用 tset 命令进行配置",
                    "arg": "",
                    "valid": False
                }
            ]
        }
        print(json.dumps(result, ensure_ascii=False))
        return
    
    # 智能判断是否应该翻译
    if not should_translate(text):
        result = {
            "items": [
                {
                    "uid": "waiting",
                    "title": f"输入中: {text}",
                    "subtitle": "继续输入完整内容以开始翻译...",
                    "arg": "",
                    "valid": False
                }
            ]
        }
        print(json.dumps(result, ensure_ascii=False))
        return
    
    # 进行翻译
    translated = translate_text(text, config)
    
    # 检查是否是错误信息
    is_error = any(translated.startswith(prefix) for prefix in [
        "错误：", "翻译失败：", "API错误：", "HTTP错误：", "网络错误："
    ])
    
    if is_error:
        result = {
            "items": [
                {
                    "uid": "error",
                    "title": "翻译失败",
                    "subtitle": translated,
                    "arg": "",
                    "valid": False
                }
            ]
        }
    else:
        # 创建两个选项：普通复制和朗读
        result = {
            "items": [
                {
                    "uid": "translation",
                    "title": translated,
                    "subtitle": f"原文: {text} | 回车复制 | Cmd+回车朗读",
                    "arg": translated,
                    "valid": True,
                    "mods": {
                        "cmd": {
                            "subtitle": f"朗读: {translated}",
                            "arg": f"speak:{translated}"
                        }
                    }
                }
            ]
        }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()