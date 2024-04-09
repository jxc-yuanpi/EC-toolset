import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import random
 
colors = [
    'black',
    'red',
    'blue',
    'green',
    'purple',
    'orange',
    'cyan',
    'magenta',
    'teal',
    'pink',
    'lime'
] #固定颜色列表
 
#使用类实现数据集转换
class PAR_Dataset:
    def __init__(self, csv_path, CV_seg = None, EIS_seg = None, CA_seg = None, CP_seg = None):
        #csv_path为文件路径，CV_seg和EIS_seg为CV或EIS对应的片段编号和名称（请使用列表套列表）
        #示例：
        #例如第45片段为50mV/s的CV，55片段为25mV/s的CV，则输入[[45,'50 mV/s'], [55, '25 mV/s]]，EIS同理
        #如需绘制I-t或E-t之类的电化学图标，也可以自行更改代码
        #CA - 恒电位计时电流法 (i-t)
        #CP - 恒电流计时电位法 (E-t)

        if CV_seg == None and EIS_seg == None and CA_seg == None and CP_seg == None:
            raise TypeError('未提供数据对应的片段编号')
           
        self.dbclass = 'PAR'
        self.file_path = csv_path
        self.data = pd.read_csv(self.file_path)
        self.segments = [] 
        #元数据中片段都是从0开始的数据，使用列表套字典储存所有数据，列表索引恰好为片段编号
        self.extract_segments()

        #接下来使用者可以根据自己数据的特征提取特定的片段作为绘图数据
        self.refined_segments = self.refine_segments(CV_seg, EIS_seg)


    def extract_segments(self):
        for segment, segment_data in self.data.groupby('Segment'):
            self.segments.append({
                'potential': segment_data['Potential (V)'].values,
                'current': segment_data['Current (A)'].values,
                'zre': segment_data['Zre (ohms)'].values,
                'zim': segment_data['Zim (ohms)'].values,
                'freq': segment_data['Frequency (Hz)'].values
            })
    
    def refine_segments(self, CV_seg, EIS_seg):
        refined_segments = []
        if CV_seg != None and type(CV_seg) == list:
            CV_segments = []
            for selected_segment in CV_seg:
                CV_segments.append({
                    'legend_name': selected_segment[1],
                    'potential': self.segments[selected_segment[0]]['potential'],
                    'current': self.segments[selected_segment[0]]['current']
                })
            refined_segments.append({
                'Property': 'CV',
                'Data': CV_segments
                })
        elif CV_seg != None and type(CV_seg) != list:
            raise TypeError('请按照提示提供列表输入')
        

        if EIS_seg != None and type(EIS_seg) == list:
            EIS_segments = []
            for selected_segment in EIS_seg:
                EIS_segments.append({
                    'legend_name': selected_segment[1],
                    'freq': self.segments[selected_segment[0]]['freq'],
                    'zre': self.segments[selected_segment[0]]['zre'],
                    'zim': self.segments[selected_segment[0]]['zim']
                })
            refined_segments.append({
                'Property': 'EIS',
                'Data': EIS_segments
                })
        elif EIS_seg != None and type(EIS_seg) != list:
            raise TypeError('请按照提示提供列表输入')
        
        return refined_segments


chi_exp = {'CV', 'EIS', 'CA', 'CP'}

class CHI_Dataset:
    def __init__(self, csv_path, exp_type = None):
        #csv需要手动移除无关信息，提供实验类型即可， 如'CV', 'EIS', 'CA', 'CP'

        if exp_type not in chi_exp or exp_type == None:
            raise TypeError('未提供数据对应的实验类型')
           
        self.dbclass = 'CHI'
        self.file_path = csv_path
        self.rawdata = pd.read_csv(self.file_path)
        self.columns = self.rawdata.columns.tolist()
        self.experiment = exp_type
        self.data = [] 
        #CHI仅含有一段实验的数据
        self.extract_data(exp_type)

    def extract_data(self, exp_type):
        if exp_type == 'CA':
            exp_data = [{
                'time': self.rawdata[self.columns[0]].values,
                'current': self.rawdata[self.columns[1]].values
            }]
            self.data.append({
                'Property': 'CA',
                'Data': exp_data
            })
        
        if exp_type == 'CV':
            exp_data = [{
                'potential': self.rawdata[self.columns[0]].values,
                'current': self.rawdata[self.columns[1]].values
            }]
            self.data.append({
                'Property': 'CV',
                'Data': exp_data
            })
        if exp_type == 'CP':
            exp_data = [{
                'time': self.rawdata[self.columns[0]].values,
                'potential': self.rawdata[self.columns[1]].values
            }]
            self.data.append({
                'Property': 'CP',
                'Data': exp_data
            })
        # EIS待添加

