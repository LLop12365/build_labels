import os
import json
import shutil
import time
import datetime
from utils import FILE_PATH
from ori_CLIP import CN_CLIP
from title_label import cut_words
from ori_video_cut import cut_pic
from typing import List
from sql import mysql_connect, meterial_list, write_table

def mkdir_file(path1: str) -> None:
    """
    为图片创建文件夹

    Args:
        path1: 路径名称
    """
    if not os.path.exists(path1):
        os.makedirs(path1)

def del_dir(path1: str) -> None:
    """
    删除文件夹下的子文件夹和所有文件

    Args:
        path1: 路径名称
    """
    shutil.rmtree(path1)

def read_title(path1: str) -> List:
    """
    读取title文件

    Args:
        path1: title文件路径
    
    Output:
        title组成的list
    """
    title = []
    fp = open(path1, 'r', encoding='utf-8')
    for line in fp.readlines():
        title.append(line.strip('\n'))

    return title

def get_video_label(dict1: dict, k: int) -> List:
    """
    将字典按值进行排序，然后按照指定的数取值

    Args:
        dict1: 输入的字典，值为数字,
        k: 输入的需要取得top k的个数，如果不足就全取

    Output:
        数量排名top k的标签
    """
    res_video_label = []
    sort_cur_dict = sorted(dict1.items(), key=lambda x: x[1], reverse=True)

    if len (sort_cur_dict) >= 4:
        for t_la in sort_cur_dict[:k]:
            if t_la[1] > 2:
                res_video_label.append(t_la[0])
    else:
        for t_la in sort_cur_dict:
            if t_la[1] > 2:
                res_video_label.append(t_la[0])
    
    return res_video_label

def mix_label(dict_ori: dict, video_labels: List, title_labels: List) -> List:
    """
    将视频标签和标签标签取并集
    
    Args:
        video_label: 视频标签
        title_label: title标签
    
    Output:
        融合后的标签
    """
    res = []
    for v_la in video_labels:
        if '卡牌' in title_labels and v_la == '抽卡':
            continue
        else:
            res.append(v_la)

        if v_la in dict_ori:
            res += dict_ori[v_la]

    if '抽卡' in res and '充值卡' in res:
        res.remove('抽卡')

    if '小游戏' not in title_labels or '关系网' in title_labels:
        return list(set(res+title_labels))  
    else:
        return title_labels

def build_sentence_list(path: str):
    """
    将每一个label转化为一句话

    Args:
        path: 路径
    
    Output:
        转化前的标签，转化后的标签
    """
    with open(path, 'r', encoding='utf-8') as f_d:
        dict_label_cut = json.load(f_d)
    
    label_list = []
    label_string = []

    for label in dict_label_cut:
        label_list.append(label)
        # label_string.append("图中包含{}的内容".format(label))
        label_string.append(dict_label_cut[label])

    return label_list, label_string

def load_init():
    """
    初始化模型和标签
    """
    ori_label_str_path = FILE_PATH + 'source/dict_label_cut.json'
    with open(FILE_PATH + 'source/dict_ori.json', 'r', encoding='utf-8') as f_d:
        dict_ori =  json.load(f_d)

    label_list, convert_label_list = build_sentence_list(ori_label_str_path)    
    cnl = CN_CLIP()
    Cut = cut_words()

    return dict_ori, label_list, convert_label_list, cnl, Cut

def out_shell(connection, cursor, res):
    """
    输出结果
    """
    print("开始写入material_labels数据库", flush=True)
    cur_time = time.time()
    # try:
    #     write_num = write_table(connection, cursor, res)
    # except:
    connection.ping(reconnect=True) # 可能会有连接超时的情况，出现了就进行重连
    write_num = write_table(connection, cursor, res)
    
    print("一共处理{}个视频，共写入material_label表{}条。花费{}s".format(len(res), write_num, round(time.time()-cur_time), 2), flush=True)


