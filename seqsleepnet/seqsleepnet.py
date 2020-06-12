'''
    Pytorch implementation of SeqSleepNet taking as input single channel signal
    x: [bs, seq_len, Fs*30]
    y: [bs, seq_len, num_classes]

    Original SeqSleepNet implmentation includes following steps:
    input x [bs, seq_len, 30*100]
    1: send x to time-frequency representation obtaining  x: [bs, seq_len, 29, 129]
    2: send x to filterbank obtaining                     x: [bs, seq_len, 29, 32]  # (29,129)*(129,32) = (29,32)
    3: reshape                                            x: [bs*seq_len, 29, 32]   # 29*32 = 928
    4: send x to biRNN obtaining                          x: [bs*seq_len, 29, 64*2]
    5: send x to an attention layer obtaining             x: [bs*seq_len, 64*2]
    6: reshape                                            x: [bs, seq_len, 64*2]
    7: send x to biRNN obtaining                          x: [bs, seq_len, 64*2]
    8: send x to seq_len of fc layers obtaining           x: [bs, seq_len, class_num]
    9: compute loss
'''

import torch
import torch.nn as nn
import torch.nn.functional as F

import numpy as np
from utils import *

class BiGRU(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers):
        super(BiGRU, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers  = num_layers
        self.gru         = nn.GRU(input_size, hidden_size, num_layers, batch_first=True, bidirectional=True)

    def forward(self, x):
        h0     = torch.randn(self.num_layers*2, x.size(0), self.hidden_size).cuda()
        #c0     = torch.randn(self.num_layers*2, x.size(0), self.hidden_size)
        out, _ = self.gru(x, h0)
        return out

class Parabit(nn.Module):
    def __init__(self, seq_len, dim, class_num):
        super(Parabit, self).__init__()
        self.bits = []
        self.seq_len = seq_len
        for i in range(seq_len):
            bit = nn.Linear(dim, class_num)
            bit_name = 'seq_at_%d' % i
            setattr(self, bit_name, bit)
            self.bits.append(getattr(self, bit_name))

    def forward(self, x):
        bit_fcs = []
        for i in range(self.seq_len):
            xx = x[:,i,:]
            fc = self.bits[i]
            yy = fc(xx)
            yy = yy.unsqueeze(1)
            bit_fcs.append(yy)
        torch_bits = torch.cat(bit_fcs, 1) # bs, seq_len, class_num
        return torch_bits

class SeqSleepNet(nn.Module):

    def __init__(self, seq_len=20, class_num=5):
        super(SeqSleepNet, self).__init__()
        self.seq_len   = seq_len
        self.class_num = class_num

        self.filterbankshape = torch.from_numpy(lin_tri_filter_shape(32, 256, 100, 0, 50)).to(torch.float) # [129, 32]
        filterweight         = torch.randn(129, 32, requires_grad=True)
        setattr(self, 'filter', filterweight)

        #self.epoch_rnn = BiGRU(seq_len=29*32, hidden_dim=64, dropout=0.75, num_layers=1)
        self.epoch_rnn  = BiGRU(32, 64, 1).cuda()
        #self.attention = Attention(64)
        #self.seq_rnn   = BiGRU(seq_len=64*2, hidden_dim=self.seq_len, dropout=0.75, num_layers=1)
        self.seq_rnn    = BiGRU(64*2, 64, 1).cuda()
        self.cls        = Parabit(self.seq_len, 64*2, self.class_num)

    def forward(self, x):
        # x: [bs, seq_len, 29, 129]
        # return: [bs, seq_len, class_num]

        # torch.mul -> element-wise dot;  torch.matmul -> matrix multiplication
        x            = torch.reshape(x, [-1, 129])                      # [bs, seq_len*29, 129]
        filterweight = torch.sigmoid(self.filter)                 # [129, 32]
        filter_      = torch.mul(filterweight, self.filterbankshape)    # [129, 32]
        filter_      = filter_.to('cuda')
        x = torch.matmul(x, filter_)                                    # [bs, seq_len*29, 32]
        x = torch.reshape(x, [-1, 29, 32])  # [bs*seq_len, 29, 32]
        x = self.epoch_rnn(x)               # [bs*seq_len, 29, 64*2]

        # above is epoch-wise learning
        # below is seq-wise learning

        x = torch.mean(x, dim=1) # [bs*seq, 64*2] to be replaced with attention
        x = torch.reshape(x, [-1, self.seq_len, 64*2]) # [bs, seq_len, 64*2]
        x = self.seq_rnn(x)                            # [bs, seq_len, 64*2]
        x = self.cls(x)

        return x

if __name__ == '__main__':
    batch_size = 2
    seq_len    = 20
    class_num  = 5
    net        = SeqSleepNet(seq_len=seq_len, class_num=class_num)
    net        = net.cuda()
    inputs     = torch.rand(batch_size, seq_len, int(100*30)) # [bs, seq_len, 30*100]
    inputs     = preprocessing(inputs) # [bs, seq_len, 29, 129]
    inputs     = inputs.type(torch.float)
    inputs     = inputs.cuda()
    outputs    = net(inputs) # [bs, seq_len]
    params     = list(net.parameters())
    print(outputs.size())
    print("total param num is: {}".format(
        sum(torch.numel(p) for p in params)
        )
    )
    for name, param in net.named_parameters():
        print(name, param.shape)
