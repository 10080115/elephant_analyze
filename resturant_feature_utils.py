import pandas as pd  
import os
import folium
from coord_convert.transform import bd2gcj
import geohash2 as geohash2

def get_resturuant_feature_df(order_file_path, restaurant_file_path):
    # 读取订单信息 Excel 文件
    df = pd.read_csv(order_file_path)
    # 计算每个店铺的总订单数和取消订单数
    shop_orders = df.groupby('简化餐厅编号')['下单时间'].count().reset_index(name='total_orders')
    shop_cancelled_orders = df[df['订单取消时间'].notnull()].groupby('简化餐厅编号')['订单取消时间'].count().reset_index(name='cancelled_orders')

    # 合并总订单数和取消订单数
    shop_orders = shop_orders.merge(shop_cancelled_orders, on='简化餐厅编号', how='left')

    # 计算订单取消率
    shop_orders['cancel_rate'] = shop_orders['cancelled_orders'] / shop_orders['total_orders']

    # 保留取消率三位小数
    shop_orders['cancel_rate'] = shop_orders['cancel_rate'].round(3)

    # 读取餐厅信息 Excel 文件
    restaurant_df = pd.read_csv(restaurant_file_path)
    # 将订单取消率和总订单数添加到餐厅信息表中
    merged_df = pd.merge(restaurant_df, shop_orders, left_on='simple_id', right_on='简化餐厅编号', how='left')

    # 将空值替换为0
    merged_df['cancel_rate'].fillna(0, inplace=True)
    merged_df['total_orders'].fillna(0, inplace=True)

    # 添加Geohash编码和精度到表格中
    merged_df['geohash'] = merged_df.apply(lambda x: geohash2.encode(x['latitude'], x['longitude']), axis=1)
    merged_df['geohash_precision'] = merged_df['geohash'].apply(len)

    # 根据不同精度计算区域划分的数量
    for precision in range(6, 10):
        column_name = f'geohash_{precision}'
        count_column_name = f'count_{precision}'

        # 将坐标编码为Geohash
        merged_df[column_name] = merged_df.apply(lambda x: geohash2.encode(x['latitude'], x['longitude'], precision=precision), axis=1)

        # 根据Geohash分组并计算每个区域的数量
        counts = merged_df.groupby(column_name).size().reset_index(name=count_column_name)

        # 将数量合并到原始表格中
        merged_df = pd.merge(merged_df, counts, on=column_name, how='left')

    merged_df.drop(['geohash', 'geohash_precision'], axis=1, inplace=True)

    return merged_df    