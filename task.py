import re
import argparse

# Constants definition
# SHIFTS and HOURLY_PRICES were defined as constats so we don need to change the code in to make
# changes in the prices for hour in each shift or how the shifts are comprised. 
SHIFTS = {
		"night_shift":["00:01", "09:00"],
		"day_shift":["09:01", "18:00"],
		"evening_shift":["18:01", "00:00"]
		}

HOURLY_PRICES = {
				"MO":{"night_shift":25, "day_shift":15, "evening_shift":20},
				"TU":{"night_shift":25, "day_shift":15, "evening_shift":20},
				"WE":{"night_shift":25, "day_shift":15, "evening_shift":20},
				"TH":{"night_shift":25, "day_shift":15, "evening_shift":20},
				"FR":{"night_shift":25, "day_shift":15, "evening_shift":20},
				"SA":{"night_shift":30, "day_shift":20, "evening_shift":25},
				"SU":{"night_shift":30, "day_shift":20, "evening_shift":25}}


# FileReader, Payroll and Payroll_I classes should be moved to new independent files.
# Not doing that just to not complicate the repository with relative imports and things
# like that right now

class FileReader:
	""" Class in charge of the files managment. In case support for new file formats 
		needs to be added, this class can be inherited and modified to convert the
		values to the format expected by the Payroll class.
	"""

	def __init__( self, filename ):
		self.filename = filename
		self.cursor = None
		self.open()

	def open( self ):
		try:
			self.file = open( self.filename, "r")
			self.cursor = 0
		except Exception as e:
			print( f"""
				ERROR: Imposible to read the file requested:
				Reason: {repr(e)}
				""")
			raise Exception
		return

	def process( self, line ):
		""" Function to process the line readed from the file to convert it to
			the format expected by the Payroll class. Empty in this case because
			the provided files comes with each line in the desired format.
		"""
		return line

	def next( self ):
		""" Function to read and maintain the state of the file being read.
		"""
		try:
			if ( self.cursor == None ):
				self.cursor = 0 
			self.file.seek( self.cursor )
			line = self.file.readline()
			line = self.process( line )
			if not line:
				return None
			self.cursor = self.file.tell()
			return line
		except Exception as e:
			# print(f"{repr(e)}")
			return None
		return line



class Payroll:
	# Singleton Class to have just one Payroll instance at every moment
	# Helps maintaining coherence between different processes. If the properties
	# needs to be changed at any moment, all the processes will have the
	# change inmediatly in a transparent way (also helps with memory consumption)
	_instance = None

	def __init__(self):
		raise RuntimeError('Call instance() instead')

	@classmethod
	def instance(cls, shifts, hourly_prices):
		# Instance creation and storage for future requests
		if cls._instance:
			return cls._instance
		cls._instance = Payroll_I(shifts, hourly_prices)
		return cls._instance