def plot_segments(dataset, filename = None):
    #文件保存于程序目录，可自行修改
    #可以自定义文件名
    if dataset.dbclass == 'PAR':
        refined_segments = dataset.refined_segments
    elif dataset.dbclass == 'CHI':
        refined_segments = dataset.data

    if filename == None:
        filename = os.path.splitext(os.path.basename(dataset.file_path))[0] #若不指定图片文件名则默认为csv文件名
    elif type(filename) != str:
        raise TypeError('请确保自定义的文件名为string类型')

    plt_idx = 0
    for segments in refined_segments:
        color_idx = 0
        plt_idx += 1
        plt.figure(num=plt_idx, figsize=(8,6))
        if segments['Property'] == 'CV':
            for segment in segments['Data']:
                plt.plot(
                    np.add(np.array(segment['potential']), 0.936), #电压换成RHE
                    np.array(segment['current']) * 1000, #电流转化为毫安
                    '-',  
                    color=colors[color_idx], #根据顺序取色
                    label=segment['legend_name'] if 'legend_name' in segment else None, #legend名称
                    lw=0.75 #线条宽度
                    )
                
                color_idx += 1
            plt.xlabel('E (V vs. RHE)')
            plt.ylabel('I (mA)')
            plt.title(filename + '_CV')
            if 'legend_name' in segment:
                plt.legend()
            plt.savefig(filename + '_CV.PNG', format='PNG', dpi=600)
            plt.close

        if segments['Property'] == 'CA':
            for segment in segments['Data']:
                # print(segment)
                # print(segment['current'])
                plt.plot(np.array(segment['time']), 
                         np.array(segment['current']),
                        '-',
                        color='red', 
                        label=segment['legend_name'] if 'legend_name' in segment else None,
                        lw=0.75
                        )
                color_idx += 1
            plt.xlabel("Time (s)")
            plt.ylabel("I (A)")
            plt.title(filename + '_CA')
            if 'legend_name' in segment:
                plt.legend()
            plt.savefig(filename + '_CA.PNG', format='PNG', dpi=600)
            plt.close

        if segments['Property'] == 'EIS':
            for segment in segments['Data']:
                plt.plot(np.array(segment['zre']) * 0.001, 
                         np.array(segment['zim']) * -0.001,
                        '-',
                        color=colors[color_idx], 
                        label=segment['legend_name'] if 'legend_name' in segment else None
                        )
                #欧姆换成千欧
                color_idx += 1
            plt.xlabel("""Z' [kohms]""")
            plt.ylabel("""Z'' [kohms]""")
            plt.title(filename + '_EIS')
            if 'legend_name' in segment:
                plt.legend()
            plt.savefig(filename + '_EIS.PNG', format='PNG', dpi=600)
            plt.close

def dataset_recombination(dataset_list):
    recombinated_dataset = []
    #将数据集作为列表输入
    property = None
    #只能支持单种实验的组合

    for dataset in dataset_list:
        if dataset.dbclass == 'PAR':
            print('实验仪器为PAR')

            for exp_count in range(len(dataset.refined_segments)):
                print('%d. 实验类型: %s' %(exp_count, dataset.refined_segments['Property']))

            exp_selection = int(input('选择需要进行组合的实验类型: '))
            if exp_selection >= len(dataset.refined_segments) or exp_selection <0:
                raise ValueError('请输入正确的序号')
            
            if property == None:
                property = dataset.refined_segments[exp_selection]['Property']
            elif property != dataset.refined_segments[exp_selection]['Property']:
                raise ValueError('请选择相同的实验类型')
            
            candidate_segments = dataset.refined_segments[exp_selection]['Data']
            recombinated_dataset.append(candidate_segments)

        elif dataset.dbclass == 'CHI':
            print('实验仪器为CHI')

            exp = dataset.experiment

            if property == None:
                property = exp
            elif property != exp:
                raise ValueError('请提供相同的实验类型')
            
            legend_name = str(input('请输入要在图例上显示的实验名称: '))

            candidate_segments = dataset.data[exp_selection]['Data']
            candidate_segments[0]['legend_name'] = legend_name
            #加入图例标识
            recombinated_dataset.append(candidate_segments)
    return {
        'Property': property,
        'Data': recombinated_dataset
    }
    #返回可直接用于绘图的数据集合
            



                
        

