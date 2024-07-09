import os
import torch
import cn_clip.clip as clip_cn
from cn_clip.clip import load_from_name, available_models
from PIL import Image
from utils import FILE_PATH
from typing import List

class CN_CLIP():
    """中文CLIP"""
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = load_from_name("ViT-B-16", device=self.device, download_root=FILE_PATH)
        self.model.eval()
    
    def loaded(self, pic_path: str, label_list: List[str])-> List[List[float]]:
        """
        读取文件夹中的图片，并进行匹配

        Args:
            pic_path: 输入图片的位置
            label_list: 句子标签列表（对标签进行优化，更符合clip场景）

            output: 二维数组，每一行表示某一帧的匹配结果
        """
        prob = []
        for pic in os.listdir(pic_path):
            img = Image.open(pic_path+pic)
            image = self.preprocess(img.crop((0, 0, img.size[0], img.size[1]-30))).unsqueeze(0).to(self.device)
            text = clip_cn.tokenize(label_list).to(self.device)

            logits_per_image, logits_per_text = self.model.get_similarity(image, text)
            tmp_prob = logits_per_image.softmax(dim=-1).cpu().detach().numpy()[0]

            prob.append(tmp_prob)

        return prob
    
    def output(self, prob: List[List[float]], ori_list: List[str], cover_value: float, k: int)-> dict:
        """
        将各张图片的结果输出组合为一个字典

        Args:
            cover_value: 超参，阈值，大于阈值的数取对应的索引，取值范围[0-1)
            ori_list: 原始的没有经过处理的标签列表
            k: 超参，输出索引的个数
        """
        res = {}
        for pr in prob:
            num = 0
            sort_prob = sorted(list(zip(pr, ori_list)), reverse=True)
            for va, la in sort_prob:
                if va < cover_value:
                    continue
                if num < k:
                    if la not in res:
                        res[la] = 0
                    res[la] += 1
                    num += 1
                if num >= k:
                    break

        return res
