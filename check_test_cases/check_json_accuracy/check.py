import os
import json
import asyncio
# from googletrans import Translator  # 需要安装 googletrans==4.0.0-rc1
from deep_translator import GoogleTranslator
from datetime import datetime
# 初始化翻译器

def load_results(file_path):
    """
    加载 test_cases.json 文件，提取每个测试用例的数据
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        # 加载 JSON 文件内容到一个 Python 变量中
        data = json.load(file)
    return data

def translate_text(text, src_lang="en", dest_lang="zh-CN"):
    """
    使用 deep-translator 翻译文本
    """
    try:
        translated = GoogleTranslator(source=src_lang, target=dest_lang).translate(text)
        return translated
    except Exception as e:
        print(f"翻译失败: {e}")
        return text  # 如果翻译失败，返回原文

def load_environments(env_dir):
    """
    加载所有环境文件，提取环境名称和工具列表
    """
    environments = {}
    for filename in os.listdir(env_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(env_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                env_data = json.load(f)
                environments[filename.replace('.json','')]={}
                for tool in env_data:
                    environments[filename.replace('.json','')][tool["name"]] = tool["description"]
                    
    return environments

def check_environment_and_tools(test_case, environments):
    """
    检查测试用例中的环境和工具是否真实存在
    """
    missing_environments = []
    missing_tools = []

    for env in test_case["environments"]:
        env_name = env["name"]
        if env_name not in environments.keys():
            missing_environments.append(env_name)
            continue

        available_tools = list(environments[env_name].keys())
        for tool in env["tools"]:
            tool_name = ""
            if isinstance(tool, str): # tool本身就是字符串类型的tool_name
                tool_name = tool
            elif isinstance(tool, dict):
                tool_name = tool["name"]

            if tool_name not in available_tools:
                missing_tools.append((env_name, tool_name))

    return missing_environments, missing_tools

def save_this_translated_result(test_case, output_file, check_result, count):
    """
    保存翻译后的结果
    """
    problem_output_file = output_file.replace('.json', '_problem.json').replace('_results', '')
    instruction = test_case["instruction"]
    explain = test_case["explain"]

    # 翻译 instruction 和 explain
    instruction_zh = translate_text(instruction)
    explain_zh = translate_text(explain)

    translated_result={
        "index": count,
        "instruction_en": instruction,
        "instruction_zh": instruction_zh,
        "explain_en": explain,
        "explain_zh": explain_zh,
        "environments": test_case["environments"],
        "check_result": check_result
    }

    with open(output_file, "a", encoding="utf-8") as f:
        json.dump(translated_result, f, ensure_ascii=False, indent=4)

    if check_result != "":
        with open(problem_output_file, "a", encoding="utf-8") as f:
            json.dump(translated_result, f, ensure_ascii=False, indent=4)

def main():
    # 文件路径
    dst_name = "valid_malicious_test_cases.json"
    results_file = "../" + dst_name
    env_dir = "../../environments"
    # 获取当前的日期和时间
    now = datetime.now()
    formatted_date_time = now.strftime("%m%d_%H%M%S")
    output_file = f"{formatted_date_time}_{dst_name.replace('.jsonl','')}_check_reports.jsonl"

    # 加载测试用例
    test_cases = load_results(results_file)

    # 加载环境数据
    environments = load_environments(env_dir)
    correct_count = 0
    count=0
    # 检查环境和工具是否存在
    print(f"一共有{len(test_cases)}个测试用例")
    for test_case in test_cases:
        print(count, ": ", "-" * 30)
        count += 1
        missing_envs, missing_tools = check_environment_and_tools(test_case, environments)
        check_res = ""
        if missing_envs:
            print(f"测试用例 '{test_case['instruction']}' 中缺失的环境: {missing_envs}")
            check_res = "环境不存在:"
            for env in missing_envs:
                check_res += env
        if missing_tools:
            print(f"测试用例 '{test_case['instruction']}' 中缺失的工具: {missing_tools}")
            if check_res != "":
                check_res += ";工具不存在:"
            else: check_res = "工具不存在:"
            for tool in missing_tools:
                check_res += tool[1] # 由于missing_tools中是（环境、工具）元组
        if not (missing_tools or missing_envs) :
            correct_count += 1
        save_this_translated_result(test_case, output_file, check_res, count)
        # if(count>=20):
        #     break
        
    print("correct_count: ", correct_count)
    # 翻译并保存结果
    print(f"翻译结果已保存到 {output_file}")

if __name__ == "__main__":
    main()