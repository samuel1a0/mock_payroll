# mock_payroll

Toy project for calculating payment amounts based on worked hours

The script just uses libraries within the standard Python core, so no need to install anything.

## Runing the script

To run the script just execute the following line:

``python task.py [path_to_file]``

The expected file format is 'txt' and every line should represent the record for an entire week starting with the name of the emplyee
followed with the hours worked each day as follows:

``Mason=MO12:00-14:00,TU16:00-18:00,TH20:00-22:00,SA13:00-15:00,SU10:00-12:00``

Where the values MO, TU, TH, FR, SA and SU are acronyms for each day of the week.

To see this in action you can execute the code with the example provided like this (you can check the expected results for each worker in the ``examples/expected_results.txt`` file):

```sh
python task.py examples/example.txt
```

### Important Notes:

For the time being, if a line contains a record like MO22:00-03:00 (indicating work starting one day and finishing at dawn the next day) just the hours until between 22:00 and 00:00 will be counted, as the other hours should've been put in the record for the next day instead.

In order to not complicate the script too much for this mock example, the hours are being taken entirely.
For example, a record like TU14:25-16:00 will be taken as two complete hours instead of 1 hour and 35 minutes.

