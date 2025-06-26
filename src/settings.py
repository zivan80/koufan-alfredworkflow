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
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            pass
    
    return default_config

def save_config(config):
    """保存配置"""
    config_file = os.path.join(get_workflow_data_dir(), "config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_available_models(api_url, api_key):
    """从API实时获取可用模型列表"""
    if not api_key or not api_url:
        return []
    
    # 构建models API URL
    # 从 domain.com/v1/chat/completions 提取 domain.com/v1
    if '/chat/completions' in api_url:
        base_url = api_url.replace('/chat/completions', '')
    elif '/completions' in api_url:
        base_url = api_url.replace('/completions', '')
    else:
        # 如果URL不包含标准端点，假设它是基础URL
        base_url = api_url.rstrip('/')
    
    models_url = f"{base_url}/models"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Colloquial-Translator/2.0",
        "Accept": "application/json"
    }
    
    try:
        print(f"🔍 调试信息:")
        print(f"   原始URL: {api_url}")
        print(f"   基础URL: {base_url}")
        print(f"   模型URL: {models_url}")
        print(f"   API Key: {api_key[:8]}..." if len(api_key) > 8 else f"   API Key: {api_key}")
        
        req = urllib.request.Request(models_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'data' in result:
                models = []
                for model in result['data']:
                    if 'id' in model:
                        models.append(model['id'])
                print(f"✅ 成功获取到 {len(models)} 个模型")
                return sorted(models)
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"❌ HTTP错误 {e.code}: {e.reason}")
        print(f"   错误详情: {error_msg}")
        try:
            error_data = json.loads(error_msg)
            if 'error' in error_data:
                print(f"   API错误信息: {error_data['error']}")
        except:
            pass
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
    
    return []

def test_api_connection(api_url, api_key, model):
    """测试API连接"""
    if not api_key or not api_url or not model:
        return False, "配置信息不完整"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Colloquial-Translator/2.0",
        "Accept": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 5
    }
    
    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'choices' in result:
                return True, "连接成功"
            else:
                return False, "API返回格式错误"
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_msg)
            if 'error' in error_data:
                return False, f"API错误: {error_data['error'].get('message', '未知错误')}"
        except:
            pass
        return False, f"HTTP错误: {e.code} {e.reason}"
    except Exception as e:
        return False, f"连接错误: {str(e)}"

def show_dialog(title, message, default_answer=""):
    """显示输入对话框"""
    script = f'''
    set userInput to text returned of (display dialog "{message}" default answer "{default_answer}" with title "{title}")
    return userInput
    '''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None

def show_choice_dialog(title, message, choices):
    """显示选择对话框"""
    choices_str = '", "'.join(choices)
    script = f'''
    set choiceList to {{"{choices_str}"}}
    set userChoice to choose from list choiceList with title "{title}" with prompt "{message}"
    if userChoice is false then
        return ""
    else
        return item 1 of userChoice
    end if
    '''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None

def show_notification(title, text):
    """显示系统通知"""
    script = f'''
    display notification "{text}" with title "{title}"
    '''
    subprocess.run(["osascript", "-e", script])

def setup_form():
    """一次性表单式设置"""
    config = load_config()
    
    # 步骤1: 设置API URL
    api_url = show_dialog("步骤1/4: 设置API URL", 
                         "请输入API URL (例如: https://api.openai.com/v1/chat/completions):", 
                         config.get("api_url", "https://api.openai.com/v1/chat/completions"))
    if not api_url:
        return
    
    # 步骤2: 设置API Key
    api_key = show_dialog("步骤2/4: 设置API Key", 
                         "请输入您的API Key:", 
                         config.get("api_key", ""))
    if not api_key:
        return
    
    # 步骤3: 获取并选择模型
    show_notification("获取模型", "正在从API获取可用模型列表...")
    models = get_available_models(api_url, api_key)
    
    if not models:
        show_notification("警告", "无法获取模型列表，请手动输入模型名称")
        model = show_dialog("步骤3/4: 设置模型", 
                           "请手动输入模型名称 (例如: gpt-3.5-turbo):", 
                           config.get("model", "gpt-3.5-turbo"))
    else:
        model = show_choice_dialog("步骤3/4: 选择模型", 
                                  f"从API获取到 {len(models)} 个可用模型，请选择:", 
                                  models)
    
    if not model:
        return
    
    # 步骤4: 设置翻译提示词
    prompt = show_dialog("步骤4/4: 自定义翻译提示词", 
                        "请输入翻译提示词 (可使用默认值):", 
                        config.get("prompt", "请将以下中文翻译成自然、口语化的英文，适合在聊天、论坛等非正式场合使用。保持原意的同时，让表达更加地道和自然："))
    if not prompt:
        prompt = config.get("prompt", "请将以下中文翻译成自然、口语化的英文，适合在聊天、论坛等非正式场合使用。保持原意的同时，让表达更加地道和自然：")
    
    # 保存配置
    new_config = {
        "api_url": api_url,
        "api_key": api_key,
        "model": model,
        "prompt": prompt
    }
    save_config(new_config)
    
    # 测试连接
    show_notification("测试连接", "正在测试API连接...")
    success, message = test_api_connection(api_url, api_key, model)
    
    if success:
        show_notification("设置完成", "✅ 配置保存成功，API连接正常！")
    else:
        show_notification("设置完成", f"⚠️ 配置已保存，但连接测试失败: {message}")

