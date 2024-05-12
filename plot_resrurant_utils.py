import pandas as pd 
import folium as folium
from coord_convert.transform import bd2gcj

def process_most_orders_per_restaurant(order_file_path):
    # 读取订单信息的Excel表格
    df = pd.read_csv(order_file_path)

    # 计算每个餐厅的订单数量，并添加到DataFrame中
    restaurant_order_counts = df.groupby('简化餐厅编号').size().reset_index(name='total_orders')

    # 将订单数量合并到原始数据表中
    df_with_total = df.merge(restaurant_order_counts, on='简化餐厅编号', how='left')

    # 按照简化餐厅编号分组，并保留每组订单数量最大的数据
    filtered_df = df_with_total.loc[df_with_total.groupby('简化餐厅编号')['total_orders'].idxmax()]

    # 提取编号和站点信息
    filtered_data = filtered_df[['简化餐厅编号', '站点']].drop_duplicates().values.tolist()

    # 创建一个空的DataFrame来存储筛选后的数据
    filtered_data_list = []

    # 遍历筛选数据列表，根据编号和站点筛选对应的数据，并追加到filtered_data_list中
    for data in filtered_data:
        filtered_row = df[(df['简化餐厅编号'] == data[0]) & (df['站点'] == data[1])]
        filtered_data_list.append(filtered_row)

    # 合并所有筛选后的数据
    filtered_data_combined = pd.concat(filtered_data_list)

    return filtered_data_combined


def process_station_data(filtered_data_combined, merged_df):
    # 获取所有站点的唯一编号
    station_ids = filtered_data_combined['站点'].unique()

    # 创建一个空的 DataFrame 用于存储所有站点的结果
    all_results = pd.DataFrame()

    for station_id in station_ids:
        # 根据站点编号筛选数据
        person_data = filtered_data_combined[filtered_data_combined['站点'] == station_id]

        # 计算每个简化餐厅编号的数量
        id_counts = person_data['简化餐厅编号'].value_counts()

        # 创建一个新的 DataFrame 存储结果，包括经纬度信息
        result_df = pd.DataFrame({'id': id_counts.index,
                                  'Count': id_counts.values})

        # 计算数量列的最小值和最大值
        min_count = result_df['Count'].min()
        max_count = result_df['Count'].max()

        # 根据简化餐厅编号从 merged_df 中获取经纬度信息
        result_df['站点'] = station_id
        result_df['餐厅纬度'] = result_df['id'].map(merged_df.set_index('simple_id')['latitude'])
        result_df['餐厅经度'] = result_df['id'].map(merged_df.set_index('simple_id')['longitude'])

        # 删除包含空值的行
        result_df.dropna(subset=['餐厅纬度', '餐厅经度'], inplace=True)

        # 对数量列进行归一化处理
        result_df['Normalized_Count'] = result_df['Count'].apply(
            lambda x: (x - min_count) / (max_count - min_count))

        # 将结果添加到总结果中
        all_results = pd.concat([all_results, result_df])

    return all_results


def draw_map(filtered_data_combined, merged_df):
    data = filtered_data_combined
    data1 = merged_df

    # 输入站点编号
    input_stations = list(set(data['站点'].tolist()))

    # 定义颜色列表
    colors = ['blue', 'pink', 'green']

    # 遍历站点
    for station_id in input_stations:
        # 筛选对应站点的数据
        selected_data = data[data['站点'] == int(station_id)]
        # 如果有数据，则绘制地图
        if not selected_data.empty:
            # 创建地图对象
            mo = folium.Map(location=[11.53221757, 104.9048867])

            # 创建要素组对象
            fg2 = folium.FeatureGroup(name='count', show=True)

            # 遍历选定的数据集，绘制圆点
            for i, row in selected_data.iterrows():
                location = [row['餐厅纬度'], row['餐厅经度']]
                rad = row['Normalized_Count'] * 20
                rad = max(min(rad, 10), 1)  # 限制半径在1到10之间
                restaurant_id = row['id']
                # 从data1中获取订单数量和取消率
                id_all_array = data1[data1['simple_id'] == restaurant_id]['id']
                total_orders_array = data1[data1['simple_id'] == restaurant_id]['total_orders']
                cancel_rate_array = data1[data1['simple_id'] == restaurant_id]['cancel_rate']
                
                geo6_array = data1[data1['simple_id'] == restaurant_id]['count_6']
                geo7_array = data1[data1['simple_id'] == restaurant_id]['count_7']
                geo8_array = data1[data1['simple_id'] == restaurant_id]['count_8']
                geo9_array = data1[data1['simple_id'] == restaurant_id]['count_9']
                # 确保只有一个值，或返回缺失的缺省值
                id_all = id_all_array.iloc[0] if not id_all_array.empty else 'N/A'
                total_orders = total_orders_array.iloc[0] if not total_orders_array.empty else 'N/A'
                cancel_rate = cancel_rate_array.iloc[0] if not cancel_rate_array.empty else 'N/A'
                geo6 = geo6_array.iloc[0] if not geo6_array.empty else 'N/A'
                geo7 = geo7_array.iloc[0] if not geo7_array.empty else 'N/A'
                geo8 = geo8_array.iloc[0] if not geo8_array.empty else 'N/A'
                geo9 = geo9_array.iloc[0] if not geo9_array.empty else 'N/A'
                # 格式化弹出窗口中的数据
                cancel_rate_percent = f"{cancel_rate * 100:.2f}%" if isinstance(cancel_rate, (int, float)) else 'N/A'
                # 创建圆点，并添加到地图上
                fg2.add_child(folium.CircleMarker(
                    location=bd2gcj(row['餐厅纬度'], row['餐厅经度']),
                    radius=rad,
                    color='blue',  # 每个站点的圆点颜色都设为蓝色
                    popup=folium.Popup(
                        f"餐厅编号: {id_all}.<br>订单数量：{total_orders}<br>订单取消率：{cancel_rate_percent}<br>geo6：{geo6}<br>geo7：{geo7}<br>geo8：{geo8}<br>geo9：{geo9}"),
                    fill=True,
                    fill_color='blue',  # 每个站点的圆点填充颜色都设为蓝色
                    fill_opacity=1
                ))

            # 将要素组添加到地图上
            mo.add_child(fg2)

            # 将要素组保持在最前面
            mo.keep_in_front(fg2)

            # 保存地图为HTML文件
            file_name = f'./data/resturan_station_{station_id}.html'
            mo.save(file_name)
            print(f'保存成功: {file_name}')
        else:
            print(f"站点编号 {station_id} 无效，已跳过")    
