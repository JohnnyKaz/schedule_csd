"""
A helper python script that allows easy, automatic data extraction
from the pdf with the csd timetable. In order for it to work, you need
to specify the path to the input pdf and the name of the output file to be generated.
The generated file adheres to the repository's style/specifications.
"""
# pip install tabula-py -> it is needed in order to work (I used version 2.6.0)
import tabula

# parameters that need tweaking accordingly
in_file  = './extract_scripts/WROLOGIO_PROGRAMMA.pdf'  # the path of the pdf file with the csd timetable
out_file = 'data.js'    # the name of the file to be generated

# other parameters you may need to tweak (not necessary)
#days_in  = ('ΔΕΥΤΕΡΑ', 'ΤΡΙΤΗ', 'ΤΕΤΑΡΤΗ', 'ΠΕΜΠΤΗ', 'ΠΑΡΑΣΚΕΥΗ')   # days as shown in the pdf columns
days_out = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday') # days as you want them in the generated file
DEBUG = False

# extract the version of the pdf file, by reading the 1st page with lattice=True
df = tabula.read_pdf(in_file, multiple_tables=True, pages=1, lattice=True)[0]

#version  = df.columns.tolist()[1]
version  = df.columns.tolist()[0].split('Έκδοση:')[1].strip()
#Read the pdf into DataFrame
df = tabula.read_pdf(in_file, multiple_tables=False, pages='all')[0]

# you can check the columns of the dataframe, for debugging purposes
column_names = df.columns.tolist()
days_in = column_names[3:]
if DEBUG:
    print(f"Column Names detected: {column_names}")

codes    = []   # list of class codes (e.g. 'HY-112')
titles   = []   # list of class names (e.g. 'Φυσική Ι')
teachers = []   # list of teachers (e.g. 'ΚΑΦΕΝΤΖΗΣ')
# list with the lecture times per day (e.g. [['10-12 ΑΜΦ ΣΟ'], [''], ['10-12 ΑΜΦ ΣΟ'], [''], ['10-12 ΑΜΦ ΣΟ (ΦΡΟΝΤ)']])
times    = [[] for i in days_in]

# iterate the rows of the extracted dataframe with i
for i, code in enumerate(df['Unnamed: 0']):
    # if the current row contains a valid code (e.g. HY-100), add the class info
    if isinstance(code, str):
        codes.append(code.replace('\r', ''))
        titles.append(df['Unnamed: 1'][i].replace('\r', ' '))
        teachers.append(df['Unnamed: 2'][i].replace('\r', ''))
        for j, d in enumerate(days_in):
            times[j].append('' if not isinstance(df[d][i], str) else df[d][i].replace('\r', ' ').replace('  ', ' '))
    # else, the class info needs > 1 rows in the pdf, so we need to add the info in the next row(s) to the previous class
    else:
        # if the previous class name is too long
        if isinstance(class_name := df['Unnamed: 1'][i], str):
            titles[-1] += ' ' + class_name.replace('\r', ' ')
        # if the previous class professor names are too long
        if isinstance(prof_name := df['Unnamed: 2'][i], str):
            teachers[-1] += prof_name.replace('\r', '')
        # if the lecture time for a day is too long
        for j, d in enumerate(days_in):
            if isinstance(time := df[d][i], str) and time != d:
                times[j][-1] += time.replace('\r', ' ').replace('(', ' (')

# now, save the extracted data in an output file, according to the repository's specifications
with open(out_file, 'w') as f:
    f.write("const csd_version = '" + version + "'\n")
    f.write("var programma = [\n")
    for i, c in enumerate(codes):
        f.write("\t{\n")
        f.write("\t\tclass: '" + c + "',\n")
        f.write("\t\tname: '" + titles[i] + "',\n")
        f.write("\t\tteacher: '" + teachers[i] + "',\n")
        for j, d in enumerate(days_out):
            f.write("\t\t" + d + ": '" + times[j][i] + "',\n")
        # time_score = the 24-hour format of the starting hour of the first lecture of the week
        class_times = [column[i] for column in times]
        first_class_time = next((x for x in class_times if x!=''), None)    # e.g. '10-12 ΑΜΦ ΣΟ'
        time_score = int(first_class_time.split('-')[0].split(':')[0])      # e.g. 10
        # classes in csd are only between 10:00 and 20:00
        if 1 <= time_score <= 8:
            time_score += 12
        f.write("\t\ttime_score: " + str(time_score) + "\n")
        f.write("\t},\n")
    f.write("]")

print(f"=== saved program data to output file: {out_file} ===")
