

import os, csv

f=open("cfg/enroll_list.csv",'w+', newline='')
w=csv.writer(f)
w.writerow(['filename','speaker'])

for path, dirs, files in os.walk("data/wav/enroll/timit"):
    for path1, dirs1, files1 in os.walk(path):
        Dirname = os.path.basename(path1)
        print(Dirname)
        for filename in files1:

            fullFilename = os.path.join(path1, filename)
            print(fullFilename)
            w.writerow([fullFilename,Dirname])