def main(dict_material, dict_ori, label_list, convert_label_list, cnl, Cut, state=1) -> dict:
    cur_hour = datetime.datetime.now().hour
    dic_pic = {}

    flag = 0 # 判断是否写入补录文件
    num = 0 # 计数，后续需要从什么地方开始写入
    for material_info in dict_material:
        if datetime.datetime.now().minute >= 55 or datetime.datetime.now().hour != cur_hour:
            # 每个小时第55分停止
            flag = num
            break

        cur_time = time.time()
        if material_info['id'] not in dic_pic:
            dic_pic[material_info['id']] = []
        
        title_label = Cut.work(material_info['title'])
        if '小游戏' in title_label:
            dic_pic[material_info['id']] = title_label
        else:
            out_pic_path = FILE_PATH + 'pics/' + material_info['path'].split('/')[-1] + '/'
            mkdir_file(out_pic_path)

            video_path = '/sucai_upload/' + material_info['path'][15:]
            try:
                cut_pic(video_path=video_path, out_path=out_pic_path, num_images=3)   
            except:
                num += 1
                continue
            # clip获取每个镜头的标签
            tmp_out = cnl.loaded(pic_path=out_pic_path, label_list=convert_label_list)
            cur_dict = cnl.output(prob=tmp_out, cover_value=0.1, ori_list=label_list, k=3)
            # 融合每个镜头的标签
            video_label = get_video_label(cur_dict, k=4)
            # 视频标签和标题标签的融合
            dic_pic[material_info['id']] = mix_label(dict_ori, video_label, title_label)
            
            del_dir(path1=out_pic_path)

        print(material_info['id'], 'finished, cost time:', round(time.time()-cur_time, 2), 's', flush=True)
        num += 1

    if state == 1 and flag != 0:
        # 正常有数据而且有数据残留的情况下，追加写入补录文件
        tmp_supplement = dict_material[num:]
        with open(FILE_PATH + 'logs/supplement.json', 'r+') as file:
            try:
                current_data = json.load(file)
            except json.JSONDecodeError:
                current_data = []
            current_data.extend(tmp_supplement)
            file.seek(0)
            json.dump(current_data, file, indent=4)
            file.truncate()
    elif state == 2 and flag != 0:
        # 补录情况下有数据残留，只取需要截断的数据重新，写入补录文件
        tmp_supplement = dict_material[num:]
        json_data = json.dumps(tmp_supplement, ensure_ascii=False, indent=4)
        with open(FILE_PATH + 'logs/supplement.json', 'w') as file:
            file.write(json_data)
    elif state == 2 and flag == 0:
        # 补录情况下全部运行完成，清空补录的json文件
        with open(FILE_PATH + 'logs/supplement.json', 'w') as file:
            file.close()

    return dic_pic

if __name__ == '__main__':
    cur_hour = datetime.datetime.now().hour
    # 数据库连接
    cnx, cursor = mysql_connect()
    state = 1
    # 数据加载
    dict_material = meterial_list(cursor)
    if len(dict_material) == 0:
        # 如果上一个小时没有新素材产生
        print("上一个小时没有新素材产生，开始补录数据", flush=True)
        with open(FILE_PATH + 'logs/supplement.json', 'r') as file:
            try:
                dict_material = json.load(file)
                state = 2
            except json.JSONDecodeError:
                dict_material = []
        if len(dict_material) == 0:
            # 当前没有需要补录的数据，就退出
            print("当前没有需要补录的数据", flush=True)
        else:
            print("当前补录的数据剩余{}个素材".format(len(dict_material)), flush=True)
    else:
        print("上一个小时产生{}个新素材".format(len(dict_material)), flush=True)

    # 模型和参数加载
    dict_ori, label_list, convert_label_list, cnl, Cut = load_init()
    # 主函数，结果输出
    res_labels = main(dict_material, dict_ori, label_list, convert_label_list, cnl, Cut, state)

    if len(res_labels) != 0:
        out_shell(cnx, cursor, res_labels)

    if datetime.datetime.now().minute <= 50 and datetime.datetime.now().hour == cur_hour:
        print("当前小时内时间有剩余，开始补录数据", flush=True)
        with open(FILE_PATH + 'logs/supplement.json', 'r') as file:
            try:
                dict_material_et = json.load(file)
                state = 2
            except json.JSONDecodeError:
                dict_material_et = []
        if len(dict_material_et) == 0:
            # 当前没有需要补录的数据，就退出
            print("当前没有需要补录的数据", flush=True)
        else:
            print("当前补录的数据剩余{}个素材".format(len(dict_material_et)), flush=True)
            res_labels_et = main(dict_material_et, dict_ori, label_list, convert_label_list, cnl, Cut, state)
            if len(res_labels_et) != 0:
                out_shell(cnx, cursor, res_labels_et)

    cnx.close()
    cursor.close()
