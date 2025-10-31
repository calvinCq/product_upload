#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
敏感词过滤器模块

负责检测和过滤文本中的敏感词，确保生成的内容符合微信小店规范。
"""

import re
from typing import List, Set, Optional


class SensitiveWordFilter:
    """
    敏感词过滤器类
    
    用于检测和过滤文本中的敏感词，支持自定义敏感词列表和替换字符。
    """
    
    def __init__(self, sensitive_words: Optional[List[str]] = None):
        """
        初始化敏感词过滤器
        
        Args:
            sensitive_words: 敏感词列表，如果为None，则使用默认敏感词列表
        """
        # 默认敏感词列表，根据微信小店教育培训类目规则
        self.default_sensitive_words = [
            "评估", "测评", "服务", "咨询", "1v1", 
            "改善", "高效", "最", "方案", "独家", 
            "第一", "报告", "深度分析", "检查", 
            "合作洽谈", "挑选安心好物"
        ]
        
        # 使用提供的敏感词列表或默认列表
        self.sensitive_words = sensitive_words if sensitive_words else self.default_sensitive_words
        
        # 将敏感词列表转换为集合，提高查找效率
        self.sensitive_words_set = set(self.sensitive_words)
        
        # 编译正则表达式，用于全局匹配敏感词
        self.sensitive_words_pattern = self._compile_sensitive_words_regex()
    
    def _compile_sensitive_words_regex(self) -> re.Pattern:
        """
        编译敏感词正则表达式
        
        Returns:
            编译后的正则表达式对象
        """
        # 对敏感词进行排序，确保较长的词先匹配（避免被短词截断）
        sorted_words = sorted(self.sensitive_words, key=len, reverse=True)
        
        # 转义特殊字符并构建正则表达式
        escaped_words = [re.escape(word) for word in sorted_words]
        pattern = '|'.join(escaped_words)
        
        return re.compile(pattern, re.IGNORECASE)
    
    def contains_sensitive(self, text: str) -> bool:
        """
        检查文本是否包含敏感词
        
        Args:
            text: 待检查的文本
            
        Returns:
            True if 文本包含敏感词，否则 False
        """
        if not text:
            return False
        
        # 使用正则表达式进行全局匹配
        return bool(self.sensitive_words_pattern.search(text))
    
    def filter_text(self, text: str, replacement: str = "*") -> str:
        """
        过滤文本中的敏感词
        
        Args:
            text: 待过滤的文本
            replacement: 用于替换敏感词的字符串，默认为星号
            
        Returns:
            过滤后的文本
        """
        if not text:
            return text
        
        # 使用正则表达式替换所有敏感词
        filtered_text = self.sensitive_words_pattern.sub(replacement, text)
        
        return filtered_text
    
    def get_detected_words(self, text: str) -> List[str]:
        """
        获取文本中检测到的敏感词列表
        
        Args:
            text: 待检查的文本
            
        Returns:
            检测到的敏感词列表，不包含重复项
        """
        if not text:
            return []
        
        # 找出所有匹配的敏感词
        matches = self.sensitive_words_pattern.findall(text)
        
        # 去重并返回
        return list(set(matches))
    
    def add_sensitive_word(self, word: str) -> None:
        """
        添加新的敏感词
        
        Args:
            word: 要添加的敏感词
        """
        if word and word not in self.sensitive_words_set:
            self.sensitive_words.append(word)
            self.sensitive_words_set.add(word)
            # 重新编译正则表达式
            self.sensitive_words_pattern = self._compile_sensitive_words_regex()
    
    def add_sensitive_words(self, words: List[str]) -> None:
        """
        批量添加敏感词
        
        Args:
            words: 要添加的敏感词列表
        """
        for word in words:
            self.add_sensitive_word(word)
    
    def remove_sensitive_word(self, word: str) -> bool:
        """
        移除敏感词
        
        Args:
            word: 要移除的敏感词
            
        Returns:
            True if 成功移除，False if 敏感词不存在
        """
        if word in self.sensitive_words_set:
            self.sensitive_words.remove(word)
            self.sensitive_words_set.remove(word)
            # 重新编译正则表达式
            self.sensitive_words_pattern = self._compile_sensitive_words_regex()
            return True
        return False
    
    def clear_sensitive_words(self) -> None:
        """
        清空所有敏感词
        """
        self.sensitive_words.clear()
        self.sensitive_words_set.clear()
        self.sensitive_words_pattern = re.compile(r'^$')
    
    def get_sensitive_words(self) -> List[str]:
        """
        获取所有敏感词
        
        Returns:
            敏感词列表的副本
        """
        return self.sensitive_words.copy()


# 测试代码
if __name__ == "__main__":
    # 创建过滤器实例
    filter = SensitiveWordFilter()
    
    # 测试文本
    test_text = "这是一个评估服务，提供1v1咨询和最专业的方案分析。"
    
    print("原始文本:", test_text)
    print("包含敏感词:", filter.contains_sensitive(test_text))
    print("检测到的敏感词:", filter.get_detected_words(test_text))
    print("过滤后的文本:", filter.filter_text(test_text))
    
    # 测试自定义替换字符
    print("使用自定义替换字符:", filter.filter_text(test_text, "[敏感词]"))
    
    # 测试添加新敏感词
    filter.add_sensitive_word("专业")
    print("添加新敏感词后检测到的敏感词:", filter.get_detected_words(test_text))
    
    # 测试移除敏感词
    filter.remove_sensitive_word("专业")
    print("移除敏感词后检测到的敏感词:", filter.get_detected_words(test_text))