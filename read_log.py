import numpy as np
import argparse

def ReadLog (logfile):

    file = open(logfile, 'r')
    line = file.readline()
    while line :
        if 'running' in line:
            break
        line = file.readline()   
    properties = [l for l in file.readline().replace('#','').split('\"') if l.strip()]
    values = [[]]
    values[0] = file.readline().split()
    line = file.readline()
    while line[0] == '#':
        tok = line.replace('#','').split()
        properties.append(tok[0]+' ('+tok[2]+')')
        values[0].append(tok[1])
        line = file.readline()
    
    properties = [p.replace(' ','-')for p in properties]
    
    while (len(line.split()) != 0):
        tmp_val = [[]]
        tmp_val[0] = line.split()
        line = file.readline()
        while line[0] == '#':
            tmp_val[0].append(line.replace('#','').split()[1])
            line = file.readline()
        values.extend(tmp_val)
    
    file.close()
    return (properties,values)
  
def WriteOutput (logfile,properties,values):
    tok = logfile.split('.')
    tok.insert((len(tok)-1),'plot')
    outfile = '.'.join(tok)
    prop = ' '.join(properties)
    np.savetxt(outfile, values, header = prop, comments='', delimiter=' ',fmt='%s')

def GetAverage(properties,values,cut):
    values=np.array(values).transpose()
    frames = int(round((1.0-cut)*len(values[0]),0))
    print('# Averaged over last {0:d} frames (steps {1} ... {2})'.format(frames,values[properties.index('Step'),(len(values[0])-frames)],values[properties.index('Step'),len(values[0])-1]))

    for prop in properties:
        if 'Step' not in prop:
            i = properties.index(prop)
            val = values[i]
            mean = np.mean([float(x) for x in val[(len(val)-frames):]])
            std = np.std([float(x) for x in val[(len(val)-frames):]]) 
            print('{0:30s} {1:15.5f} +/- {2:.5f}'.format(prop.replace('-',' '),mean,std))

def main():
    parser = argparse.ArgumentParser( description = 'Reads log file, print file for plotting and calculates average values')
    parser.add_argument('-log', '--logfile', dest='logfile', default='openmm.log', type=str, help='openmm output file [default: %(default)s]')
    parser.add_argument('-c', '--cut',  dest='cut', type=float, default=0.0, help = 'calculate average staring from [default: %(default)s] 0 %% till 100 %% frames, cut < 1.0')

    args = parser.parse_args()

    (properties,values) = ReadLog (args.logfile)
    WriteOutput (args.logfile,properties,values)
    GetAverage(properties,values,args.cut)

if __name__ == '__main__':
    main()