#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import os
import urllib.request
import urllib.parse
import urllib.error
import subprocess

def get_workflow_data_dir():
    """获取workflow数据目录"""
    bundle_id = "com.translator.alfred"
    data_dir = os.path.expanduser(f"~/Library/Application Support/Alfred/Workflow Data/{bundle_id}")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

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
                # 合并默认配置，确保所有必要的键都存在
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
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "Colloquial-Translator/2.0",
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

def show_notification(title, text):
    """显示系统通知"""
    script = f'''
    display notification "{text}" with title "{title}"
    '''
    subprocess.run(["osascript", "-e", script])

def main():
    if len(sys.argv) < 2:
        print("请输入要翻译的中文文本")
        return
    
    text = sys.argv[1].strip()
    if not text:
        print("请输入要翻译的中文文本")
        return
    
    config = load_config()
    result = translate_text(text, config)
    
    # 输出结果给Alfred
    print(result)
    
    # 显示通知
    if not result.startswith("错误：") and not result.startswith("翻译失败：") and not result.startswith("API错误：") and not result.startswith("HTTP错误：") and not result.startswith("网络错误："):
        show_notification("翻译完成", "已复制到剪贴板")
    else:
        show_notification("翻译失败", result[:50] + "..." if len(result) > 50 else result)

if __name__ == "__main__":
    main()