import os
import sys
import multiprocessing.dummy as mp
from typing import Callable, Tuple

assert sys.version_info <= (3, 9), "需要使用 Python 3.9 或更低版本"

class TestCase:
    def __init__(self, name: str, input: str, output: str, solution: str):
        self.name = name
        self.input = input
        self.output = output
        self.solution = solution

    def __str__(self):
        s = [
            f'测试用例：{self.name}',
            '输入：', self.input,
            '输出：', self.output,
            '答案：', self.solution
        ]
        return '\n'.join(s)

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def load_case(path: str):
    """加载一个测试用例"""
    name = os.path.basename(path)
    input_path = os.path.join(path, 'input.txt')
    output_path = os.path.join(path, 'output.txt')
    solution_path = os.path.join(path, 'solution.py')
    return TestCase(
        name,
        read_file(input_path),
        read_file(output_path),
        read_file(solution_path)
    )

def iter_cases(root: str) -> Tuple[int, TestCase]:
    """迭代根路径下的所有测试用例"""
    i = 0
    for case in os.listdir(root):
        yield i, load_case(os.path.join(root, case))
        i += 1

class TestStatus:
    Success = 0         # 成功
    Error = 1           # 运行错误
    Timeout = 2         # 运行超时
    WrongAnswer = 3     # 答案错误

class TestResult:
    def __init__(self, name: str, status: int, message=''):
        self.name = name
        self.status = status
        self.message = message

    def __str__(self):
        s = f'{self.name}: {self.status}'
        if self.message:
            s += '\n' + self.message
        return s

class TestReport:
    """由一组测试结果组成的测试报告"""
    def __init__(self, results: dict):
        self.results = results

    def number_success(self):
        """成功的测试用例数量"""
        return sum(1 for res in self.results.values() if res.status == TestStatus.Success)
    
    def number_failed(self):
        """失败的测试用例数量"""
        return sum(1 for res in self.results.values() if res.status != TestStatus.Success)

    def summary(self) -> dict:
        return {
            "成功": self.number_success(),
            "失败": self.number_failed(),
            "总计": len(self.results)
        }

class Pipeline:
    """测试管线，继承此类实现具体测试逻辑"""

    def __init__(self, root: str):
        if not os.path.exists(root):
            raise FileNotFoundError(f'路径不存在：{root!r}')
        self.root = root
        self.results = {}

    def process_case(self, case: TestCase) -> TestCase:
        """对测试用例进行预处理"""
        case.input = case.input.strip()
        case.output = case.output.strip()
        return case

    def __len__(self):
        """计算所有测试用例的数量"""
        return len(os.listdir(self.root))

    def run_case(self, case: TestCase) -> TestResult:
        """运行单个测试用例"""
        raise NotImplementedError
    
    def on_case_begin(self, i, total, case: TestCase):
        """开始运行一个测试用例"""
        pass

    def on_case_end(self, i, total, res: TestResult):
        """结束运行一个测试用例"""
        pass

    def _step(self, i, case, nb_cases):
        self.on_case_begin(i, nb_cases, case)
        case = self.process_case(case)
        res = self.run_case(case)
        assert isinstance(res, TestResult)
        assert res.name == case.name
        self.results[case.name] = res
        self.on_case_end(i, nb_cases, res)

    def run(self):
        """运行测试"""
        self.results = {}
        nb_cases = len(self)
        for i, case in iter_cases(self.root):
            self._step(i, case, nb_cases)
        return TestReport(self.results)

    def run_multithread(self, thread_count: int = 4):
        """多线程运行测试"""
        self.results = {}
        nb_cases = len(self)
        pool = mp.Pool(thread_count)
        pool.apply(lambda x: self._step(*x, nb_cases), iter_cases(self.root))
        pool.close()
        pool.join()
        return TestReport(self.results)