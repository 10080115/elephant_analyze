import pandas as pd
import numpy as np


def rename_columns(columns, ignore_strings):
    return [col.replace(s, '').strip() for s in ignore_strings for col in columns]


def concatenate_behaviors(group):
    behaviors_time = group.apply(lambda row: f"{row['分配标记']}", axis=1)
    return ''.join(behaviors_time)


def get_dispatch_df(data, star_date='2024-03-01', end_date='2024-03-07'):
    print('你好')
    data = data[(data['下单时间'] >= star_date) & (data['下单时间'] <= end_date)]

    time_cols = [col for col in data.columns if '时间' in col]
    for col in time_cols:
        data[col] = pd.to_datetime(data[col], errors='coerce')
        data = data.dropna(subset=[col])
    data['下单时间'] = data['下单时间'].astype(str)
    pattern = r'(\w+):(\w+)'
    data[['小时', '分钟']] = data['下单时间'].str.extract(pattern)
    data['小时'] = pd.to_numeric(data['小时'], errors='coerce')
    data['分钟'] = pd.to_numeric(data['分钟'], errors='coerce')
    data['分钟桶'] = data['小时'] * 60 + data['分钟']
    data['日期'] = data['下单时间'].astype(str)
    data['日期'] = data['日期'].apply(lambda x: x.split(" ")[0])
    print('1、日期处理完毕')

    df = data[['订单编号', '派单时间', '分配类型']]
    grouped = df.groupby(['订单编号', '分配类型']).agg(
        最大派单时间=('派单时间', 'max'),
        最小派单时间=('派单时间', 'min'),
        派单数量=('派单时间', 'count')
    ).reset_index()

    # 对分组结果进行透视，以便将人工和机器派单分开到不同的列
    pivot_df = grouped.pivot_table(index='订单编号',
                                   columns='分配类型',
                                   values=['最大派单时间', '最小派单时间', '派单数量'],
                                   aggfunc='first').fillna(0)

    pivot_df.columns = ['_'.join(col) for col in pivot_df.columns]
    pivot_df.rename(columns={'最大派单时间_人工派单': '人工派单最大时间',
                             '最大派单时间_机器派单': '机器派单最大时间',
                             '最小派单时间_人工派单': '人工派单最小时间',
                             '最小派单时间_机器派单': '机器派单最小时间',
                             '派单数量_人工派单': '人工派单次数',
                             '派单数量_机器派单': '机器派单次数'}, inplace=True)
    pivot_df.reset_index(inplace=True)

    # # 计算每个订单的最大和最小派单时间（不区分人工或机器）
    order_times = df.groupby('订单编号')['派单时间'].agg(最大派单时间='max', 最小派单时间='min').reset_index()

    type_df = pd.merge(order_times, pivot_df, on='订单编号', how='left')
    type_df['最终类型'] = type_df.apply(
        lambda row: '人工' if row['最大派单时间_人工分配'] == row['最大派单时间'] else '机器', axis=1)
    print('2、类型处理完毕')

    unique_cols = ['订单编号', '下单时间', '开始调度时间', '骑手接单时间', '骑手到店时间', '骑手取餐时间',
                   '骑手到达时间', '导航距离', '小时', '分钟', '分钟桶', '日期']
    data_unique = data[unique_cols].drop_duplicates()
    data_merge = data_unique.merge(type_df)

    # 要忽略的字符串列表
    ignore_strings = ["时间"]

    # 重新命名列名
    new_column_names = rename_columns(data_merge.columns.tolist(), ignore_strings)
    # 应用新的列名
    data_merge.columns = new_column_names

    ignore_strings = ["骑手"]
    new_column_names = rename_columns(data_merge.columns.tolist(), ignore_strings)
    # 应用新的列名
    data_merge.columns = new_column_names

    data_merge['派单-接单'] = (data_merge['接单'] - data_merge['最大派单']).dt.seconds
    data_merge['接单-到店'] = (data_merge['到店'] - data_merge['接单']).dt.seconds
    data_merge['到店-取餐'] = (data_merge['取餐'] - data_merge['到店']).dt.seconds
    data_merge['取餐-到达'] = (data_merge['到达'] - data_merge['取餐']).dt.seconds
    data_merge['派单时长'] = (data_merge['最大派单'] - data_merge['最小派单']).dt.seconds
    data_merge['开小派单-开始调度'] = (data_merge['最小派单'] - data_merge['开始调度']).dt.seconds
    data_merge['最大派单-最小派单'] = (data_merge['最大派单'] - data_merge['最小派单']).dt.seconds
    print('3、时间间隔处理完毕')

    data['分配标记'] = np.where(data['分配类型'] == '人工分配', '2', '1')
    data_third = data[['订单编号', '派单时间', '分配标记']]
    sorted_df = data_third.sort_values(by=['订单编号', '派单时间'])
    dispatch_type_df = sorted_df.groupby('订单编号').apply(concatenate_behaviors).reset_index()
    dispatch_type_df.columns = ['订单编号', '分配标记']

    type_list = ['1', '2', '12', '22']
    dispatch_type_df['分配标记简化'] = np.where(dispatch_type_df['分配标记'].isin(type_list),
                                                dispatch_type_df['分配标记'], '其他')
    data_merge_2 = data_merge.merge(dispatch_type_df)
    print('4、分配标记隔处理完毕')
    print(type(data_merge_2))
    print(data_merge_2)
    data_merge_2.to_csv(f'./data/dispatchlog_{star_date}_{end_date}.csv')
    return data_merge_2