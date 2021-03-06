Model zoo of sleep staging networks implemented in pytorch

pytorch dataLoader of mass and sleep-edf dataset can be accessed [here](https://drive.google.com/drive/folders/1ayevfsoN8pYUUKx4nTMHn6nVs3oIY5qI)

model    |  input epoch  | network input shape                | total paramaeter
---------|---------------|------------------------------------|-------------------
dsn      |        1      | #ch * Fs(200) * 30                 |   46,371,589
seqsleepnet |{10, 20, 30}| #ch * Fs(100) * 30 * {10, 20, 30} --> (29 * 129) * {10, 20, 30} |  137,476(20 epoch)
utime    |       35      | #ch * Fs(100) * 30 * 35            |    1,220,317
segnet   |      128      | #ch * Fs(100) * 30 * 128           |    3,674,464

<b># Run the line below before using each model </b>

pip3 install -r requirements.txt

<b># original paper references

dsn: https://arxiv.org/pdf/1703.04046.pdf

seqsleepnet: https://arxiv.org/pdf/1809.10932.pdf

utime: https://arxiv.org/pdf/1910.11162.pdf
