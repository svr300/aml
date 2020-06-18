#takes before/after legalization dot files as input
def parse_dot(dotfile,dotfilename):
	import re
	with open(dotfile) as f:
		s=f.read()
	count=1
	rows=[]

	#splitting each paragraph in the dot file
	for i in s.split("\n\n"):			
		if count==1:
			i=i[27:len(i)]
		count+=1

		#For every paragraph that has Result/Output min and max values 
		lsr=re.findall(r'Result : .+\]',i)
		lso=re.findall(r'output : .+\]',i)
		if lsr:
			res=re.findall(r'Result : .+\]',i)[0]
		elif lso:
			res=re.findall(r'output : .+\]',i)[0]
				
		#Output lines containing minmax has 4 characters Min:\Max: ending with ].Trimming these characters
		if lsr or lso:
			minstring=re.findall(r'Min:.+\,',res)[0]
			min=float(minstring[4:len(minstring)-1])
			maxstring=re.findall(r'Max:.+\]',res)[0]
			max=float(maxstring[4:len(maxstring)-1])
			name=re.findall(r'[^\[]*',i)
			node=name[0]
			rows.append([node,min,max])
	
	#Since after post legalization is in reverse order
	if re.findall(r'after_post_legalization',dotfilename):
		rows.reverse()

	return(rows)

#takes rows and dotfilename as input and outputs a csv	
def rows_to_csv(rows,dotfilename):
	with open(dotfilename+'_dot_summary.csv', mode='w',newline='') as csvfile:
		fields = ['Node', 'min', 'max']
		csvwriter = csv.writer(csvfile)
		csvwriter.writerow(fields)
		csvwriter.writerows(rows)

#filtering bias nodes and zero nodes from before legalization dot
def filtering_before_legalization_dot(rows,dict):
	filtered_rows=[]
	exception_node=dict['varp'][1][10:]
	for row in rows:
		node=row[0]
		if dict[node][0]!='Bias;' and node[0:4]!='zero' and node!=exception_node:
			filtered_rows.append(row)

	return filtered_rows

#Filtering cwq input nodes and boundary nodes 
def filtering_post_legalization_dot(rows):
	filtered_rows=[]
	for row in rows:
		node=row[0]
		if node[len(node)-3:len(node)]!='cwq' and node[0:8]!='boundary':
			filtered_rows.append(row)

	return filtered_rows

#plots a lineplot from the csv containging the minmax
def plot_min_max(dotfilename):
	df=pd.read_csv(dotfilename+'_dot_summary.csv')
	print(df)
	df.plot(x='Node',y=['min','max'],kind='line',grid='true')
	plt.xticks(np.arange(0,len(df)),df['Node'].values,rotation='vertical')
	plt.savefig(dotfilename+'_dot_minmaxplot.png')

#Takes rows as input and sorts them in the topological order given by top_dict
def topo_order(rows,topo_dict):
	topo_rows=[]
	new_dict={}
	for i in rows:
		if i[0] in topo_dict:
			new_dict[tuple(i)]=topo_dict[i[0]]
	topo_rows=[list(k) for k,v in sorted(new_dict.items(), key=lambda x: x[1])]

	return topo_rows

#This function outputs every node in the dot file with as key to top_dict and the level in the graph being the value
def create_topo_dict(mydict):
	x=[]
	for k,v in mydict.items():
		x.append([k,v[1][10:]])

	
	x=np.array(x)
	y=list(set(list(x[:,0])+list(x[:,1])))
	count=0
	for i in x:
		if i[0]=='Placeholder_0':
			temp=copy.copy(x[count])
			x[count]=x[0]
			x[0]=temp
		count+=1

	topo_dict={'Placeholder_0':0}
	i=0
	j=len(x)-1
	while i<len(x)-3:
		if x[i][0] in topo_dict:
			topo_dict[x[i][1]]=topo_dict[x[i][0]]+1
		if x[i][1] in topo_dict:
			topo_dict[x[i][0]]=topo_dict[x[i][1]]-1
		if x[i][0] not in topo_dict and x[i][1] not in topo_dict:
			temp=copy.copy(x[i])
			x[i]=x[j]
			x[j]=temp
			i=i-1
			j=j-1
		i+=1
		if(i==j):
				j=len(x)-1

	return topo_dict