class Payroll_I:
	# Class in charge of calculating the payment of a person based on the work
	# records and the prices provided for each day.

	def __init__( self, shifts, hourly_prices ):
		
		self.prices = HOURLY_PRICES
		self.update_shifts( shifts )


	def update_shifts( self, shifts ):
		""" Method to create/update the prices for every shift specified in 'shifts'
			The hours are being converted to integers in order to have a cleaner
			code afterwards and not having to convert them every time they are requested.
			in:
				shifts (dict):	Dictionary with the shifts as keys, and they corresponding
								begining and ending time
			out:
				None
		"""
		result = {}
		for k, v in shifts.items():
			h_in, h_out = v
			h_in = int( h_in.split(":")[0] ) 
			h_out = int( h_out.split(":")[0] )
			if h_out == 0:
				h_out = 24
			result[k] = [h_in, h_out]
		self.shifts = result
		return


	def determine_day_load( self, day ):
		""" Function to, given a day determine how many hours where worked in each shift
			in:
				day (string):	A string with format 'hh:mm-hh:mm' indicating
								the begining and endig hours of work for the day
			out:
				result(dict)	A dictionary in the form {k:v} where 'k' are the
								names of the shifts defined in 'self.shifts', and
								'v' the ammount of hours worked for that shift
		"""
		pattern = r"\d{2}:\d{2}"
		hour_in, hour_out = re.findall( pattern, day )
		hour_in = [int( x ) for x in hour_in.split(":")][0]
		hour_out = [int( x ) for x in hour_out.split(":")][0]
		result = {}
		if hour_in > hour_out:
			hour_out = 24
		for k, v in self.shifts.items():
			shift_in, shift_out = v
			hours = min(hour_out, shift_out) - max(hour_in, shift_in)
			result[k] = max(hours, 0)
		return result

	def determine_shift_load( self, week ):
		""" Function to, given a week determine worload of every shift for each day
			in:
				week (string):		String in the format '{day},{day}...', with
									day defined as some letters specifying the day
									followed by 'hh:mm-hh:mm',for the days worked in
									that week
									example: MO10:00-12:00,TU10:00-12:00,TH01:00-03:00,SA14:00-18:00,SU20:00-21:00
			out:
				result (dict):		Dictionary in the form '{k:v}' with 'k' as 
									letters representing the day and 'v' a dict with
									the shift load as specified in the 'determine_day_load'
									function output.
		"""

		result = {}
		day_pattern = r"[a-zA-Z]+"
		for day in week.split(","):
			d = re.findall(day_pattern, day)[0]
			work = day[len(d):]
			worked_hours = self.determine_day_load( work )
			result[d] = worked_hours
		return result

	def determine_amounts( self, workload ):
		""" Function to calculate the amount to be paid for each day given a dictionary
			with the hours worked in each shift.
			in:
				workload (dict):	A dictionary containing the worked days and for
									each day, how many hours were worked
									in each shift.
			out:
				result (array)		An array in wich each value is a tuple indicating
									the day and the amount to be paid for that day.
		"""

		
		# iterating just over the days worked according to the input
		day_keys = list( set(workload.keys() ) & set( self.prices.keys() ) )
		shift_keys = self.shifts.keys()
		weekly_ammount = []
		for dk in day_keys:
			prices = self.prices[dk]
			work = workload[dk]
			daily_payment = 0
			for sk in shift_keys:
				daily_payment += prices.get(sk, 0) * work.get(sk, 0)
			weekly_ammount.append((dk, daily_payment))
		return weekly_ammount


	def calcaulate_payment( self, week ):
		""" Function in charge of calculate the amount to be paid for a specified
			amount of worked hours.
			in:
				week (string):		String in the format '{day},{day}...', with
									day defined as some letters specifying the day
									followed by 'hh:mm-hh:mm',for the days worked in
									that week
									example: MO10:00-12:00,TU10:00-12:00,TH01:00-03:00,SA14:00-18:00,SU20:00-21:00
			out:
				amount (int):		Amount to be paid according to the specified workload.
		"""

		workload = self.determine_shift_load( week )	# Delegating the shift load calculation
		ammounts = self.determine_amounts( workload )		# Delegating the paid/day calculation
		amount = sum( [y for (x,y) in ammounts])
		return amount







def create_parser():
	""" Utilitary function used to manage the arguments being passed to the function.
	"""
	parser = argparse.ArgumentParser(
		description='Given a file name, calculates the payment of the emplyees by the information contained in it.')
	parser.add_argument('file', type=str, help='path to the file containing the employees work record.')
	return parser.parse_args()


def main():
	""" Main function in charge of initializing the objects and delegating
		the responsibilities to maintain a clear understanding of the process
	"""

	parser = create_parser()
	contador = Payroll.instance( SHIFTS, HOURLY_PRICES )
	reader = FileReader( parser.file )

	line = reader.next()
	while line:
		name, record = line.split("=")
		ammount = contador.calcaulate_payment( record )
		print(f"El monto a pagar de {name} es: {ammount} USD\n")
		line = reader.next()


if __name__ == "__main__":
    main()
