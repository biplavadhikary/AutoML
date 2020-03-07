import pandas as pd
import os, sys
from autoviz.AutoViz_Class import AutoViz_Class

def buildSvg(folderName, targetY):
    Av = AutoViz_Class()
    #print(f'foldername: {folderName},  target={targetY}')
    df = pd.read_csv(f'datasets/{folderName}.csv')
    os.mkdir(f'datasets/{folderName}') 

    #print to logs instead of stdout
    stdoutSave = sys.stdout
    sys.stdout = open(f'datasets/logs/{folderName}.txt', 'w')

    sep = ','
    target = targetY

    dft = Av.AutoViz(
        filename='',
        sep=sep,
        depVar=target,
        dfte=df,
        header=0,
        verbose=2,
        lowess=False,
        chart_format="svg",
        max_rows_analyzed=150000,
        max_cols_analyzed=30,
    )

    sys.stdout.close()
    #restore stdout
    sys.stdout = stdoutSave

    PltType = [Av.scatter_plot, Av.pair_scatter, Av.dist_plot, Av.pivot_plot, Av.violin_plot, Av.heat_map, Av.bar_plot, Av.date_plot]

    for plottypes in PltType:
        i=0
        name = plottypes['name']
        plottypes['loc']=[]
        for plotlist in plottypes['plots']:
            j=0
            for plot in plotlist:
                f = open(f'./datasets/{folderName}/{name}-{i+1}-{j+1}.svg', 'w', encoding="utf-8")
                f.write(plot)
                f.close()
                plottypes['loc'].append(f'{name}-{i+1}-{j+1}.svg')
                j+=1
            print('')
            i+=1
    return PltType

def displayPlotData(Av):
    PltType = [Av.scatter_plot, Av.pair_scatter, Av.dist_plot, Av.pivot_plot, Av.violin_plot, Av.heat_map, Av.bar_plot, Av.date_plot]
    for plottypes in PltType:
        for key, value in plottypes.items():
            if key != 'plots' :
                print(f'{key}: {value}')
        print('\n')