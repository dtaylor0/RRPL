import sys

file_in=sys.argv[1]
file_out=sys.argv[2]
f1=open(file_in,'r')
f2=open(file_out,'w')

r=[line.split() for line in f1.readlines()]

time=0

for line in r:
    if len(line)<7:
        continue
    line[8]=str(float(line[8])*-1)
    #line[-1]=str(float(line[-1])/1000)
    temp=line[8]
    line[8]=line[9]
    line[9]=temp
    time+=0.5
    '''
    if len(line)<=12:
        line.append(str(time))
    line.insert(2,"0")
    line.insert(3,"0")
    '''
finalStr="alt barom GPS_La GPS_Lo Gx Gy Gz Ax Ay Az Mx My Mz t\n"+"\n".join([" ".join(line) for line in r])

f2.write(finalStr)
f1.close()
f2.close()
