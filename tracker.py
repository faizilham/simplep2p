from blaze.trackerlib import Tracker

tracker = Tracker('localhost', 9999, 'trackerdata/db')
tracker.start()

input = ''
try:
	while (input!='exit'):
		input = raw_input()
		if input == 'peers':
			tracker.print_peer()
except:
	pass
finally:
	tracker.stop()
	tracker.join()