#takes yaml summary as input and gives a dictionary yaml node along with their minmax as output
def parse_yamlsummary(yamlsummary):
	with open(yamlsummary, mode='r') as infile:
		reader = csv.reader(infile)
		yamldict = {rows[0][1:len(rows[0])-3]:[rows[3],rows[4]] for rows in reader}
	return yamldict

def parse_net_dot(dotfile, yamldict):
	with open(dotfile) as f:
		s=f.read()
	count=1
	rows=[]
	net_rows=[]

	for i in s.split("\n\n"):
		if count==1:
			i=i[27:len(i)]
		count+=1
		name=re.findall(r'[^\[]*',i)
		node=name[0]
		if node:
			rows.append(node)
	rows=rows[0:len(rows)-1]
	for node in rows:
			if node in yamldict:
				net_rows.append([node,yamldict[node][0],yamldict[node][1]])

	return net_rows



if __name__ == "__main__":
	import sys
	import matplotlib.pyplot as plt
	import pandas as pd
	import numpy as np
	import re
	import copy
	import csv
	fig_size = plt.rcParams["figure.figsize"]
	fig_size[0] = 150
	fig_size[1] = 60
	plt.rcParams["figure.figsize"] =fig_size

	dotfilename=sys.argv[1][0:len(sys.argv[1])-4]
	parse_dot(sys.argv[1],dotfilename)

	yamlsummary=sys.argv[2]
	yamldict=parse_yamlsummary(yamlsummary)

	#my_dict is a dictionary containing each input node as a key and the output with output type as the value 
	with open(sys.argv[1]) as f:
			s=f.read()
	enddata=s.split("\n\n")[-1]
	enddata=enddata[0:len(enddata)-2]
	mydict={}
	mydict = {re.findall(r'[^:]*',i)[0]:[re.findall(r'[^:]*',i)[4],re.findall(r'[^:]*',i)[2]] for i in enddata.split("\n")}
	topo_dict=create_topo_dict(mydict)
	
	#For before legalization dot
	if re.findall(r'before_legalization',dotfilename):
		
		rows=parse_dot(sys.argv[1],dotfilename)
		rows_to_csv(rows,dotfilename)
		plot_min_max(dotfilename)

		filtered_rows=filtering_before_legalization_dot(rows,mydict)
		rows_to_csv(filtered_rows,dotfilename+'_filtered')
		plot_min_max(dotfilename+'_filtered')


		topo_rows=topo_order(rows,topo_dict)
		rows_to_csv(topo_rows,dotfilename+'_topo_ordered')
		plot_min_max(dotfilename+'_topo_ordered')

		topo_filtered_rows=filtering_before_legalization_dot(topo_rows,mydict)
		rows_to_csv(topo_filtered_rows,dotfilename+'_topo_ordered'+'_filtered')
		plot_min_max(dotfilename+'_topo_ordered'+'_filtered')

	#For post legalization dot
	if re.findall(r'after_post_legalization',dotfilename):
		print()

		rows=parse_dot(sys.argv[1],dotfilename)
		rows_to_csv(rows,dotfilename)
		plot_min_max(dotfilename)
		
		filtered_rows=filtering_post_legalization_dot(rows)
		rows_to_csv(filtered_rows,dotfilename+'_filtered')
		plot_min_max(dotfilename+'_filtered')
		 
		topo_rows=topo_order(rows,topo_dict)
		rows_to_csv(rows,dotfilename+'_topo_ordered')
		plot_min_max(dotfilename+'_topo_ordered')

		topo_filtered_rows=filtering_post_legalization_dot(topo_rows)
		rows_to_csv(topo_filtered_rows,dotfilename+'_topo_ordered'+'_filtered')
		plot_min_max(dotfilename+'_topo_ordered'+'_filtered')
	
	#For net dot
	if dotfilename=='net':
		net_rows=parse_net_dot(sys.argv[1], yamldict)
		rows_to_csv(net_rows,dotfilename)
		plot_min_max(dotfilename)

		topo_rows=topo_order(net_rows,topo_dict)
		rows_to_csv(topo_rows,dotfilename+'_topo_ordered')
		plot_min_max(dotfilename+'_topo_ordered')

		


	
