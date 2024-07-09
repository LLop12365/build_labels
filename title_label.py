from typing import List
from utils import FILE_PATH
import json
import jieba

jieba.load_userdict(FILE_PATH + 'source/dict_text.txt')

class cut_words():
    """
    分词，结合标签进行分类
    """
    def __init__(self):
        with open(FILE_PATH + 'source/dict_ori.json', 'r', encoding='utf-8') as f_d:
            self.dict_ori =  json.load(f_d)

        self.label_list = []
        with open(FILE_PATH + 'source/label.txt', 'r', encoding='utf-8') as f_la:
            for la in f_la.readlines():
                self.label_list.append(la.strip('\n'))
        
        f_d.close()
        f_la.close()

    def work(self, strs: str) -> List:
        """
        分词
        
        Args:
            strs: 输入的句子
        
        Output:
            标签
        """
        res = []
        # seg_list = list(jieba.cut(strs, cut_all=True))
        seg_list = jieba.lcut(strs, cut_all=False)
        for word in seg_list:
            if word in self.dict_ori:
                res += self.dict_ori[word]

            if word in self.label_list:
                res.append(word)
        
        return list(set(res))

if __name__ == '__main__':
    f_path = open(FILE_PATH + 'title.txt', 'r', encoding='utf-8')
    
    stc = f_path.readlines()[4]
    print(stc)
    Cut = cut_words()
    res = []
    res.append(Cut.work(stc))

    print(res)
    # f_path.close()
    
