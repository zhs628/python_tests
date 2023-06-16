import pandas as pd
import numpy as np
import json
import os
from tqdm import tqdm
import subprocess
import streamlit as st
import psutil
import time
import math

def get_folders(path):
    folders = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            folders.append(item_path)
    return folders

def get_json_names(directory):
    json_files = [file for file in os.listdir(directory) if file.endswith('.json')]
    return json_files

def load_json(path)-> str:
    with open(path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    return data

def normalize(a: str)-> str:
    # replace all \r 
    a = a.replace("\r", "")
    # strip trailing whitespace in each line
    # strip multiple \n
    a = "\n".join([line.rstrip() for line in a.split("\n") if line.rstrip()])
    return a

def run_pipe(cmd, input) -> str:
    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="gbk",
    )
    try:
        stdout, stderr = p.communicate(input=input, timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
        return "", "TimeoutExpired"
    return stdout, stderr


# def cup_sleep():
#     '''
#     根据cpu占有率返回应该睡眠的时间
#     '''
#     cpu_percent = psutil.cpu_percent(interval=0)
#     sleep_time = 0
#     if cpu_percent >= 0.9:
#         sleep_time = 10
#     return sleep_time

# def memory_save():
#     '''
#     根据内存占用率返回保存间隔
#     '''
#     mem_percent = psutil.virtual_memory()[2]
#     save_num = 50
#     if mem_percent < 0.9:
#         save_num = 0
#     return save_num

class TextData:
    """
    以下是np_data中，每一个轴的含义。

       z: question_index
       ^
      /
     /
    .------> x: inputs_outpus_index
    |
    |
    v
    y: solution_index

    ----> t: text:[solution_text, input_text, output_text]


    self.np_data的格式及各维度对应的轴:
    [
        x: [
            y: [
                z: [t:<solution_text>, t:<input_text>, t:<output_text>, t:<is_passed>],
                z: ...

               ]
            y: ...

           ]

        x: ...
    ]



    """

    def __init__(self, save_dict_path, list_data=None):
        self.save_dict_path = save_dict_path
        self.t_indexes = np.array(
            ["solution_text", "input_text", "output_text", "is_passed"]
        )
        if list_data == None:
            self.np_data = np.empty((0, 0, len(self.t_indexes)))
        else:
            list_data = list_data.copy()

            # 假设四维列表为 list_data，已知其第一维有 n1 个元素，第二维有 n2 个元素，
            # 第三维有 n3 个元素，第四维有 n4 个元素
            n1, n2, n3, n4 = len(list_data), \
                            max((len(row) for row in list_data), default=0), \
                            max((len(cell) for row in list_data for cell in row), default=0), \
                            max((len(last) for row in list_data for cell in row for last in cell), default=0)
  
            # 补全缺失元素
            for i in range(n1):
                for j in range(n2):
                    if j >= len(list_data[i]):
                        list_data[i].append([])
                    for k in range(n3):
                        if k >= len(list_data[i][j]):
                            list_data[i][j].append([])
                        for l in range(n4):
                            if l >= len(list_data[i][j][k]):
                                list_data[i][j][k].append(None)

            # 转换成numpy数组
            arr = np.array(list_data)
            
                    
            self.np_data = arr
            # print(json.dumps(self.np_data[136].tolist(), indent=4))

    @property
    def t_len(self):
        return self.np_data.shape[4]

    @property
    def x_len(self):
        return self.np_data.shape[3]

    @property
    def y_len(self):
        return self.np_data.shape[2]

    @property
    def z_len(self):
        return self.np_data.shape[1]
    
    def __call__(self):
        return self.np_data
    
    def save(self):
        np.save(self.save_dict_path+'/data.npy', self.np_data)

    def load(self):
        self.np_data = np.load(self.save_dict_path+'/data.npy', allow_pickle=True)


class DataProcessor:
    def __init__(self, base_dict_path, save_dict_path):
        self.save_dict_path = save_dict_path
        self.base_dict_path = base_dict_path
        self.questions_path = get_folders(base_dict_path)
        self.t_indexes = np.array(
            ["solution_text", "input_text", "output_text", "is_passed"]
        )
        self.list_data = []
    
    # def get_solution_from_file(self, question_index, solution_index)-> str:
    #     """
    #      返回给定的索引问题的解决方案
         
    #      Args:
    #      	 question_index: 问题序号
    #      	 solution_index: 解决方案代码的序号
         
    #      Returns: 
    #      	 解决方案代码的字符串
    #     """
    #     path = self.base_dict_path + '/' +str(question_index).rjust(4, "0") + '/' + 'solutions.json'
    #     return normalize(load_json(path)[solution_index])
    
    # def get_input_from_file(self, question_index, inputs_outpus_index)-> str:
    #     path = self.base_dict_path + '/' +str(question_index).rjust(4, "0") + '/' + 'input_output.json'
    #     return normalize(load_json(path)['inputs'][inputs_outpus_index])
    
    # def get_output_from_file(self, question_index, inputs_outpus_index)-> str:
    #     path = self.base_dict_path + '/' +str(question_index).rjust(4, "0") + '/' + 'input_output.json'
    #     return normalize(load_json(path)['outputs'][inputs_outpus_index])
  
    def get_url_from_file(self, question_path)-> str:
        path = question_path + '/' + 'metadata.json'
        return load_json(path)['url']
   
    def to_TextData(self)-> TextData:
        return TextData(self.save_dict_path, self.list_data)
    
    def append_line(self, z_index, y_index, x_index, line)-> None:
        """
         设置self.list_data对应位置的"solution_text", "input_text", "output_text", "is_passed"
         	 line: 输入的数据，列表长度和self.t_index相同
        """
        
        if z_index >= len(self.list_data):
            for i in range(len(self.list_data), z_index + 1):
                self.list_data.append([])
        if y_index >= len(self.list_data[z_index]):
            for i in range(len(self.list_data[z_index]), y_index + 1):
                self.list_data[z_index].append([])
        if x_index >= len(self.list_data[z_index][y_index]):
            for i in range(len(self.list_data[z_index][y_index]), x_index + 1):
                self.list_data[z_index][y_index].append([])
                    
        self.list_data[z_index][y_index][x_index] = line
        
        
                    
    def run_in_terminal(self)-> None:
        z_index, y_index, x_index = 0,0,0
        for question_index, question_path in tqdm(list(enumerate(self.questions_path)),  desc=' question ', leave=False):
           
            if 'leetcode' in self.get_url_from_file(question_path):
                continue
            
            if 'input_output.json' not in get_json_names(question_path):
                continue
            
            if 'solutions.json' not in get_json_names(question_path):
                continue
            
            y_index, x_index = 0, 0
            for solution_index, solution_str in tqdm(list(enumerate(load_json(question_path + '/' + 'solutions.json'))),  desc=' solution ',  leave=False):
                
                if 'print' not in solution_str:
                    continue
                
                if 'input' not in solution_str:
                    continue
                
                if len(load_json(question_path + '/' + 'input_output.json')['inputs']) == 0:
                    continue
                
                x_index = 0
                for input_output_index, input_output_str in enumerate(zip(load_json(question_path + '/' + 'input_output.json')['inputs'], load_json(question_path + '/' + 'input_output.json')['outputs'])):
                    input_str, output_str = input_output_str
                    input_str, output_str = str(input_str), str(output_str)
                    
                    self.append_line(z_index, y_index, x_index, [normalize(solution_str), normalize(input_str), normalize(output_str), 'false'])
                    x_index += 1
                
                if x_index == 0:
                    continue

                y_index += 1
            
            if y_index == 0:
                continue
            
            z_index += 1
        
        print(f'{len(self.questions_path)} {len(self.list_data)}')
        # print(json.dumps(self.list_data[135:138], indent=4))
    
    def run_in_streamlit(self)-> None:
        import streamlit as st
        from stqdm import stqdm
        z_index, y_index, x_index = 0,0,0
        

        # write_container_1 = st.text(body='')
        # write_container_2 = st.text(body='')
        # save_num = memory_save()
        # write_container_2.write(f'保存间隔: {save_num}')
        
        for question_index, question_path in stqdm(list(enumerate(self.questions_path)),  desc=' question '):
            
            # if question_index // 10 == 0:
            #     sleep_time = cup_sleep()
            #     write_container_1.write(f'执行间隔: {sleep_time}s')
            #     time.sleep(sleep_time)
            
            # save_num -= 1
            # if save_num < 0:
            #     self.to_TextData().save()
            #     save_num = memory_save()
            #     write_container_2.write(f'保存间隔: {save_num}')
           
            if 'leetcode' in self.get_url_from_file(question_path):
                continue
            
            if 'input_output.json' not in get_json_names(question_path):
                continue
            
            if 'solutions.json' not in get_json_names(question_path):
                continue
            
            y_index, x_index = 0, 0
            for solution_index, solution_str in stqdm(list(enumerate(load_json(question_path + '/' + 'solutions.json'))),  desc=' solution ' ):
                
                if 'print' not in solution_str:
                    continue
                
                if 'input' not in solution_str:
                    continue
                
                if len(load_json(question_path + '/' + 'input_output.json')['inputs']) == 0:
                    continue
                
                x_index = 0
                for input_output_index, input_output_str in enumerate(zip(load_json(question_path + '/' + 'input_output.json')['inputs'], load_json(question_path + '/' + 'input_output.json')['outputs'])):
                    input_str, output_str = input_output_str
                    input_str, output_str = str(input_str), str(output_str)
                    
                    if input_str[0] == '[':
                        continue
                    
                    self.append_line(z_index, y_index, x_index, [normalize(solution_str), normalize(input_str), normalize(output_str), 'false'])
                    x_index += 1
                    
                
                if x_index == 0:
                    continue

                y_index += 1
            
            if y_index == 0:
                continue
            
            z_index += 1
        
        print(f'{len(self.questions_path)} {len(self.list_data)}')
        # print(json.dumps(self.list_data[135:138], indent=4))
                    
class Test():
    def __init__(self, save_dict_path):
        
        self.save_dict_path = save_dict_path
        self.text_data = TextData(self.save_dict_path)
        self.text_data.load()
        self.text_data.np_data = self.text_data.np_data
    
    def save(self):
        self.np_data.save()


    def run_in_streamlit(self):
        import streamlit as st
        from stqdm import stqdm
        
        
        
        # write_container_1 = st.text(body='')
        # write_container_2 = st.text(body='')
        
        
        list_questions = []
        
        accuracy_bar = st.progress(0, text='通过数量')
        all_num = 0
        passed_num = 0
        accuracy = 0
        
        # save_num = memory_save()
        for question_index, np_question in stqdm(list(enumerate(self.text_data.np_data)), desc=' question '):
            
            # if question_index // 10 == 0:
            #     sleep_time = int(cup_sleep())
            #     write_container_1.write(f'cup占用率: {round(psutil.cpu_percent(interval=1), 2)}\t执行间隔: {sleep_time}s')
            #     time.sleep(sleep_time)
            
            # save_num -= 1
            # if save_num < 0:
            #     self.to_TextData().save()
            #     save_num = memory_save()
            #     write_container_2.write(f'内存占用率: {round(psutil.virtual_memory().percent, 1)}\t保存间隔: {save_num}')
            
            # 转成列表并删除其中值为None的元素
            list_question = np_question.tolist()
            
            new_list_question = []
            for solution in list_question:
                new_solution = []
                for input_output in solution:
                    new_inout = []
                    for e in input_output:
                        if e != None:
                            new_inout.append(e)
                    if new_inout == []:
                        continue
                    new_solution.append(input_output)
                if new_solution == []:
                    continue
                new_list_question.append(new_solution)
                
            list_question = new_list_question
            
            for solution_index, solution in stqdm(list(enumerate(list_question)), desc=' solution '):
                

                
                with open("tmp.py", "wt", encoding="utf-8") as f:
                    f.write(solution[0][0])
                    
                for input_output_index, input_output in stqdm(list(enumerate(solution)), desc=' input_output '):
                    
                    str_solution, str_input, str_output, str_is_passed = input_output[0], input_output[1], input_output[2], input_output[3]
                    
                    stdout, stderr = run_pipe(["python", "tmp.py"], normalize(str_input))
                    
                    if normalize(stdout) != normalize(str_output):
                        list_question[solution_index][input_output_index][3] = 'false'
                    if normalize(stdout) == normalize(str_output):
                        list_question[solution_index][input_output_index][3] = 'true'
                        passed_num += 1
                    
                    all_num += 1
            
            list_questions.append(list_question)
            
            if all_num > 0:
                accuracy_bar.progress(passed_num/all_num, text=f'通过:{passed_num}  失败:{all_num-passed_num}  总计:{all_num}  通过率:{round(passed_num/all_num, 1)}')
        
        self.text_data = TextData(save_dict_path=self.save_dict_path, list_data=list_questions)


    def run_in_terminal(self):
        
        list_questions = []
        
        for question_index, np_question in tqdm(list(enumerate(self.text_data.np_data)), desc=' question ', leave=False):
            
            # 转成列表并删除其中值为None的元素
            list_question = np_question.tolist()
            
            new_list_question = []
            for solution in list_question:
                new_solution = []
                for input_output in solution:
                    new_inout = []
                    for e in input_output:
                        if e != None:
                            new_inout.append(e)
                    if new_inout == []:
                        continue
                    new_solution.append(input_output)
                if new_solution == []:
                    continue
                new_list_question.append(new_solution)
                
            list_question = new_list_question
            
            for solution_index, solution in tqdm(list(enumerate(list_question)), desc=' solution ', leave=False):
                for input_output_index, input_output in tqdm(list(enumerate(solution)), desc=' input_output ', leave=False):
                    
                    str_solution, str_input, str_output, str_is_passed = input_output[0], input_output[1], input_output[2], input_output[3]
                    
                    stdout, stderr = run_pipe(["python", "tmp.py"], str_input)
                    stdout = normalize(stdout)
                    
                    if stdout != str_output:
                        list_question[solution_index][input_output_index][3] = 'false'
                    if stdout == str_output:
                        list_question[solution_index][input_output_index][3] = 'true'
            
            list_questions.append(list_question)
        
        self.text_data = TextData(save_dict_path=self.save_dict_path, list_data=list_questions)
                    
                        

    
    


if __name__ == '__main__':
    test = Test(save_dict_path='.')
    test.run_in_terminal()
    # text_data = TextData(save_dict_path='.')
    # text_data.load()




