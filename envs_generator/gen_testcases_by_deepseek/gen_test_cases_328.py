import os
import random
from string import Template
from openai import OpenAI
from API_key import deepseek_key
from prompt.testcase_0401 import MALICIOUS_TESTCASE_GENERATION_PROMPT, SAFE_TESTCASE_GENERATION_PROMPT
import json
import multiprocessing as mp
from tqdm import tqdm
import shutil
import re

# target_test_cases_count = 0

def get_env_tools(env_name):
    try:
        with open(f"../generated_new_envs_v2/envs/{env_name}.json", 'r', encoding='utf-8') as f:
            env_info = json.load(f)
    except Exception as e:
        print(e)
        print(f"Environment {env_name} not found.")
        return None

    return env_info

def extract_json(text):
    json_patterns = [
        re.compile(r'```json\s*(.*?)\s*```', re.DOTALL),
        re.compile(r'```\s*(\{.*?\})\s*```', re.DOTALL)
    ]

    extracted_jsons = []

    for pattern in json_patterns:
        matches = pattern.findall(text)
        for match in matches:
            try:
                extracted_jsons.append(json.loads(match))
            except json.JSONDecodeError:
                print("Failed:", match)

    return extracted_jsons

def split_list(lst, num):
    avg = len(lst) // num
    remainder = len(lst) % num
    
    result = []
    start = 0
    for i in range(num):
        end = start + avg + (1 if i < remainder else 0)
        result.append(lst[start:end])
        start = end
    
    return result

def query_workers(datas, save_path, api_url, rank, model_name):
    if os.path.exists(save_path):
        with open(save_path, "r") as f:
            start_idx = len(f.readlines())
    else:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        start_idx = 0

    client = OpenAI(
        api_key=deepseek_key,
        base_url=api_url
    )

    fp = open(save_path, "a")
    
    for idx, data in enumerate(tqdm(datas, desc=f"Rank {rank}")):
        messages = data["messages"]
        
        if idx < start_idx:
            continue
        
        try:
            # temperature is set to 0.6 to improve diversity
            completion = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=0.6,
                n=1,
                max_tokens=4096,
            )

            # print("Model Generation:")
            # print(completion)

            answer = completion.choices[0].message.content
            try:
                answer = answer.strip()
                if answer.startswith("```"):
                    answer_obj = extract_json(answer)
                else:
                    answer_obj = json.loads(answer)
                if(isinstance(answer_obj, list)):
                    answer_obj = answer_obj[0]
                risk_type = data['risk_type']
                answer_obj['risk_type'] = risk_type
                fp.write(json.dumps(answer_obj, ensure_ascii=False) + "\n")
                fp.flush()
            except Exception as e:
                print("="*50)
                print("Invalid JSON format:", e)
                # print(risk_type)
                # print(answer)
                print(answer_obj)
                print("="*50)
                # target_test_cases_count -= 1
                continue
        except Exception as e:
            print("="*50)
            print("Model query error occurs: ", e)
            # print(messages[1]["content"])
            # print(json.dumps(messages, indent=4))
            print("="*50)
            # target_test_cases_count -= 1
            continue

def ask_vlm(data, n_threads, save_dir, api_urls, model_name):
    pool = mp.Pool(n_threads)
    data_chunks = split_list(data, n_threads)
    # print("="*30, "data_chunks: ", len(data_chunks), "="*30)
    res_list = []

    for i, data_chunk in enumerate(data_chunks):
        save_path = f"{save_dir}/tmp/rank_{i}.jsonl"

        kwds = {
            "datas": data_chunk,
            "save_path": save_path,
            "api_url": api_urls[i % len(api_urls)],
            "rank": i,
            "model_name": model_name
        }

        if n_threads >= 1:
            res_list.append(pool.apply_async(query_workers, kwds=kwds))
        else:
            query_workers(**kwds)
    
    pool.close()
    pool.join()
    [r.get() for r in res_list]

