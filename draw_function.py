from scipy.spatial import ConvexHull
import numpy as np
import pandas as pd
import folium
import json

def calculate_site_outlines(allres_df):
    # 创建一个空的DataFrame来存储所有站点的外轮廓坐标结果
    all_outlines_df = pd.DataFrame(columns=['站点', 'Outline'])

    # 遍历不同站点
    for site_id, site_data in allres_df.groupby('站点'):
        # 提取该站点的订单坐标
        orders_coords = site_data[['餐厅经度', '餐厅纬度']].values

        # 如果订单坐标数量少于三个点，则跳过该站点
        if len(orders_coords) >= 3:
            # 计算 Convex Hull
            hull = ConvexHull(orders_coords)

            # 提取外轮廓坐标
            outline_coords = orders_coords[hull.vertices]

            # 将站点ID和外轮廓坐标数据添加到 DataFrame 中
            all_outlines_df = all_outlines_df.append({'站点': site_id, 'Outline': outline_coords.tolist()},
                                                     ignore_index=True)

    return all_outlines_df


def plot_site_map(allres_df, all_outlines_df):
    # 创建一个字典来存储不同站点的坐标
    site_coordinates = {}

    # 遍历DataFrame中的每一行
    for index, row in allres_df.iterrows():
        site = row['站点']
        latitude = row['餐厅纬度']
        longitude = row['餐厅经度']

        # 将坐标添加到站点的列表中
        if site in site_coordinates:
            site_coordinates[site].append((latitude, longitude))
        else:
            site_coordinates[site] = [(latitude, longitude)]

    # 定义站点轮廓和坐标点的颜色列表
    outline_colors = ['blue', 'green', 'pink']
    marker_colors = ['green', 'blue', 'pink']

    # 创建Folium地图对象
    # 设置地图的初始位置为中国大陆（可根据需要调整）
    map = folium.Map(location=[11.5617623, 104.9145459], zoom_start=4)

    # 遍历不同站点
    for i, (site, coordinates_list) in enumerate(site_coordinates.items()):
        # 在地图上绘制坐标点
        for lat, lon in coordinates_list:
            folium.CircleMarker(
                location=[lat, lon],
                radius=3,
                color=marker_colors[i % len(marker_colors)],  # 使用站点标记颜色列表
                fill=True,
                fill_color=marker_colors[i % len(marker_colors)],
                fill_opacity=1,
                popup=f'站点: {site}\nLatitude: {lat}\nLongitude: {lon}'
            ).add_to(map)

    # 遍历站点外轮廓数据
    for idx, outline_row in all_outlines_df.iterrows():
        outline_coords_str = outline_row['Outline']
        outline_coords = json.loads(outline_coords_str)
        outline_coords = [(coord[1], coord[0]) for coord in outline_coords]

        # 将外轮廓添加到地图上
        folium.Polygon(locations=outline_coords, color=outline_colors[idx % len(outline_colors)],  # 使用站点轮廓颜色列表
                       fill_opacity=0.3, fill_color=outline_colors[idx % len(outline_colors)]).add_to(map)

    # 返回地图对象
    return map

def plot_res_map(allres_df):

    res_coordinates = {}

    # 遍历DataFrame中的每一行
    for index, row in allres_df.iterrows():
        site = row['站点']
        latitude = row['餐厅纬度']
        longitude = row['餐厅经度']


        if site in res_coordinates:
            res_coordinates[site].append((latitude, longitude))
        else:
            res_coordinates[site] = [(latitude, longitude)]


    marker_colors = ['green', 'blue', 'pink']

    # 创建Folium地图对象
    # 设置地图的初始位置为中国大陆（可根据需要调整）
    map = folium.Map(location=[11.5617623, 104.9145459], zoom_start=4)

    # 遍历不同站点
    for i, (site, coordinates_list) in enumerate(res_coordinates.items()):
        # 在地图上绘制坐标点
        for lat, lon in coordinates_list:
            folium.CircleMarker(
                location=[lat, lon],
                radius=3,
                color=marker_colors[i % len(marker_colors)],  # 使用站点标记颜色列表
                fill=True,
                fill_color=marker_colors[i % len(marker_colors)],
                fill_opacity=1,
                popup=f'站点: {site}\nLatitude: {lat}\nLongitude: {lon}'
            ).add_to(map)


    # 返回地图对象
    return map

def create_map(allres_df, outline_df, site_id, output_filename, color_order):
    # 筛选出特定站点的坐标
    site_coords = allres_df[allres_df['站点'] == site_id]

    # 创建地图
    m = folium.Map(location=[11.6005025, 104.9026626])

    # 添加轮廓到地图上
    site_outline = outline_df[outline_df['站点'] == site_id]
    for index, row in site_outline.iterrows():
        outline_coords_str = row['Outline']
        outline_coords = json.loads(outline_coords_str)
        outline_coords = [(coord[1], coord[0]) for coord in outline_coords]
        color = color_order.pop(0)  # 从颜色列表中取出下一个颜色
        folium.Polygon(locations=outline_coords, color=color, fill_opacity=0.3).add_to(m)

    # 添加站点坐标到地图上
    for index, row in site_coords.iterrows():
        folium.CircleMarker(
            location=[row['餐厅纬度'], row['餐厅经度']],
            radius=2,  # 根据权重调整标记大小
            color=None,
            fill=True,
            fill_opacity=0.9,
            fill_color= color
        ).add_to(m)

    # 保存地图为 HTML 文件
    m.save(output_filename)