import os
import json
import asyncio
from datetime import datetime
# from googletrans import Translator  # 需要安装 googletrans==4.0.0-rc1
from deep_translator import GoogleTranslator
import requests
import random

def print_colored_sentence(sentence_name, sentence):
    GREEN_BOLD = "\033[1;32m"
    RESET = "\033[0m"

    print(f"{GREEN_BOLD}{sentence_name}:{RESET} {sentence}\n")

def load_results(file_path):
    """
    加载 results.json 文件，提取每个测试用例的数据
    """
    test_cases = []
    with open(file_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    return test_cases    

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

def youdao_translate(query):
    url = 'http://fanyi.youdao.com/translate'
    data = {
        "i": query,  # 待翻译的字符串
        "from": "AUTO",
        "to": "AUTO",
        "smartresult": "dict",
        "client": "fanyideskweb",
        "salt": "16081210430989",
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "action": "FY_BY_CLICKBUTTION"
    }
    # res = requests.post(url, data=data).json()
    # print(res['translateResult'][0][0]['tgt'])  # 打印翻译后的结果
    response = requests.post(url, data=data)
    
    # 打印服务器返回的原始内容
    print("服务器响应内容:", response.text)
    
    try:
        res = response.json()  # 尝试解析为 JSON
        print(res['translateResult'][0][0]['tgt'])  # 打印翻译后的结果
    except ValueError as e:
        print("JSON 解析失败:", e)

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
    risk = test_case["risk"]
    # 翻译 instruction 和 explain
    instruction_zh = translate_text(instruction)
    explain_zh = translate_text(explain)

    translated_result={
        "index": count,
        "risk": risk,
        "instruction_en": instruction,
        "instruction_zh": instruction_zh,
        "explain_en": explain,
        "explain_zh": explain_zh,
        "environments": test_case["environments"],
        "check_result": check_result
    }

    with open(output_file, "a", encoding="utf-8") as f:
        json.dump(translated_result, f, ensure_ascii=False)
        f.write("\n")

    if check_result != "":
        with open(problem_output_file, "a", encoding="utf-8") as f:
            json.dump(translated_result, f, ensure_ascii=False)

def check_exist_and_translate(file_path = "../valid_safe_test_cases.json", env_dir = "../../environments"):
    """
    检查用例中使用的环境和工具是否存在
    """
    print("Start checking tool exist and translating...")
    file_name = os.path.basename(file_path) # 提取文件名

    current_directory = os.getcwd()
    output_file = f"check_result_folder/{file_name.replace('.jsonl','').replace('.json','')}_check_reports.jsonl"
    output_file = f"{current_directory}/{output_file}"
    if os.path.exists(output_file):
        print(f"已有json文件的检查-翻译结果{output_file}，无需重新生成")
        return output_file
    else:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # 加载测试用例
    test_cases = load_results(file_path)

    # 加载环境数据
    environments = load_environments(env_dir)
    correct_count = 0
    count = 0
    
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
    return output_file

# 以上是用于check_exist_and_translate的所有函数。以下补充新的函数，用于辅助人工检查测试用例

def Manually_inspect(output_file, pick_quantity = 50):
    """
    在jsonl格式的翻译后结果文件中, 利用随机生成的数字, 通过交互窗口来方便用户给测试用例打标签

    参数:
        output_file: jsonl格式的翻译后结果文件路径

    返回:
        无
    """
    # 计算一个 .jsonl 文件中包含的 JSON 对象数量。
    now = datetime.now()
    formatted_date_time = now.strftime("%m%d_%H%M%S")
    manually_check_result_path = f"check_result_folder/{formatted_date_time}_manually_check_result.jsonl"
    data = []
    with open(output_file, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            cur_content = json.loads(l)
            data.append(cur_content)
    json_count = len(data)

    current_directory = os.getcwd()
    save_pick_list_folder = f'{current_directory}\\{json_count}-{pick_quantity}-{os.path.basename(output_file).replace(".jsonl","")}'
    os.makedirs(save_pick_list_folder, exist_ok=True)
    save_pick_list_dir = f'{current_directory}\\{json_count}-{pick_quantity}-{os.path.basename(output_file).replace(".jsonl","")}\\{json_count}-{pick_quantity}-{os.path.basename(output_file).replace(".jsonl",".json")}'
    pick_list = pick_and_sort(json_count, pick_quantity, save_pick_list_dir)
    
    for pick_number in pick_list:
        test_case = data[pick_number]
        clear_screen()
        # print("-"*50)
        # print(f"第{pick_number}个测试用例的内容如下：")
        # print(f"index: \n\t{test_case['index']}\n")
        # print(f"risk: \n\t{test_case['risk']}\n")
        # print(f"instruction: \n\t{test_case['instruction_en']}\n\t{test_case['instruction_zh']}\n")
        # print(f"explain: \n\t{test_case['explain_en']}\n\t{test_case['explain_zh']}\n")
        # 
        print("-"*50)
        print(f"\033[1m第{pick_number}个测试用例的内容如下：\033[0m")
        print_colored_sentence("index", test_case['index'])
        print_colored_sentence("risk", test_case['risk'])
        print_colored_sentence("instruction", test_case['instruction_en'])
        print_colored_sentence("instruction_zh", test_case['instruction_zh'])
        # print_colored_sentence("Reflexion Results", test_case['reflexion_res'])
        print("environments: ")
        for env in test_case["environments"]:
            print(f"\tenv name: {env['name']}")
            print(f"\tenv tools: {env['tools']}")
            print(f"\tenv parameters: {env['parameters']}\n")

        """每个test_case的格式如下：
        translated_result={
            "index": count,
            "risk": risk,
            "instruction_en": instruction,
            "instruction_zh": instruction_zh,
            "explain_en": explain,
            "explain_zh": explain_zh,
            "environments": test_case["environments"],
            "check_result": check_result
        }
        """
        is_valid_flag = input("explain是否准确？若explain正确则输入1，错误则输入2，若不确定则输入3: ")
        check_result = is_right_switch_case(is_valid_flag)
        test_case["check_result"] = check_result
        with open(manually_check_result_path, "a", encoding="utf-8") as f:
            json.dump(test_case, f,indent=4, ensure_ascii=False)
            f.write("\n")
        with open(save_pick_list_dir,"r", encoding="utf-8") as f:
            temp_data = json.load(f)
        
        # 删除列表的第一项
        removed_item = temp_data.pop(0)

        # 将修改后的列表写回文件
        with open(save_pick_list_dir, "w", encoding="utf-8") as f:
            json.dump(temp_data, f, ensure_ascii=False, indent=4)

    os.remove(save_pick_list_dir)
    os.rmdir(save_pick_list_folder)
        
def is_right_switch_case(value):
    switch_dict = {
        '1': '判断正确',
        '2': '判断错误',
        '3': '待定',
    }
    # 使用 get 方法处理默认值
    return switch_dict.get(value, 'Default case')

def pick_and_sort(n, m, save_pick_list_dir):
    """
    从 n 个数字中随机挑选 m 个数字，并返回排序后的结果。

    参数:
        n (int): 总数范围（从 1 到 n）。
        m (int): 需要挑选的数字个数。
    保存在文件中
    返回:
        list: 排序后的随机挑选的数字列表。
    """
    if m > n:
        raise ValueError("m 不能大于 n")
    
    # 检查文件是否存在
    if os.path.exists(save_pick_list_dir):
        with open(save_pick_list_dir, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 确保读取的内容是一个列表
        if isinstance(data, list):
            print(f"成功读取抽样列表: {data}")
            return data
        else:
            print("文件内容不是一个列表")

    # with open("data.json", "w", encoding="utf-8") as f:
    # json.dump(my_list, f, ensure_ascii=False, indent=4)

    picked_numbers = random.sample(range(0, n - 1), m)  # 随机挑选 m 个数字
    res = sorted(picked_numbers)
    print(f"成功创建抽样列表: {res}")
    with open(save_pick_list_dir, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    return res  # 返回排序后的结果

def clear_screen():
    # 使用 ANSI 转义序列清屏
    print("\n"*20)

if __name__ == "__main__":
    # file_path = "../generated_testcases_new_envs/valid_malicious_all_kind_test_cases_reflexion.json"
    # envs_path = "../generated_new_envs/envs/"
    # file_path = "/home/huhaoxuan/safe_agents/agents_testcase_generator/envs_generator/generated_testcases_new_envs/valid_malicious_all_kind_test_cases_reflexion.json"
    # envs_path = "/home/huhaoxuan/safe_agents/agents_testcase_generator/envs_generator/generated_new_envs/envs/"
    # output_file = check_exist_and_translate("../envs_generator/generated_testcases_new_envs/temp_test_file.json", "../envs_generator/generated_new_envs/envs")
    file_path = "../envs_generator/gen_testcases_by_deepseek/gen_new_testcases_by_ds/malicious_results_all_kind_with_fixed_prompt.jsonl"
    envs_path = "../environments"
    output_file = check_exist_and_translate(file_path, envs_path)
    Manually_inspect(output_file, 4)
    