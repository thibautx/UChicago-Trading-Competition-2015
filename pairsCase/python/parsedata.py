import csv


def parsedata(filename):
	f_original = open(filename, "r")
	f_new = open("example_new.csv", "w")
	prevtime = ""
	for line in f_original:
		lastprice = line.split(',')[3]
		curr_time = line.split(',')[1]
		f_new.write("IBM, 20100105,")
		if(curr_time is not prevtime):
			f_new.write(lastprice)

	f_original.close()
	f_new.close()

if __name__ == '__main__':
	parsedata("example.csv")