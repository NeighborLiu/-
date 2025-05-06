import json
import os

def merge_jsonl_files(input_files, output_file):
    """
    合并多个 JSONL 文件到一个文件中。
    
    :param input_files: 输入的 JSONL 文件路径列表
    :param output_file: 输出的合并后的 JSONL 文件路径
    """
    print(output_file)
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for input_file in input_files:
            print(f"Processing file: {input_file}")
            current_json=""
            with open(input_file, 'r', encoding='utf-8') as infile:
                for line in infile:
                    stripped_line = line.strip()
                    if stripped_line:
                        current_json += stripped_line
                        try:
                            # 尝试解析当前累积的 JSON
                            data = json.loads(current_json)
                            compact_json = json.dumps(data, ensure_ascii=False)  # 转换为紧凑格式
                            outfile.write(compact_json + '\n')
                            current_json = ""  # 重置累积器
                        except json.JSONDecodeError:
                            # 如果解析失败，继续累积下一行
                            continue
# 示例用法
input_files = []
for root, dirs, files in os.walk(r"C:\Users\liusongling\Desktop\科研小组\github\agents_testcase_generator\envs_generator\gen_testcases_by_deepseek\check_result_folder"):  # 遍历文件夹及其子文件夹
    for file in files:
        if file.endswith(".jsonl") and file[0:4]=="0402":  # 检查文件后缀
            input_files.append(os.path.join(root, file))  # 添加完整路径
            print(file)
if len(input_files)>1 :
    output_file = './merged_output.jsonl'  # 输出的合并后的文件
    merge_jsonl_files(input_files, output_file)
else:
    print("没有2个即以上满足条件的jsonl文件！")