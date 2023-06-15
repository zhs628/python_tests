import streamlit as st
import numpy as np
import os
from test2 import DataProcessor, TextData, Test


@st.cache_resource
def load_data(path, view_mode):
    
    data = np.load(path, allow_pickle=True)
    
    filter_obj = {'只看通过的':'true', '只看不通过的':'false', '我都要看':'none'}[view_mode]

    if filter_obj != 'none':
        filtered_data = np_tolist(data, filter_obj)
    if filter_obj == 'none':
        filtered_data = data
    
    return filtered_data


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

def np_tolist(np_data, filter_obj):

    data = np_data.tolist()
    
    new_data = []
    for qusetion in data:
        
        new_qusetion = []
        for solution in qusetion:
            
            new_solution = []
            for input_output in solution:
                
                new_inout = []
                for e in input_output:
                    if e != None:
                        new_inout.append(e)
                        
                if new_inout == []:
                    continue
                if new_inout[3] != filter_obj:
                    continue
                new_solution.append(input_output)
                
            if new_solution == []:
                continue
            new_qusetion.append(new_solution)
            
        if new_qusetion == []:
            continue
        new_data.append(new_qusetion)
    
    return new_data

mode = st.radio('选择模式', ['浏览', '更新测试项目文件', '开始测试'])

# --------------------------------------
if mode == '浏览':
    
    data_path = st.selectbox(
        f'选择文件 "data.npy" 在目录及其子目录 {os.getcwd()}', find_data_npy_files(".")
    )

    

    view_mode = st.radio('选择模式', ['只看通过的', '只看不通过的', '我都要看'])


    filtered_data = load_data(data_path, view_mode)



    if len(filtered_data) == 0:
        st.header('Not Found')

    else:
        question_index = 0
        if len(filtered_data) != 1:
            question_index = st.slider("question", 0, len(filtered_data) - 1, 0, 1)

        solution_index = 0
        if len(filtered_data[question_index]) != 1:
            solution_index = st.slider("solution", 0, len(filtered_data[question_index]) - 1, 0, 1)

        input_output_index = 0
        if len(filtered_data[question_index][solution_index]) != 1:
            input_output_index = st.slider(
                "input,output", 0, len(filtered_data[question_index][solution_index]) - 1, 0, 1
            )

        display_list = filtered_data[question_index][solution_index][input_output_index]

        display_dict = {
            "solution": display_list[0],
            "input": display_list[1],
            "output": display_list[2],
            "test_passed?": display_list[3],
        }

        st.header("test_passed?")
        display_dict["test_passed?"]

        col1, col2 = st.columns(2)
        with col1:
            st.header("solution")
            st.code(display_dict['solution'])
        with col2:
            st.header("input")
            st.code(display_dict['input'])
            st.header("output")
            st.code(display_dict['output'])

# --------------------------------------
if mode == '更新测试项目文件':
    
    base_dict_path = st.selectbox(
        f'选择问题文件夹所在的目录 在目录及其子目录{os.getcwd()}', find_folder_0000(".")
    )
    save_dict_path = st.selectbox(
        f'选择文件 "data.npy" 在目录及其子目录 {os.getcwd()}', find_data_npy_files(".")
    )

    save_dict_path = os.path.dirname(save_dict_path)

    if st.button('开始'):
        data_processor = DataProcessor(base_dict_path=base_dict_path, save_dict_path=save_dict_path)
        data_processor.run_in_streamlit()
        data_processor.to_TextData().save()
# --------------------------------------
if mode == '开始测试':
    
    save_dict_path = st.selectbox(
        f'选择文件 "data.npy" 在目录及其子目录 {os.getcwd()}', find_data_npy_files(".")
    )

    save_dict_path = os.path.dirname(save_dict_path)

    if st.button('开始'):
        test = Test(save_dict_path=save_dict_path)
        test.run_in_streamlit()
        test.text_data.save()