def main():
    config = load_config()
    
    # 显示主菜单
    menu_choices = [
        "快速设置 (推荐)",
        "查看当前配置",
        "测试API连接",
        "高级设置"
    ]
    
    choice = show_choice_dialog("口语翻译设置", "请选择操作:", menu_choices)
    
    if not choice:
        return
    
    if choice == "快速设置 (推荐)":
        setup_form()
    
    elif choice == "查看当前配置":
        config_text = f"""当前配置:
        
API URL: {config.get('api_url', '未设置')}
API Key: {'已设置 (' + config.get('api_key', '')[:8] + '...)' if config.get('api_key') else '未设置'}
模型: {config.get('model', '未设置')}
提示词: {config.get('prompt', '未设置')[:30]}..."""
        
        script = f'''
        display dialog "{config_text}" with title "当前配置" buttons {{"确定"}} default button "确定"
        '''
        subprocess.run(["osascript", "-e", script])
    
    elif choice == "测试API连接":
        if not config.get("api_key") or not config.get("api_url") or not config.get("model"):
            show_notification("错误", "请先完成配置设置")
            return
        
        show_notification("测试连接", "正在测试API连接...")
        success, message = test_api_connection(config.get("api_url"), config.get("api_key"), config.get("model"))
        
        if success:
            show_notification("测试成功", "✅ API连接正常")
        else:
            show_notification("测试失败", f"❌ {message}")
    
    elif choice == "高级设置":
        # 原来的逐项设置菜单
        advanced_choices = [
            "修改API URL",
            "修改API Key", 
            "重新选择模型",
            "修改翻译提示词"
        ]
        
        advanced_choice = show_choice_dialog("高级设置", "请选择要修改的项目:", advanced_choices)
        
        if advanced_choice == "修改API URL":
            new_url = show_dialog("修改API URL", "请输入新的API URL:", config.get("api_url", ""))
            if new_url:
                config["api_url"] = new_url
                save_config(config)
                show_notification("设置成功", "API URL已更新")
        
        elif advanced_choice == "修改API Key":
            new_key = show_dialog("修改API Key", "请输入新的API Key:", config.get("api_key", ""))
            if new_key:
                config["api_key"] = new_key
                save_config(config)
                show_notification("设置成功", "API Key已更新")
        
        elif advanced_choice == "重新选择模型":
            if not config.get("api_key") or not config.get("api_url"):
                show_notification("错误", "请先设置API URL和API Key")
                return
            
            show_notification("获取模型", "正在获取可用模型列表...")
            models = get_available_models(config.get("api_url"), config.get("api_key"))
            
            if models:
                selected_model = show_choice_dialog("选择模型", f"从API获取到 {len(models)} 个可用模型:", models)
                if selected_model:
                    config["model"] = selected_model
                    save_config(config)
                    show_notification("设置成功", f"已选择模型: {selected_model}")
            else:
                show_notification("错误", "无法获取模型列表，请检查API配置")
        
        elif advanced_choice == "修改翻译提示词":
            new_prompt = show_dialog("修改翻译提示词", "请输入新的翻译提示词:", config.get("prompt", ""))
            if new_prompt:
                config["prompt"] = new_prompt
                save_config(config)
                show_notification("设置成功", "翻译提示词已更新")

if __name__ == "__main__":
    main()