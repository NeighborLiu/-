from env_gen import ENV_JSON_GENERATION_PROMPT
from API_key import deepseek_key
import os
from openai import OpenAI
import json
import multiprocessing as mp
from tqdm import tqdm
import shutil
from string import Template
import re

# 根据设定的线程数量 和 工具包中工具规模，生成工具包

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

def query_workers(datas, save_path, api_url, rank, model_name, new_tools_count = 5):
    if os.path.exists(save_path):
        with open(save_path, "r") as f:
            start_idx = len(f.readlines())
    else:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        start_idx = 0

    # For openai models, you can add your OpenAI key here.
    client = OpenAI(
        api_key=deepseek_key, 
        base_url=api_url
    )

    fp = open(save_path, "a")
    
    # new_tools_count = 5 
    for idx, data in enumerate(datas):
        # You should follow the template to generate a new tool description for {toolkit_name}, and the description of this toolkit is as follows:{toolkit_description}. The generated tool should satisfy the description of the toolkit, and should not contain same tool name we already have in our toolkit: {already_tool_name}. Your answer MUST output in JSON format.

        toolkit_name = data['toolkit_name']
        toolkit_desc = data['toolkit_desc']
        already_tool_name = []

        if idx < start_idx:
            continue
        
        try:
            for i in tqdm(range(new_tools_count), desc=f"Rank {rank}, finished tookit {idx}, total {len(datas)}"):
                template = Template(ENV_JSON_GENERATION_PROMPT)

                values = {
                    "toolkit_name": toolkit_name,
                    "toolkit_description": toolkit_desc,
                    "already_tool_name": already_tool_name
                }

                prompt = template.substitute(**values)

                response = client.chat.completions.create(
                    model=model_name,
                    temperature=0.6,
                    max_tokens=4096,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant"},
                        {"role": "user", "content": prompt},
                    ],
                    stream=False
                )
                answer = response.choices[0].message.content
                print(answer)

                try:
                    answer = answer.strip()
                    if answer.startswith("```"):
                        answer_obj = extract_json(answer)[0]
                    # the JSON object must be str, bytes or bytearray, not list
                    else:
                        answer_obj = json.loads(answer)
                    answer_obj['toolkit_name'] = toolkit_name

                    tool_name = answer_obj['name']
                    already_tool_name.append(tool_name)

                    fp.write(json.dumps(answer_obj, ensure_ascii=False) + "\n")
                    fp.flush()
                except Exception as e:
                    print("Invalid JSON format:", e)
                    print(answer)
                    continue
        except Exception as e:
            print("Model query error occurs: ", e)
            continue

def ask_vlm(data, n_threads, save_dir, api_urls, model_name):
    pool = mp.Pool(n_threads)
    data_chunks = split_list(data, n_threads)
    res_list = []

    # print(data_chunks)
    for i, data_chunk in enumerate(data_chunks):
        save_path = f"{save_dir}/tmp/rank_{i}.jsonl"

        # print(api_urls[i % len(api_urls)])
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

    print("Cleaning temp files...")
    shutil.rmtree(os.path.join(experiment_path, "tmp"))
    print("Cleaning Done!")

if __name__ == "__main__":
    tool_desc = open("camel_tools.md",'r',encoding='utf-8').readlines()

    datas = []
    for l in tool_desc:
        toolkit_split = l.split("|")
        toolkit_name = toolkit_split[1].strip()
        toolkit_desc = toolkit_split[2].strip()

        datas.append({"toolkit_name": toolkit_name, "toolkit_desc": toolkit_desc})

    save_ans_path = "./generated_new_envs/"
    output_file_name = "new_envs.jsonl"

    model_name = "deepseek-chat"
    api_urls = ["https://api.deepseek.com"] 
    n_threads = 32 

    ask_vlm(datas, n_threads, save_ans_path, api_urls, model_name)
    combine_json(save_ans_path, output_file_name)