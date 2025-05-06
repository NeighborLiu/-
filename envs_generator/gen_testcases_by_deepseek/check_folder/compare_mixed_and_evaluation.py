import json

def merge_explain_en(original_file, evaluated_file, output_file):
    # 读取原始文件的所有测试用例
    with open(original_file, 'r', encoding='utf-8') as f:
        original_cases = [json.loads(line) for line in f if line.strip()]
    
    # 读取已评估文件的所有测试用例
    with open(evaluated_file, 'r', encoding='utf-8') as f:
        evaluated_cases = [json.loads(line) for line in f if line.strip()]
    
    # 检查文件长度是否一致
    if len(original_cases) != len(evaluated_cases):
        print("警告：两个文件的测试用例数量不一致！")
        print(f"原始文件测试用例数: {len(original_cases)}")
        print(f"评估文件测试用例数: {len(evaluated_cases)}")
        return
    
    # 合并explain_en字段
    merged_cases = []
    for orig_case, eval_case in zip(original_cases, evaluated_cases):
        # 如果原始用例中有explain_en字段，则添加到评估用例中
        if 'explain_en' in orig_case:
            eval_case['explain_en'] = orig_case['explain_en']
        merged_cases.append(eval_case)
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for case in merged_cases:
            f.write(json.dumps(case, ensure_ascii=False) + '\n')
    
    print(f"合并完成，结果已保存到 {output_file}")

if __name__ == "__main__":
    # 文件路径配置
    original_file = "mixed.jsonl"  # 原始测试用例文件
    evaluated_file = "mixed_risk_evaluation.jsonl"  # 风险评估后的文件
    output_file = "merged_final.jsonl"  # 输出文件
    
    # 执行合并
    merge_explain_en(original_file, evaluated_file, output_file)