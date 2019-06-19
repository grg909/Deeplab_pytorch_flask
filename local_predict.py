# -*- coding: UTF-8 -*-

# @Date    : 2019/6/18
# @Author  : WANG JINGE
# @Email   : wang.j.au@m.titech.ac.jp
# @Language: python 3.6
"""
    For local image prediction
"""

import numpy as np
import pandas as pd
from deeplab import DeeplabPytorch


label_count = 182
confusion = np.zeros((label_count, label_count))

imageseg = "_segcoco"

labels = open('labels.txt', 'r')
X = pd.read_csv(labels, sep="\t", header=None)
X = X[1:]
X.columns = ['number', 'label']
X['number'] = X['number'].astype('int')
X['label'] = X['label'].astype('str')

X_labels = X['label']

id = np.array(['ImageID', 'PointID'])
header = np.concatenate((id, X_labels), axis=0)

city = "shenyang"

outputFile = 'sv_pt_' + city + imageseg + '.csv'
output = pd.DataFrame(columns=header)

dp = DeeplabPytorch(
    config_path='configs/cocostuff164k.yaml',
    model_path='data/models/coco/deeplabv2_resnet101_msc-cocostuff164k-100000.pth')


for filename, labelmap in dp.iter_local_pro('data/shenyang'):

    image_id = filename.split('_')[0]
    point_id = filename.split('_')[1]

    try:
        data = np.squeeze(labelmap)
        data = np.transpose(data)
        data = data[:513, :513]
        cat_ids = range(0, 182)
        valid = np.reshape(np.in1d(data, cat_ids), data.shape)
        valid_pred = data[valid].astype(int)

        # get the size of the image
        height = data.shape[0]
        width = data.shape[1]
        size = height * width
        # Accumulate confusion
        n = confusion.shape[0] + 1  # Arbitrary number > labelCount

        # Groupby categories
        image_df = pd.DataFrame(valid_pred, columns=['class'])

        df = pd.DataFrame(
            {'count': image_df.groupby(['class']).size()}).reset_index()
        df['labelnum'] = df['class'] + 1

        df_label = pd.merge(
            df,
            X,
            how='right',
            left_on=['labelnum'],
            right_on=['number'])
        df_label['ratio'] = df_label['count'] / size

        df_ratio = df_label.transpose()
        df_ratio.columns = df_ratio.loc['label']

        df_final = df_ratio.loc['ratio']
        df_final = pd.DataFrame(df_final)

        df_final = df_final.transpose()
        df_final['ImageID'] = image_id
        df_final['PointID'] = point_id
        df_final = df_final.fillna(0)

        # Resets the index, makes factor a column
        df_final.reset_index(inplace=True)
        df_final.drop("index", axis=1, inplace=True)

        output = pd.concat([output, df_final], sort=False)
    except BaseException:
        pass


output.to_csv(outputFile, sep=',', index=False)
print('All down!!!')