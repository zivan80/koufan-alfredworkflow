#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess

def speak_text(text):
    """使用系统语音朗读文本"""
    try:
        # 使用macOS的say命令，选择更好的英文语音
        subprocess.run(["say", "-v", "Alex", text], check=False)
    except Exception as e:
        # 如果失败，尝试默认语音
        try:
            subprocess.run(["say", text], check=False)
        except:
            pass

def main():
    if len(sys.argv) < 2:
        return
    
    arg = sys.argv[1].strip()
    
    if arg.startswith("speak:"):
        # 朗读功能
        text_to_speak = arg[6:]  # 移除 "speak:" 前缀
        speak_text(text_to_speak)
        print(text_to_speak)  # 同时输出到剪贴板
    else:
        # 普通复制功能
        print(arg)

if __name__ == "__main__":
    main()