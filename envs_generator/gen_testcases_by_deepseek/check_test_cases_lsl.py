import hashlib
import os
import json
import asyncio
from datetime import datetime
import time
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

def youdao_translate(text, from_lang="auto", to_lang="zh-CHS"):
    
    """
    调用有道智云翻译 API 进行文本翻译。
    :param text: 待翻译的文本
    :param from_lang: 源语言代码，默认为 "auto"（自动检测）
    :param to_lang: 目标语言代码，默认为 "zh-CHS"（简体中文）
    :return: 翻译结果
    """
    url = 'https://openapi.youdao.com/api'
    app_key = '659395bdeef4d8dc'
    app_secret = 'fH7tEDa7GCeokl0AiUkD7CmvyRijf9vU'
    # 生成随机数和当前时间戳
    salt = str(random.randint(10000, 99999))
    cur_time = str(int(time.time()))

    # 构造签名
    sign_str = app_key + text + salt + cur_time + app_secret
    sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    # 构造请求参数
    params = {
        "q": text,
        "from": from_lang,
        "to": to_lang,
        "appKey": app_key,
        "salt": salt,
        "sign": sign,
        "signType": "v3",
        "curtime": cur_time,
    }

    # 发送 POST 请求
    response = requests.post(url, data=params)
    result = response.json()

    # 解析返回结果
    if result.get("errorCode") == "0":
        translation = result["translation"][0]
        return translation
    else:
        error_code = result.get("errorCode")
        raise Exception(f"Translation failed with error code: {error_code}")

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
    # print(json.dumps(test_case))
    print([item["name"] for item in test_case["environments"] if "name" in item])
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
    risk = test_case["risk_type"]
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
        json.dump(translated_result, f,  ensure_ascii=False)
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
        print(count, ": ", "=" * 30)
        count += 1
        missing_envs, missing_tools = check_environment_and_tools(test_case, environments)
        check_res = ""
        if missing_envs:
            print(f'测试用例 "{test_case["instruction"]}" 中缺失的环境: {missing_envs}')
            check_res = "环境不存在:"
            for env in missing_envs:
                check_res += env+";"
        if missing_tools:
            print(f'测试用例 "{test_case["instruction"]}" 中缺失的工具: {missing_tools}')
            check_res = "工具不存在:"
            for tool in missing_tools:
                check_res += tool[1]+";" # 由于missing_tools中是（环境、工具）元组
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
        print_colored_sentence("instruction_en", test_case['instruction_en'])
        print_colored_sentence("instruction_zh", test_case['instruction_zh'])
        print_colored_sentence("explain_en", test_case['explain_en'])
        print_colored_sentence("explain_zh", test_case['explain_zh'])
        # print_colored_sentence("Reflexion Results", test_case['reflexion_res'])
        print_colored_sentence("environments", "")

        for env in test_case["environments"]:
            print_colored_sentence("\tenv name", env['name'])
            print_colored_sentence("\tenv tools", env['tools'])
            if( isinstance(env['parameters'], dict)):
                env['parameters'] = json.dumps(env['parameters']).replace("\\n"," ").replace('\\"','"').replace("  "," ")
            print_colored_sentence("\tenv parameters", env['parameters'])
            # print(f"\tenv name: {env['name']}")
            # print(f"\tenv tools: {env['tools']}")
            # print(f"\tenv parameters: {env['parameters']}\n")

        """每个test_case的格式如下：
        translated_result={
            "index": count,
            "risk": risk,
            "instruction": instruction,
            "instruction_zh": instruction_zh,
            "explain": explain,
            "explain_zh": explain_zh,
            "environments": test_case["environments"],
            "check_result": check_result
        }
        """
        check_result = is_right_switch_case()
        test_case["check_result"] += check_result
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
        
def is_right_switch_case():
    value = '0'
    switch_dict = {
        '1': '判断正确',
        '2': '判断错误',
        '3': '待定',
    }
    while(value not in switch_dict.keys()):
        value = input("explain是否准确？若explain正确则输入1，错误则输入2，若不确定则输入3: ")
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

    
    if m >= n:
        print("m 不能大于 n, 已改为全选")
        picked_numbers = [i for i in range(0 , n)]
    else:
        picked_numbers = random.sample(range(0, n), m)  # 随机挑选 m 个数字
    # with open("data.json", "w", encoding="utf-8") as f:
    # json.dump(my_list, f, ensure_ascii=False, indent=4)

    res = sorted(picked_numbers)
    print(f"成功创建抽样列表: {res}")
    with open(save_pick_list_dir, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    return res  # 返回排序后的结果

def clear_screen():
    # 使用 ANSI 转义序列清屏
    print("\n"*20)

def jsonl_to_json(jsonl_file_path, json_file_path, indent=2):
    """
    将 JSONL 文件转换为格式化的 JSON 文件
    :param jsonl_file_path: 输入的 JSONL 文件路径
    :param json_file_path: 输出的 JSON 文件路径
    :param indent: 缩进空格数（默认 2）
    """
    if(os.path.exists(json_file_path)):
        print("存在jsonl转换后的json文件")
        return 
    json_objects = []
    
    # 读取 JSONL 文件
    with open(jsonl_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:  # 跳过空行
                json_objects.append(json.loads(line))
    
    # 写入 JSON 文件（自动格式化缩进）
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_objects, f, ensure_ascii=False, indent=indent)
    
    print(f"转换完成！输出文件: {json_file_path}")

if __name__ == "__main__":

    # jsonl_file_path = "./check_result_folder/safe_results_with_old_prompt_check_reports.jsonl"
    # json_file_path = jsonl_file_path.replace(".jsonl", ".json")
    # jsonl_to_json(jsonl_file_path, json_file_path)
    # envs_path = "../generated_new_envs_v2/envs"
    # output_file = check_exist_and_translate(json_file_path, envs_path)
    # Manually_inspect(output_file, 50)

    # ==============================================================

    output_file = "./check_result_folder/safe_results_with_old_prompt_check_reports.jsonl"
    Manually_inspect(output_file, 50)
    