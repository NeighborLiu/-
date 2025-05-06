import json
import random

def shuffle_and_merge_jsonl(file1_path, file2_path, output_path):
    # 读取第一个文件的所有行
    with open(file1_path, 'r', encoding='utf-8') as f1:
        lines1 = [line.strip() for line in f1 if line.strip()]
    
    # 读取第二个文件的所有行
    with open(file2_path, 'r', encoding='utf-8') as f2:
        lines2 = [line.strip() for line in f2 if line.strip()]
    
    # 合并两个列表
    combined = lines1 + lines2
    
    # 随机打乱顺序
    random.shuffle(combined)
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as out:
        for line in combined:
            out.write(line + '\n')

if __name__ == "__main__":
    # 输入文件路径
    file1 = "envs_generator/gen_testcases_by_deepseek/gen_new_testcases_by_ds/malicious_result_risk_evaluation.jsonl"
    file2 = "envs_generator/gen_testcases_by_deepseek/gen_new_testcases_by_ds/safe_results_risk_evaluation.jsonl"
    
    # 输出文件路径
    output_file = "envs_generator/gen_testcases_by_deepseek/gen_new_testcases_by_ds/mixed_2030.jsonl"
    
    # 执行合并和打乱
    shuffle_and_merge_jsonl(file1, file2, output_file)
    print(f"文件已成功合并并打乱，保存到 {output_file}")