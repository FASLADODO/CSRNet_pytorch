import sys
from net_files.model import CSRNet
from eval_as_a_whole import *
from TrainDatasetConstructor import TrainDatasetConstructor
from EvalDatasetConstructor import EvalDatasetConstructor
from net_files.metrics import *
from utils import *
import time
# %matplotlib inline
# config
config = {
'SHANGHAITECH': 'A',
'min_RATE':10000000,
'min_MAE':10240000,
'min_MSE':10240000,
'eval_num':182,
'train_num':300,
'learning_rate': 1e-5,
'train_batch_size': 1,
'epoch': 100000,
'eval_per_step': 1600,
'mode':'crop'}

img_dir = "/home/zzn/Documents/Datasets/part_" + config['SHANGHAITECH'] + "_final/train_data/images"
gt_dir = "/home/zzn/Documents/Datasets/part_" + config['SHANGHAITECH'] + "_final/train_data/gt_map"
img_dir_t = "/home/zzn/Documents/Datasets/part_" + config['SHANGHAITECH'] + "_final/test_data/images"
gt_dir_t = "/home/zzn/Documents/Datasets/part_" + config['SHANGHAITECH'] + "_final/test_data/gt_map"
model_save_path = "/home/zzn/Downloads/CSRNet_pytorch-master/checkpoints/model_a_crop.pkl"

# data_load
train_dataset = TrainDatasetConstructor(img_dir, gt_dir, config['train_num'], mode=config['mode'])
eval_dataset = EvalDatasetConstructor(img_dir_t, gt_dir_t, config['eval_num'], mode=config['mode'])
train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=config['train_batch_size'])
eval_loader = torch.utils.data.DataLoader(dataset=eval_dataset, batch_size=1)

# obtain the gpu device
assert torch.cuda.is_available()
cuda_device = torch.device("cuda")

# model construct
net = CSRNet().to(cuda_device)
# net = torch.load("/home/zzn/Downloads/CSRNet_pytorch-master/checkpoints/model_a_crop_14:55_0328.pkl")
# set optimizer and estimator
criterion = Loss().to(cuda_device)
optimizer = torch.optim.Adam(net.parameters(), config['learning_rate'])
ae_batch = AEBatch().to(cuda_device)
se_batch = SEBatch().to(cuda_device)
modules = {'model':net, 'loss':criterion, 'ae':ae_batch, 'se':se_batch}

step = 0
for epoch_index in range(config['epoch']):
    dataset = train_dataset.shuffle()
    for train_img_index, train_img, train_gt, data_ptc in train_loader:
        if step % config['eval_per_step'] == 0:
            validate_MAE, validate_loss, validate_RMSE = eval_model(eval_loader, modules)
            sys.stdout.write(
                'In step {}, epoch {}, with loss {}, MAE = {}, MSE = {}\n'.format(step, epoch_index + 1, validate_loss,
                                                                                  validate_MAE, validate_RMSE))
            sys.stdout.flush()

            # save model
            if config['min_MAE'] > validate_MAE:
                config['min_MAE'] = validate_MAE
                torch.save(net, model_save_path)
            torch.save(net, "/home/zzn/Downloads/CSRNet_pytorch-master/checkpoints/model_in_time.pkl")
            # return train model

        net.train()
        optimizer.zero_grad()
        # B
        x = train_img
        y = train_gt
        prediction = net(x)
        loss = criterion(prediction, y)
        loss.backward()
        optimizer.step()
        step += 1
        if step == 400 * 100 or step == 400 * 1000 or step == 400 * 500:
            config['eval_per_step'] = eval_steps_adaptive(step)
        sys.stdout.write('In step {}, the loss = {}\r'.format(step, loss))
        sys.stdout.flush()