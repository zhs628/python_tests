import streamlit as st
import numpy as np
import os
from test2 import DataProcessor, TextData, Test


@st.cache_resource
def load_data(path):
    return np.load(path, allow_pickle=True)


def find_data_npy_files(root_path):
    npy_file_paths = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            if filename == "data.npy":
                npy_file_paths.append(os.path.join(dirpath, filename))
    return npy_file_paths

def find_folder_0000(root_path):
    folder_0000_paths = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        if '0000' in dirnames:
            folder_0000_paths.append(dirpath)
    return folder_0000_paths


mode = st.radio('选择模式', ['浏览', '更新测试项目文件', '开始测试'])

# --------------------------------------
if mode == '浏览':

    data_path = st.selectbox(
        '选择文件 "data.npy" 在目录及其子目录 ' + str(os.getcwd()), find_data_npy_files(".")
    )

    data = load_data(data_path)
    if st.button('刷新'):
        st.cache_resource.clear()
        data = load_data(data_path)

    question_index = st.slider("question", 0, len(data) - 1, 0, 1)

    # 转成列表并删除其中值为None的元素
    lst = data[question_index].tolist()
    new_lst = []
    for solution in lst:
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
        new_lst.append(new_solution)

    solution_index = 0
    if len(new_lst) - 1 != 0:
        solution_index = st.slider("solution", 0, len(new_lst) - 1, 0, 1)

    input_output_index = 0
    if len(new_lst[solution_index]) - 1 != 0:
        input_output_index = st.slider(
            "input,output", 0, len(new_lst[solution_index]) - 1, 0, 1
        )

    display_list = new_lst[solution_index][input_output_index]
    display_dict = {
        "solution": display_list[0],
        "input": display_list[1],
        "output": display_list[2],
        "test_passed?": display_list[3],
    }
    display_dict

# --------------------------------------
if mode == '更新测试项目文件':
    
    base_dict_path = st.selectbox(
        '选择问题文件夹所在的目录 在目录及其子目录' + str(os.getcwd()), find_folder_0000(".")
    )
    save_dict_path = st.selectbox(
        '选择文件 "data.npy" 在目录及其子目录 ' + str(os.getcwd()), find_data_npy_files(".")
    )
    
    save_dict_path = os.path.dirname(save_dict_path)
    
    if st.button('开始'):
        data_processor = DataProcessor(base_dict_path=base_dict_path, save_dict_path=save_dict_path)
        data_processor.run_in_streamlit()
        data_processor.to_TextData().save()
# --------------------------------------
if mode == '开始测试':
    
    save_dict_path = st.selectbox(
        '选择文件 "data.npy" 在目录及其子目录 ' + str(os.getcwd()), find_data_npy_files(".")
    )
    
    save_dict_path = os.path.dirname(save_dict_path)

    if st.button('开始'):
        test = Test(save_dict_path=save_dict_path)
        test.run_in_streamlit()
        test.text_data.save()