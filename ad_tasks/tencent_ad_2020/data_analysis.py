#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : Joshua
@Time    : 5/15/20 5:40 PM
@File    : data_analysis.py
@Desc    : 数据分析

"""


import csv
import json
import os
import matplotlib.pyplot as plt
from collections import OrderedDict


def read_data_from_csv_file(file):
    # data = list()
    with open(file, "r", encoding="utf-8-sig") as csvfile:
        csv_reader = csv.reader(csvfile)  # 使用csv.reader读取csvfile中的文件
        header = next(csv_reader)  # 读取第一行每一列的标题
        print("data header: {}".format(header))
        for i, row in enumerate(csv_reader):   # 将 csv 文件中的数据保存到data中
            # data.append(row)
            # if i < 5:
            #     print(row)
            yield row
    # count = len(data)
    # print("data with {} lines".format(count))

def dict_sort(result, limit_num=None):
    """
    字典排序, 返回有序字典
    :param result:
    :param limit_num:
    :return:
    """
    _result_sort = sorted(result.items(), key=lambda x: x[1], reverse=True)
    result_sort = OrderedDict()

    count_limit = 0
    domain_count = 0
    for i in _result_sort:
        if limit_num:
            if i[1] > limit_num:
                result_sort[i[0]] = i[1]
                domain_count += 1
                count_limit += i[1]
        else:
            result_sort[i[0]] = i[1]
    return result_sort


def write_ad_analysis_details_to_file(file, outfile):
    print("start writing ad analysis details to file: {}".format(outfile))
    ad_info = dict()
    ad_info["product_info"] = dict()
    ad_info["advertiser_info"] = dict()
    _count = 0

    for line in read_data_from_csv_file(file):
        _count += 1
        if _count < 6:
            print(line)
        # else:
        #     break
        # 产品信息
        if line[3] in ad_info["product_info"]:
            ad_info["product_info"][line[3]]["_count"] += 1
            if line[2] in ad_info["product_info"][line[3]]:
                ad_info["product_info"][line[3]][line[2]] += 1
            else:
                ad_info["product_info"][line[3]][line[2]] = 1
        else:
            ad_info["product_info"][line[3]] = dict()
            ad_info["product_info"][line[3]]["_count"] = 1
            ad_info["product_info"][line[3]][line[2]] = 1

        # 广告主信息
        if line[5] in ad_info["advertiser_info"]:
            ad_info["advertiser_info"][line[5]]["_count"] += 1
            if line[4] in ad_info["advertiser_info"][line[5]]:
                ad_info["advertiser_info"][line[5]][line[4]] += 1
            else:
                ad_info["advertiser_info"][line[5]][line[4]] = 1
        else:
            ad_info["advertiser_info"][line[5]] = dict()
            ad_info["advertiser_info"][line[5]]["_count"] = 1
            ad_info["advertiser_info"][line[5]][line[4]] = 1

    print("data with {} lines".format(_count))
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(json.dumps(ad_info, ensure_ascii=False, indent=4))
    print("write down")
    return ad_info

def read_data_from_json_file(file):
    print("load data from file: {}".format(file))
    with open(file, "r", encoding="utf-8") as jsonfile:
        info = json.load(jsonfile)
    print("read down")
    return info

def analysis_ad(file, outfile):

    if not os.path.exists(outfile):
        ad_info = write_ad_analysis_details_to_file(file, outfile)
    else:
        ad_info = read_data_from_json_file(outfile)

    # 产品信息统计
    product_count = len(ad_info["product_info"].keys())
    print("\nall products category: {}".format(product_count))
    new_product_info = dict()
    for k, v in ad_info["product_info"].items():
        new_product_info[k] = v["_count"]
    sort_category = dict_sort(new_product_info)
    print("--- details of product category info ---")
    print("{}".format(json.dumps(sort_category, indent=4)))

    # 广告主信息统计
    advertiser_count = len(ad_info["advertiser_info"].keys())
    print("\nall advertisers industry: {}".format(advertiser_count))
    new_advertiser_info = dict()
    for k, v in ad_info["advertiser_info"].items():
        new_advertiser_info[k] = v["_count"]
    sort_industry = dict_sort(new_advertiser_info)
    print("--- details of advertiser industry info ---")
    print("{}".format(json.dumps(sort_industry, indent=4)))

def analysis_user(file, outfile):
    if not os.path.exists(outfile):
        user_info = write_user_analysis_details_to_file(file, outfile)
    else:
        user_info = read_data_from_json_file(outfile)

    # 用户信息统计
    print("\nall age: {}".format(user_info["age_info"].keys()))
    sort_age = dict_sort(user_info["age_info"])
    print("--- details of age info ---")
    print("{}".format(json.dumps(sort_age, indent=4)))
    print("\nall gender: {}".format(user_info["gender_info"].keys()))
    sort_gender = dict_sort(user_info["gender_info"])
    print("--- details of gender info ---")
    print("{}".format(json.dumps(sort_gender, indent=4)))
    print("\nall age with gender: {}".format(user_info["age_gender_info"].keys()))
    sort_age_gender = dict_sort(user_info["age_gender_info"])
    print("--- details of age with gender info ---")
    print("{}".format(json.dumps(sort_age_gender, indent=4)))



def write_user_analysis_details_to_file(file, outfile):
    print("start writing user analysis details to file: {}".format(outfile))
    user_info = dict()
    user_info["age_info"] = dict()
    user_info["gender_info"] = dict()
    user_info["age_gender_info"] = dict()
    _count = 0

    for line in read_data_from_csv_file(file):
        _count += 1
        if _count < 6:
            print(line)
        # else:
        #     break
        # 用户信息
        age_gender = "{}_{}".format(line[1], line[2])
        if age_gender in user_info["age_gender_info"]:
            user_info["age_gender_info"][age_gender] += 1
            if line[1] in user_info["age_info"]:
                user_info["age_info"][line[1]] += 1
            else:
                user_info["age_info"][line[1]] = 1
            if line[2] in user_info["gender_info"]:
                user_info["gender_info"][line[2]] += 1
            else:
                user_info["gender_info"][line[2]] = 1

        else:
            user_info["age_gender_info"][age_gender] = dict()
            user_info["age_gender_info"][age_gender] = 1

    print("data with {} lines".format(_count))
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(json.dumps(user_info, ensure_ascii=False, indent=4))
    print("write down")
    return user_info


def plot_user_click_dist(all_text_len, save_path=None):
    """
    绘制文本长度分布
    :param all_text_len: [22,33,34,...]
    :param save_path: 图片保存路径
    :return:
    """
    plt.figure()
    plt.title("Length dist of user click times")
    plt.xlabel("Length")
    plt.ylabel("Count")
    _, _, all_data = plt.hist(all_text_len, bins=100, normed=1, alpha=.2, color="b")
    plt.show()
    if save_path:
        plt.savefig(save_path)


def analysis_click(file, outfile):
    if not os.path.exists(outfile):
        click_info = write_click_analysis_details_to_file(file, outfile)
    else:
        click_info = read_data_from_json_file(outfile)
    # 用户点击信息统计绘图
    user_total_click_times = list()
    user_total_click_days = list()
    for _ in click_info.keys():
        user_total_click_times.append(int(click_info["total_click_times_info"]))
        user_total_click_days.append(int(click_info["total_click_days_info"]["_count"]))
    plot_user_click_dist(user_total_click_times)
    plot_user_click_dist(user_total_click_days)

def write_click_analysis_details_to_file(file, outfile):
    print("start writing click analysis details to file: {}".format(outfile))
    click_info = dict()
    _count = 0

    for line in read_data_from_csv_file(file):
        _count += 1
        if _count < 6:
            print(line)
        # else:
        #     break
        # 用户点击信息
        if line[1] in click_info:
            click_info[line[1]]["total_click_times_info"] += int(line[3])
            if line[0] not in click_info[line[1]]["total_click_days_info"]:
                click_info[line[1]]["total_click_days_info"][line[0]] = 1
                click_info[line[1]]["total_click_days_info"]["_count"] += 1
            else:
                click_info[line[1]]["total_click_days_info"][line[0]] += 1
        else:
            click_info[line[1]] = dict()
            click_info[line[1]]["total_click_times_info"] = int(line[3])
            click_info[line[1]]["total_click_days_info"] = dict()
            click_info[line[1]]["total_click_days_info"][line[0]] = 1
            click_info[line[1]]["total_click_days_info"]["_count"] = 1


    print("data with {} lines".format(_count))
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(json.dumps(click_info, ensure_ascii=False, indent=4))
    print("write down")
    return click_info


ad_data_file = "/data/work/dl_project/data/corpus/tencent_ad_2020/train_preliminary/ad.csv"
ad_data_analysis_file = "/data/work/dl_project/data/corpus/tencent_ad_2020/train_preliminary/ad_analysis.json"

user_data_file = "/data/work/dl_project/data/corpus/tencent_ad_2020/train_preliminary/user.csv"
user_data_analysis_file = "/data/work/dl_project/data/corpus/tencent_ad_2020/train_preliminary/user_analysis.json"
click_log_data_file = "/data/work/dl_project/data/corpus/tencent_ad_2020/train_preliminary/click_log.csv"
click_log_data_analysis_file = "/data/work/dl_project/data/corpus/tencent_ad_2020/train_preliminary/click_log_analysis.json"

# analysis_ad(ad_data_file, ad_data_analysis_file)
# analysis_user(user_data_file, user_data_analysis_file)
analysis_click(click_log_data_file, click_log_data_analysis_file)

# user_data = read_data_from_csv(user_data_file)
#
# click_log_data = read_data_from_csv(click_log_data_file)