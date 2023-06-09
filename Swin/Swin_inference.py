
import mmcv
from mmcv import Config
from mmdet.datasets import (build_dataloader, build_dataset,
                            replace_ImageToTensor)
from mmdet.models import build_detector
from mmdet.apis import single_gpu_test
from mmcv.runner import load_checkpoint
import os
from mmcv.parallel import MMDataParallel
import pandas as pd
from pandas import DataFrame
from pycocotools.coco import COCO
import numpy as np
import torch


classes = ("General trash", "Paper", "Paper pack", "Metal", "Glass",
           "Plastic", "Styrofoam", "Plastic bag", "Battery", "Clothing")

# config file 들고오기
cfg = Config.fromfile('./configs/swin/cascade_mask_rcnn_swin_base.py')

root = '../../dataset/'

epoch = 'best_bbox_mAP'

# dataset config 수정
cfg.data.test.classes = classes
cfg.data.test.img_prefix = root
cfg.data.test.ann_file = root + 'test.json'  # test json 정보
# cfg.data.test.pipeline[1]['img_scale']= (512,512)
cfg.data.test.test_mode = True

cfg.data.samples_per_gpu = 4

cfg.seed = 2021
cfg.gpu_ids = [1]
cfg.work_dir = './work_dirs/Swin_trash'

cfg.model.roi_head.bbox_head[0].num_classes = 10
cfg.model.roi_head.bbox_head[1].num_classes = 10
cfg.model.roi_head.bbox_head[2].num_classes = 10

cfg.model.train_cfg = None
# build dataset & dataloader
dataset = build_dataset(cfg.data.test)
data_loader = build_dataloader(
    dataset,
    samples_per_gpu=1,
    workers_per_gpu=cfg.data.workers_per_gpu,
    dist=False,
    shuffle=False)

# checkpoint path
checkpoint_path = os.path.join(cfg.work_dir, f'{epoch}.pth')

model = build_detector(cfg.model, test_cfg=cfg.get(
    'test_cfg'))  # build detector
checkpoint = load_checkpoint(
    model, checkpoint_path, map_location='cpu')  # ckpt load

model.CLASSES = dataset.CLASSES
model = MMDataParallel(model.cuda(), device_ids=[0])

# submission 양식에 맞게 output 후처리
prediction_strings = []
file_names = []
coco = COCO(cfg.data.test.ann_file)
img_ids = coco.getImgIds()
len(img_ids)

class_num = 10
# out -> 4772, 10, prediction num, 5 (x, x1, y, y1, score)
for i, out in enumerate(output):
    prediction_string = ''
    image_info = coco.loadImgs(coco.getImgIds(imgIds=i))[0]
    for j in range(class_num):
        for o in out[j]:
            prediction_string += str(j) + ' ' + str(o[4]) + ' ' + str(o[0]) + ' ' + str(o[1]) + ' ' + str(
                o[2]) + ' ' + str(o[3]) + ' '

    prediction_strings.append(prediction_string)
    file_names.append(image_info['file_name'])


submission = pd.DataFrame()
submission['PredictionString'] = prediction_strings
submission['image_id'] = file_names
submission.to_csv(os.path.join(
    cfg.work_dir, f'submission_{epoch}.csv'), index=None)
submission.head()