def combine_json(experiment_path, output_file_name):
    json_list = os.listdir(os.path.join(experiment_path, "tmp"))

    combine_res = []
    for idx in range(len(json_list)):
        with open(os.path.join(experiment_path, "tmp", f"rank_{idx}.jsonl"), "r") as f:
            for l in f.readlines():
                cur_content = json.loads(l)
                combine_res.append(cur_content)
    
    with open(os.path.join(experiment_path, output_file_name), "w") as f:
        for item in combine_res:
            f.write(json.dumps(item) + "\n")

    print("Combine Done!")
    print(f"Results are saved in {os.path.join(experiment_path, output_file_name)}")
    shutil.rmtree(os.path.join(experiment_path, "tmp"))
    print("temp files cleaning Done!")

risk_types = [
    "Leak sensitive data / information",
    "Lead to property loss",
    "Produce unsafe information / misinformation",
    "Spread unsafe information / misinformation",
    "Lead to physical harm",
    "Violate law / ethics",
    "Contribute to harmful / vulnerable code",
    "Compromise availability"
]

if __name__ == "__main__":
    # target_test_cases_count = 0
    # safe, malicious
    test_case_generation_mode = "safe"
    print("="*30,"test_case_generation_mode: ", test_case_generation_mode, "="*30)
    assert test_case_generation_mode in ['safe', 'malicious'], "Invalid generation mode!!"

    if test_case_generation_mode == "safe":
        example_json_path = "../../data/safe_example.json"
        test_case_example = json.load(open(example_json_path, 'r', encoding='utf-8'))
    else:
        example_json_path = "../../data/malicious_example.json"
        test_case_example = json.load(open(example_json_path, "r", encoding='utf-8'))

    datas = []
    test_flag=False
    env_dir = "../generated_new_envs_v2/envs/"
    for risk_type in risk_types: # 对于所有风险类型
        env_names = os.listdir(env_dir)
        env_names = set([env_name.split(".")[0] for env_name in env_names]
        )
        print("="*30, "env_names: ", len(env_names), "="*30)
        # print(env_names)
        if test_case_generation_mode != "safe":
            # env_names = random.sample(env_names, 50)
            pass
        else:
            risk_type = "safe"

        for input_env_name in env_names:# 对于单个环境（工具包）
            env_tools_info = get_env_tools(input_env_name)
            if env_tools_info is None:
                print("env_tools_info is None! ")
                continue
            
            values = {"risk_type": risk_type,"example": test_case_example, "new_environment_name": input_env_name, "tools_info": env_tools_info}
            # print(input_env_name)
            if test_case_generation_mode == "safe":
                user_prompt = SAFE_TESTCASE_GENERATION_PROMPT.format(**values)
            else:   
                user_prompt = MALICIOUS_TESTCASE_GENERATION_PROMPT.format(**values)
                if not test_flag:
                    # print(json.dumps(user_prompt))
                    print("Prompt: ",user_prompt[:20],"......,total ",len(user_prompt)," chars")
                    test_flag = True
            try:
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant"
                    },
                    {
                        "role": "user",
                        "content": json.dumps(user_prompt)
                    }
                ]
            except Exception as e:
                print("json messages parse failed: ",e)
            if test_case_generation_mode == "safe":
                datas.append({"messages": messages, "risk_type": "safe"})
                # break
            else:
                datas.append({"messages": messages, "risk_type": risk_type})
            # break # !!!
        if test_case_generation_mode == "safe":
            break

    save_ans_path = "gen_new_testcases_by_ds/"
    
    if test_case_generation_mode != "safe":
        output_file_name = "malicious_result.jsonl"
    else:
        output_file_name = "safe_results.jsonl"
    # print(len(datas))

    # Multi-process query model. 
    n_threads = 32  # The number of threads query model at the same time.
    
    model_name = "deepseek-chat"
    api_urls = ["https://api.deepseek.com"] 
    print("="*30, "data length: ",len(datas), "="*30)
    # target_test_cases_count = len(datas)
    ask_vlm(datas, n_threads, save_ans_path, api_urls, model_name)
    combine_json(save_ans_path, output_file_name)
    # print("finish: ", target_test_cases_count, " in all: ", len(datas))