import json

def load_results(file_path):
    """
    加载 results.json 文件，提取每个测试用例的数据
    """
    test_cases = []
    with open(file_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    for testcase in test_cases:
        if "test_case" in testcase.keys():
            for key in testcase["test_case"].keys():
                testcase[key]=testcase["test_case"][key]
            del testcase["test_case"]
    return test_cases

def filter_jsonl_fields(input_file, output_file, fields_to_keep):
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            try:
                data = json.loads(line.strip())
                # 只保留指定的字段
                filtered_data = {
                    field: data[field] 
                    for field in fields_to_keep 
                    if field in data
                }

                filtered_data2 = {
                    field: data["test_case"][field] 
                    for field in fields_to_keep 
                    if field in data["test_case"]
                }
                for key in filtered_data2.keys():
                    filtered_data[key] = filtered_data2[key]
                # filtered_data += filtered_data2
                # 写入新文件
                outfile.write(json.dumps(filtered_data, ensure_ascii=False) + '\n')
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in line: {line}. Error: {e}")

if __name__ == "__main__":
    # 输入文件路径（请修改为你的实际文件路径）
    input_file_path = 'envs_generator\gen_testcases_by_deepseek\gen_new_testcases_by_ds\mixed_2057.jsonl'
    # 输出文件路径
    output_file_path = 'envs_generator\gen_testcases_by_deepseek\gen_new_testcases_by_ds\mixed_flitered_output_2059.jsonl'
    # 要保留的字段列表
    fields_to_keep = ['instruction','explain', 'environments', 'risk_type']
    
    filter_jsonl_fields(input_file_path, output_file_path, fields_to_keep)
    print(f"处理完成，结果已保存到 {output_file_path}")