import tkinter as tk                # For GUI widgets
from tkinter import messagebox      # For Close Program popup widget
import datetime as dt               # For time management of flights
import os                           # For Determining if file path exists
import random                       # For construction of random data, determining if flight has delay


class Airport:
    """
    Airport class is used to provide an origin or destination for flights, alongside housing inbound, outbound and
    landed flights within lists.

    When constructed, the Airport will proceed to gather and store references to Flight objects from the allFlights
    parameter. Newly constructed flights are directly assigned to the Airport.
    """
    def __init__(self, name, allFlights):
        self.name = name
        self.inboundFlights = []
        self.outboundFlights = []
        self.landedFlights = []
        self.GetAirportFlightData(allFlights)

    def GetAirportFlightData(self, flightsList):
        """
        obtain inbound and outgoing flights for this airport name from `flightsList`,
        which is the `ongoingFlights.txt` file
        :param flightsList:
        :return:
        """
        for flight in flightsList:
            # Determine if flight belongs to inbound or outbound list:
            if flight.fliOrigin == self.name:
                self.outboundFlights.append(flight)
            elif flight.fliDestination == self.name:
                self.inboundFlights.append(flight)


class Flight:
    """
    Flight Objects travel between two airports, set as their Origin and Destination. They may be constructed using data
    stored within the `ongoingFlights.txt` file, or from user inputs.

    When the time is within a Flight's "flight window" - the time between timetabled departure and arrival time - it
    will depart, allowing the flight to update its remaining distance of travel between the Origin and Destination
    airports until reaching 0.

    Flights with a remaining distance > 0 will be saved to the `ongoingFlights.txt` file upon program close (if the
    user permits).
    """
    def __init__(self, flightDetails, airlineDetails, timeDetails, stringDetailsList):
        # fli is for flight, al is for airline. shortened for simpler var names
        self.stringDetailsList = stringDetailsList
        # flight details
        self.fliNum = flightDetails[0]
        self.fliCode = flightDetails[1]
        self.fliOrigin = flightDetails[2]
        self.fliDestination = flightDetails[3]
        self.fliSpeed = float(flightDetails[4])
        self.fliDist = float(flightDetails[5])
        # airline/aircraft details
        self.aircraft = airlineDetails[0]
        self.alName = airlineDetails[1]
        self.alCode = airlineDetails[2]
        # timetabling, and delay details (in timedelta objects)
        self.ttblDepartTime = self.StripTime(timeDetails[0])
        self.ttblArriveTime = self.StripTime(timeDetails[1])
        # Since programTime operates in 24hr loop, arrival time can be < departure time, hence:
        if self.ttblArriveTime < self.ttblDepartTime:
            self.trueArrive = dt.timedelta(days=1, seconds=self.ttblArriveTime.seconds)
        else:
            self.trueArrive = self.ttblArriveTime
        self.appxArriveTime = self.StripTime(timeDetails[2])
        self.delayTime = self.StripTime(timeDetails[3])

        # Ensure flight only "flies" when it should be:
        self.hasDeparted = self.GetBool(timeDetails[4])  # Departs when program time is >= to departure time:
        self.isDeparting = self.GetBool(timeDetails[5])  # Is the program due to be departing in the next timeframe
        self.hasLanded = False

    def UpdateDistanceAndTime(self, prevTime, programTime):
        """
        This function will first determine if the Flight can be updated. This is done through checking the hasLanded
        value of the Flight (True will result in the function ending without updating values) and if program time is
        within the flight window. Should the programTime be within the Flight window, the Flight departs, and the
        function begins to update the remaining distance value.

        The remaining distance value is decremented by the flight speed (converted to seconds) multiplied by the change
        in time since the function was last called.
        :param prevTime:
        :param programTime:
        :return:
        """
        if self.hasLanded:
            print("Flight Landed, ignoring Update Function")
            return

        # Ensures time is within the "flightwindow" - the time between departure and arrival of the flight
        # before permitting flight to depart
        if programTime <= self.ttblDepartTime and programTime <= self.ttblArriveTime < self.ttblDepartTime:
            inFlightWindow = True
        elif self.ttblDepartTime <= programTime <= self.trueArrive:  # in flight window
            inFlightWindow = True
        else:  # Not currently in flight window
            self.isDeparting = True
            inFlightWindow = False

        # Shift Program Time to account for 24hr repeat loop:
        if prevTime > programTime:
            programTime = dt.timedelta(days=1, seconds=programTime.seconds)

        if (inFlightWindow and self.isDeparting) or self.hasDeparted:
            # get change in time since function last called
            # ensure that change of time is no greater than timechange from the earliest the Flight could have departed
            timechange = programTime - prevTime
            if prevTime < self.ttblDepartTime and not self.hasDeparted:
                timechange = programTime - self.ttblDepartTime

            self.isDeparting = False  # Update departing status - plane will not depart again after arriving
            self.hasDeparted = True  # Flight Distance will continue to decrease to 0 regardless of timeframe

            distanceCovered = (self.fliSpeed / 60 / 60) * timechange.seconds  # speed converted from km/h to km/s
            newDist = self.fliDist - distanceCovered
            if newDist > 0:
                self.fliDist = newDist
                seconds = (self.fliDist / self.fliSpeed) * 60 * 60  # Get remaining time in flight in seconds
                flightTimeRemaining = dt.timedelta(seconds=int(seconds))
                self.appxArriveTime = programTime + flightTimeRemaining
                self.delayTime = self.appxArriveTime - self.trueArrive
                if self.delayTime.days < 0:
                    self.delayTime = dt.timedelta(seconds=0)

                if self.appxArriveTime.days == 1:   # remove days value to retain 24:00:00 format
                    self.appxArriveTime = self.appxArriveTime - dt.timedelta(days=1)
            else:   # Distance <=0 so flight has landed at destination airport
                self.fliDist = 0
                self.hasLanded = True
                self.hasDeparted = False

    @staticmethod
    def StripTime(time):
        """
        Converts non-timedelta parameters into timedelta values. Used primarily for reading data from file.
        :param time:
        :return:
        """
        if type(time) is not dt.timedelta:
            time = dt.datetime.strptime(time, "%H:%M:%S")   # Obtain datetime value
            return dt.timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)  # Convert to timedelta
        else:  # time is of timedelta type already
            return time

    @staticmethod
    def GetBool(string):
        """
        Converts non-boolean parameters into boolean values. Used primarily for reading data from file.
        :param string:
        :return:
        """
        if type(string) is not bool:
            if string == "True":
                return True
            elif string == "False":
                return False
        else:  # Already boolean
            return string

    def GetFlightValue(self, stringTerm):
        """
        Function utilises a dictionary to utilise a string input parameter as a key for obtaining a tuple of the value
        stored within the Flight that the string refers to, and the data type of the value.
        :param stringTerm:
        :return:
        """
        flightDataList = [(self.fliNum, 'int'), (self.fliCode, 'str'), (self.fliOrigin, 'str'),
                          (self.fliDestination, 'str'),
                          (self.fliSpeed, 'float'), (round(self.fliDist, 1), 'float'), (self.aircraft, 'str'),
                          (self.alName, 'str'), (self.alCode, 'str'), (self.ttblDepartTime, 'time'),
                          (self.ttblArriveTime, 'time'), (self.appxArriveTime, 'time'), (self.delayTime, 'time'),
                          (self.hasDeparted, 'bool'), (self.isDeparting, 'bool')]
        # Construct Dictionary from flight data strings and flight data list:
        flightTermDict = {self.stringDetailsList[i]: flightDataList[i] for i in range(len(self.stringDetailsList))}
        return flightTermDict[stringTerm]


class Main:
    """
    This is the main body of the program. Contains variables accessed by multiple screen classes, and also provides the
    construction of the main Tk root window.

    Additionally, reads data from the `ongoingFlights.txt` and `AirportsAirlines.txt` files to construct Flights and
    Airports.

    Also performs the program loop for updating the GUI, programTime and Flight Values, alongside providing code for the end-of-program processes, such
    as saving data to files.
    """
    def __init__(self):
        # For determining end-of-program processes:
        self.running = True
        self.updateFile = False

        # Confirm that the file paths exist, else close program
        self.allFlightsFileName = self.ConstructFile("ongoingFlights.txt")
        self.airportsAirlinesFileName = self.ConstructFile("AirportsAirlines.txt")

        # construct tk root window, title, size
        self.root = tk.Tk()
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self.root.title('Airport Flight Arrival Enquiry Software')
        self.root.resizable(False, False)
        # Protocol dictates what happens when user attempts to close the tk window
        self.root.protocol("WM_DELETE_WINDOW", self.CloseProgramMessage)

        # construct program time and time multiplier display
        self.programTimeFrame = tk.Frame(self.root, relief='raised', borderwidth=5)
        self.programTimeFrame.grid(row=0, column=0, sticky='nsew')
        tk.Label(self.programTimeFrame, text='Current Program Time:').grid(row=0, column=0)
        self.programTimeDisplay = tk.Text(self.programTimeFrame, width=15, height=1, bg='light gray')
        self.programTimeDisplay.grid(row=0, column=1)
        self.programTimeDisplay.config(state='disabled')
        tk.Label(self.programTimeFrame, text="Time Multiplier:").grid(row=0, column=2)
        self.inputTimeMultiplier = tk.StringVar()
        self.inputTimeMultiplier.set("1")
        tk.Entry(self.programTimeFrame, textvariable=self.inputTimeMultiplier).grid(row=0, column=3)

        # Initialise Program Time from file:
        self.timeMultiplier = 1
        timeString = open(self.allFlightsFileName, 'r').readlines()[1].strip()[1:]
        time = dt.datetime.strptime(timeString, "%H:%M:%S")  # Create time object
        self.programTime = dt.timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
        self.prevTime = self.programTime  # Monitor change in time for updating flight values
        self.UpdateProgramTime()

        # Get Data Search Terms from file:
        # read first line, remove \n and # char, split into list of values
        # print("Unsplit search terms list:\n", open(self.allFlightsFileName).readline().strip())
        self.dataSearchTerms = open(self.allFlightsFileName).readline().strip()[1:].split(', ')

        # Read Flight data from file:
        self.allFlights = []
        self.maxFlights = 75
        for flight in open(self.allFlightsFileName).readlines():
            # Omit lines beginning with #, no value or \n char as these are not flight data lines
            omit = ['#', '', '\n', ' ']
            if flight[0] not in omit:
                flightData = flight.strip().split(', ')
                # Split data into categories using slices of the total flight data list
                flightDetails = flightData[:6]
                airlineDetails = flightData[6:9]
                timeDetails = flightData[9:]
                self.allFlights.append(Flight(flightDetails, airlineDetails, timeDetails, self.dataSearchTerms))

        # Construct Airports and get Airline Data from file:
        # gets 1st line from file, remove \n, # chars, split into a list of airport names
        with open(self.airportsAirlinesFileName, 'r') as file:
            self.airlineDataSets = []
            self.airlineNames = []
            for line in file:
                if line[0] == '#':
                    self.airportNames = line.strip()[1:].split(', ')
                else:
                    self.airlineDataSets.append(line.strip().split(', '))
                    self.airlineNames.append(self.airlineDataSets[-1][0])

        self.airports = []
        for airport in self.airportNames:
            # Create list of airport objects
            self.airports.append(Airport(airport, self.allFlights))
            # print("Created new airport:", self.airports[-1], airport)

        # Construct Program Screens:
        # Screens are classes containing tk Widgets and necessary functions, with self passed as parameter, so they can
        # access AirTrafficControl vars/funcs
        self.screenFrames = [AirportFlightsScreen(self), SearchFlightDataScreen(self), AddFlightAirportScreen(self)]
        for sf in self.screenFrames:
            sf.Construct()

        # Construct Menubar to switch between screens of the program:
        self.menubar.add_command(label='Display Airport Flights',
                                 command=lambda: self.SwitchScreen(self.screenFrames[0]))
        self.menubar.add_command(label='Search All Flights',
                                 command=lambda: self.SwitchScreen(self.screenFrames[1]))
        self.menubar.add_command(label='Add New Airport/Flight',
                                 command=lambda: self.SwitchScreen(self.screenFrames[2]))

        self.SwitchScreen(self.screenFrames[0])  # Display Airport Flights screen to load in automatically

        self.FlightUpdateLoop()  # Starts the flight update loop, runs every 500ms#
        self.ProgramLoop()  # Run window updates
        self.EndProgram()  # Run Close Program Code (update files)

    def ProgramLoop(self):
        """
        Continuously runs until the user confirms that they wish to close the program, or the program is forcefully
        closed by KeyboardInterrupt.
        :return:
        """
        while self.running:
            try:
                self.root.update()
            except KeyboardInterrupt:  # Program closed through unexpected means, File not updated.
                self.running = False

    def EndProgram(self):
        """
        This code runs after the user confirms that they wish to close the program, or the program is forcefully closed
        by KeyboardInterrupt
        :return:
        """
        if self.updateFile is False:
            print("Files not updated.")
            return

        # sort self.allFlights into list organised by timetabled arrival time (ascending from 00:00:00 to 23:59:59)
        self.allFlights.sort(key=lambda fliDat: fliDat.ttblArriveTime)

        # Update the ongoingFlights File
        with open(self.allFlightsFileName, 'w') as file:
            # Construct the Data Search Term Strings line:
            dataSearchTermStrings = f"#{self.dataSearchTerms[0]}"
            for searchTerm in self.dataSearchTerms[1:]:
                dataSearchTermStrings = f"{dataSearchTermStrings}, {searchTerm}"
            file.write(f"{dataSearchTermStrings}\n")

            # Construct the programTime line:
            file.write(f"#{self.programTime}\n")

            # Construct the updated flight data lines:
            for flight in self.allFlights:
                if not flight.hasLanded:
                    # Construct string of Flight object's values:
                    flightDataString = f"{flight.GetFlightValue(self.dataSearchTerms[0])[0]}"
                    for dataValue in self.dataSearchTerms[1:]:
                        flightDataString = f"{flightDataString}, {flight.GetFlightValue(dataValue)[0]}"
                    file.write(f"{flightDataString}\n")

        # Update AirportsAirlines file:
        with open(self.airportsAirlinesFileName, 'w') as file:
            # Construct Airport names String line:
            airportNamesString = f"#{self.airportNames[0]}"
            for airport in self.airportNames[1:]:
                airportNamesString = f"{airportNamesString}, {airport}"
            file.write(f"{airportNamesString}\n")

            # Construct airline data into string lines
            for airline in self.airlineDataSets:
                airlineDataString = f"{airline[0]}"
                for data in airline[1:]:
                    airlineDataString = f"{airlineDataString}, {data}"
                file.write(f"{airlineDataString}\n")
        print("Files updated.")

    @staticmethod
    def ConstructFile(fileName):
        """
        This function will determine if a file already exists for a path, given by a string parameter. If the file is
        not found, then the program will construct new files with default data entered into them. This data can then be
        used to continue normal use of the program.
        :param fileName:
        :return:
        """
        if os.path.exists(fileName):  # Tests if file path exists.
            return fileName
        else:  # File path not found
            print(f"Essential file: {fileName} NOT in local space. Ensure file has accessible presence in local space.")
            print("File will be constructed using default data in program.")
            if fileName == "AirportsAirlines.txt":  # Determine which file is being constructed, and hence what data
                defaultAirportsString = "#East Midlands Airport, Heathrow Airport, Birmingham International Airport\n"
                defaultAirlineString = ("BritishAirways, BA, Boeing787-9, Airbus A350-1000, Airbus A380-800, Embraer "
                                        "190-BA, 1050, 905, 1086, 870")
                with open(fileName, 'w') as file:
                    file.write(defaultAirportsString)
                    file.write(defaultAirlineString)
            elif fileName == "ongoingFlights.txt":  # Determine which file is being constructed, and hence what data
                defaultDataString = ("#Flight Number, Flight Code, Origin, Destination, Current Speed, Rem. Distance, "
                                     "Aircraft, Airline, Airline Code, Departure Time, Arrival Time, APPX Arrival "
                                     "Time, Delay Time, Has Departed, is Departing\n")
                defaultProgramTime = "#07:30:00"
                with open(fileName, 'w') as file:
                    file.write(defaultDataString)
                    file.write(defaultProgramTime)
            return fileName

    def UpdateProgramTime(self):
        """
        Updates the programTime by a set amount every real-time second. This set amount may be anywhere from 0 to
        6 hours. Larger values will default to 6 hours, and smaller or other non-suitable values default to 1.

        :return:
        """
        try:
            # Obtain the time Multiplier, which alters the rate at which the Program Time is updated
            self.timeMultiplier = int(self.inputTimeMultiplier.get())
            # Limit speed of timeMultiplier
            if self.timeMultiplier > 3600*6:
                raise OverflowError
            if self.timeMultiplier < 0:
                raise ValueError
        except (ValueError, AttributeError):
            # No value in time Multiplier input, use default value 1 / ScreenFrames not yet constructed
            # / value inputted was below 0
            self.timeMultiplier = 1
        except OverflowError:
            # Value set was too large, go by 6hours per second
            self.timeMultiplier = 3600 * 6

        self.programTime = dt.timedelta(seconds=self.programTime.seconds + (1 * self.timeMultiplier))
        if self.programTime.days >= 1:
            # If the Program Time is at 24:00:00 or greater, removes days value to keep to 24hr time only
            ptSeconds = int(self.programTime.seconds)
            self.programTime = dt.timedelta(seconds=ptSeconds)

        # Update the program time display, and ensure it is non-editable by user:
        self.programTimeDisplay.config(state='normal')
        self.programTimeDisplay.delete('1.0', 'end')
        self.programTimeDisplay.insert('1.0', str(self.programTime))
        self.programTimeDisplay.config(state='disabled')
        self.root.after(1000, self.UpdateProgramTime)

    def CloseProgramMessage(self):
        """
        This function determines the actions taken by the program when the user attempts to close the root window.
        Provides a popup window prompt to confirm that the user wishes to close the program, and if or if not to save
        the updated Flight data.
        :return:
        """
        # Confirm close, and if to update the program files
        messageboxMessage = 'Closing Program. Would you like to update the program files?'
        updateFile = messagebox.askyesnocancel('Quit', messageboxMessage)
        # Returns True, False or None (to not close program)
        if updateFile:
            self.running = False
            self.updateFile = True
        elif updateFile is False:
            self.running = False
            self.updateFile = False

    def SwitchScreen(self, screenToGrid):
        """
        switches the screen by grid "forgetting" the current screen and "gridding" the new one, which is given
        via parameter.
        :param screenToGrid:
        :return:
        """
        for screen in self.screenFrames:
            if screen.body.winfo_ismapped():  # If the screen is currently displayed in root window.
                screen.body.grid_forget()
        screenToGrid.body.grid(row=1, column=0)

    def FlightUpdateLoop(self):
        """
        This function runs through all flights stored within the allFlights list and calls their UpdateDistanceAndTime
        function. following this, if a flight has landed, it is removed from it's respective airports' inbound and
        outbound lists, and moved into the landedFlights list of the Destination Airport.

        Flights which have landed are then removed from the allFlights list, so that they are not continuously updated
        and to permit more flights to be made (75 max ongoing flights)
        :return:
        """
        for i, flight in enumerate(self.allFlights):
            flight.UpdateDistanceAndTime(self.prevTime, self.programTime)  # Update Flight Values
            if flight.hasLanded:
                for airport in self.airports:  # iterate through all airports to find flight references
                    for inb, inbFlight in enumerate(airport.inboundFlights):
                        if flight == inbFlight:
                            airport.landedFlights.append(airport.inboundFlights.pop(inb))
                            break  # Flight found
                    for outb, outbFlight in enumerate(airport.outboundFlights):
                        if flight == outbFlight:
                            airport.outboundFlights.pop(outb)
                            break  # Flight found
                self.allFlights.pop(i)  # Remove from allFlights list

        self.prevTime = self.programTime  # Update previous time
        self.root.after(1000, self.FlightUpdateLoop)  # Calls function automatically after 1 second

    @staticmethod
    def ConstructDynamicDataGrid(frame, nwrow, nwcol, dataLabels, width=800, height=400, numRows=5):
        """
        Constructs a scrollable data grid which data can be inserted into through the use of a tk.Canvas Widget to house
        a tk.Frame containing the data grid.

        The Canvas is constructed with the `frame` parameter as its root, at the position [nwcol+1, nwrow+1].
        A Horizontal Scrollbar is constructed above the Canvas, and a Vertical Scrollbar to the left of the Canvas.

        `DataLabels` is a list of strings, which are used to construct tk.Label widgets as the headers of each column.
        Minimum columns in the data grid is 6, but maximum is unlimited. `numRows` determines the number of rows in the
        data grid, defaulting to the minimum 5, and is able to be at most 25.

        Parameters `width` and `height` are used to determine the size of the canvas, defaulting to 800 and 400
        respectively.

        This function is adapted from https://stackoverflow.com/a/3092341 [accessed 14th November 2023]
        :param frame:
        :param nwrow:
        :param nwcol:
        :param dataLabels:
        :param width:
        :param height:
        :param numRows:
        :return:
        """
        # Construct Canvas and inner frame window widgets
        canvas = tk.Canvas(frame, borderwidth=5, relief='raised', bg='gray', width=width, height=height)
        canvas.grid(row=nwrow+1, column=nwcol+1)
        canvasFrame = tk.Frame(canvas)
        canvas.create_window((4, 4), window=canvasFrame, tags="self.srFrameInCanvas", anchor="nw")

        # Construct Vertical and Horizontal Scrollbars
        vsb = tk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        vsb.grid(row=nwrow+1, column=nwcol, sticky='ns')
        canvas.config(yscrollcommand=vsb.set)
        hsb = tk.Scrollbar(frame, orient='horizontal', command=canvas.xview)
        hsb.grid(row=nwrow, column=nwcol+1, sticky='ew')
        canvas.config(xscrollcommand=hsb.set)
        canvasFrame.bind("<Configure>", lambda x: canvas.configure(scrollregion=canvas.bbox("all")))

        # Construct labels from the DataLabels list:
        dataFieldLabels = []
        for i, label in enumerate(dataLabels):
            dataFieldLabels.append(tk.Label(canvasFrame, text=label))
            dataFieldLabels[-1].grid(row=0, column=i)
        if len(dataLabels) < 6:  # Ensure there are a minimum of 6 columns
            for i in range(6 - len(dataLabels)):
                dataFieldLabels.append(tk.Label(canvasFrame, text=""))  # Empty labels
                dataFieldLabels[-1].grid(row=0, column=6 - i)

        # Ensure rows number between 5 and 25:
        numRows = min(25, numRows)
        numRows = max(5, numRows)

        # construct the datagrid:
        dataFieldRows = []
        for row in range(numRows):
            dataField = []
            for col in range(len(dataFieldLabels)):  # Construct a row of cells for the data grid
                bg = 'light gray' if row % 2 == 0 else 'white'
                dataField.append(tk.Text(canvasFrame, width=15, height=2, state='disabled', bg=bg,
                                         borderwidth=1, pady=1, wrap='word'))
                dataField[-1].grid(row=row + 1, column=col)
            dataFieldRows.append(dataField)  # add constructed row to data grid cells list
        return canvas, [canvasFrame, dataFieldLabels, dataFieldRows]

    @staticmethod
    def InsertValuesToDataGrid(dataGrid, dataLabels, flightData):
        """
        This function updates values within a given dataGrid by deleting all values currently present in the data grid,
        and then iterating through a set of flightData, updating the cells in each row of the data grid with the values
        obtained from flightData.
        :param dataGrid:
        :param dataLabels:
        :param flightData:
        :return:
        """
        # Delete all values in dataGrid cells:
        for dataRow in dataGrid:
            for dataField in dataRow:
                dataField.config(state='normal')
                dataField.delete('1.0', 'end')
                dataField.config(state='disabled')

        # Sort data being inputted by arrival time
        flightData.sort(key=lambda fli: fli.ttblArriveTime)

        # Insert into dataGrid:
        for row, flight in enumerate(flightData):
            try:
                for col, label in enumerate(dataLabels):
                    dataGrid[row][col].config(state='normal')
                    dataGrid[row][col].insert('1.0', flight.GetFlightValue(label)[0])
                    dataGrid[row][col].config(state='disabled')
            except IndexError:
                # more flights than present rows to input data into, hence end loop as all rows filled.
                break

    @staticmethod
    def UpdateOptionMenuItems(menu, optionList, strvar, default=''):
        """
        This function updates the options within a tk.OptionMenu widget's dropdown menu.

        This function is adapted from: https://stackoverflow.com/a/17581364 [Accessed 14th November 2023]
        :param menu:
        :param optionList:
        :param strvar:
        :param default:
        :return:
        """
        menu['menu'].delete(0, 'end')  # Remove all items in optionMenu
        strvar.set(default)  # set prompt to given value
        for option in optionList:
            menu['menu'].add_command(label=option, command=tk._setit(strvar, option))  # Adds option to optionMenu

    @staticmethod
    def Converter(dataType, fliValue, searchValues):
        """
        This function acts as a data type converter for values fetched from the flight object, and for the values
        inputted into the search by the user. This ensures that the data can be suitably compared.

        :param dataType:
        :param fliValue:
        :param searchValues:
        :return:
        """
        convValues = []
        if dataType == 'int':  # Convert to int
            convValues = [int(searchValues[i]) for i in range(len(searchValues))]
            return int(fliValue), convValues
        elif dataType == 'float':  # Convert to float
            convValues = [float(searchValues[i]) for i in range(len(searchValues))]
            return float(fliValue), convValues
        elif dataType == 'bool':  # Convert bools into strings
            fliValue = f"{fliValue}"
            return fliValue, searchValues
        elif dataType == 'time':  # Convert into timedeltas
            for i, sv in enumerate(searchValues):
                try:
                    time = dt.datetime.strptime(sv, "%H:%M:%S").time()
                    timedelta = dt.timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
                    convValues.append(timedelta)
                except ValueError:  # Unsuitable inputs are provided, revert to default values
                    convValues = [dt.timedelta(seconds=0) for _ in range(len(searchValues))]
            return fliValue, convValues
        else:  # Values did not need converting
            return fliValue, searchValues


class AirportFlightsScreen:
    """
    This Class provides the user with the Airport Flights screen. From this screen, the user can select a specific
    airport and view the inbound, outbound, and landed flights.

    Main is passed as a parameter so that the class can access the variables stored within it, without having to utilise
    inheritance and creation of a new Main instance.
    """
    def __init__(self, host):
        self.host = host
        self.body = tk.Frame(self.host.root)
        self.framesList = [tk.Frame(self.body, relief="raised", borderwidth=5) for _ in range(4)]

        # Flight Data Display Values:
        self.apSelection = tk.StringVar()  # OptionMenu value which stores the airport name which user selects
        self.apSelection.set('Select Airport')  # Set default value to the OptionMenu selection

        # Default values from flights which are displayed:
        self.displayInbDataValues = ['Flight Code', 'Origin', 'Arrival Time', 'Departure Time', 'Delay Time',
                                     'Rem. Distance']
        self.displayOutbDataValues = ['Flight Code', 'Destination', 'Arrival Time', 'Departure Time', 'Delay Time',
                                      'Rem. Distance']
        self.displayLandedDataValues = ['Flight Code', 'Origin', 'Arrival Time', 'Delay Time']

        # Construct var-stored Widgets:
        self.airportMenu = tk.OptionMenu(self.framesList[0], self.apSelection, *self.host.airportNames)
        self.inboundCanvas, self.inbCanvasFrameWidgets = (
            self.host.ConstructDynamicDataGrid(self.framesList[1], 1, 0, self.displayInbDataValues, 700, 200, 10))
        self.outboundCanvas, self.outbCanvasFrameWidgets = (
            self.host.ConstructDynamicDataGrid(self.framesList[2], 1, 0, self.displayOutbDataValues, 700, 200, 10))
        self.landedCanvas, self.landedCanvasFrameWidgets = (
            self.host.ConstructDynamicDataGrid(self.framesList[3], 1, 0, self.displayLandedDataValues, 500, 200, 10))

    def Construct(self):
        """
        This function is utilised to grid any widgets defined within __init__, alongside constructing and mapping
        Widgets which do not require a variable for storage.
        :return:
        """
        # grid Frames:
        self.framesList[0].grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.framesList[1].grid(row=1, column=0, sticky='nsew')
        self.framesList[2].grid(row=2, column=0, sticky='nsew')
        self.framesList[3].grid(row=1, column=1, sticky='nsew')

        # Airport Selection Frame
        tk.Label(self.framesList[0], text='Get Flight Data From:').grid(row=0, column=0)
        self.airportMenu.grid(row=0, column=1)

        # Flight Data Frame Labels:
        tk.Label(self.framesList[1], text='Inbound Flights Data').grid(row=0, column=0, columnspan=6)
        tk.Label(self.framesList[2], text='Outbound Flights Data').grid(row=0, column=0, columnspan=6)
        tk.Label(self.framesList[3], text='Landed Flights Data').grid(row=0, column=0, columnspan=6)

        self.UpdateAirportDisplay()

    def UpdateAirportDisplay(self):
        """
        This function updates the data grids each second to display the relevant flight information for the currently
        selected Airport. This function only performs the updates when the frames are visible, hence it does not use up
        proccessing whilst the user is on other screens.
        :return:
        """
        for airport in self.host.airports:
            # only update frames when they are visible
            if self.apSelection.get() == airport.name and self.body.winfo_ismapped():
                self.host.InsertValuesToDataGrid(self.inbCanvasFrameWidgets[2], self.displayInbDataValues,
                                                 airport.inboundFlights)
                self.host.InsertValuesToDataGrid(self.outbCanvasFrameWidgets[2], self.displayOutbDataValues,
                                                 airport.outboundFlights)
                self.host.InsertValuesToDataGrid(self.landedCanvasFrameWidgets[2], self.displayLandedDataValues,
                                                 airport.landedFlights)
        self.host.root.after(1000, self.UpdateAirportDisplay)  # Creates loop, calls function again every second.


class SearchFlightDataScreen:
    """
    This Class provides the user with the Search Flights Screen. From this screen, the user can search flights with
    specific data and search terms. The matching flights are then displayed in a data grid on the right-hand side of
    the window.

    Main is passed as a parameter so that the class can access the variables stored within it, without having to utilise
    inheritance and creation of a new Main instance.
    """
    def __init__(self, host):
        self.host = host
        self.body = tk.Frame(self.host.root)
        self.framesList = [tk.Frame(self.body, relief='raised', borderwidth=5) for _ in range(2)]

        # Construct Search Term variables list [StringValue 1, StringValue 2, EnabledStatus] for each data element
        self.searchTerms = [[tk.StringVar(), tk.StringVar(), tk.IntVar()] for _ in range(len(self.host.dataSearchTerms))]
        self.searchedFlights = []  # List of flights which match search data

        # Construct search results canvas
        self.searchResultsCanvas, self.srCanvasFrameWidgets = (
            self.host.ConstructDynamicDataGrid(self.framesList[1], 0, 0, self.host.dataSearchTerms, 800, 400, 50))

    def Construct(self):
        """
        This function is utilised to grid any widgets defined within __init__, alongside constructing and mapping
        Widgets which do not require a variable for storage.
        :return:
        """
        # Grid frames:
        self.framesList[0].grid(row=0, column=0, sticky='nsew', rowspan=500)
        self.framesList[1].grid(row=0, column=1, sticky='nsew')

        # Provide Column identifiers:
        tk.Label(self.framesList[0], text='Search Term:').grid(row=0, column=0)
        tk.Label(self.framesList[0], text='Value 1 ').grid(row=0, column=1)
        tk.Label(self.framesList[0], text='Value 2 ').grid(row=0, column=2)
        tk.Label(self.framesList[0], text='Enabled?').grid(row=0, column=3)

        for row, searchTerm in enumerate(self.host.dataSearchTerms):
            # Construct a label for each Search Term
            tk.Label(self.framesList[0], text=searchTerm).grid(row=row + 1, column=0)
            # Construct a checkbutton for each Search Term and set to "Enabled"
            tk.Checkbutton(self.framesList[0], variable=self.searchTerms[row][2]).grid(row=row + 1, column=3)
            self.searchTerms[row][2].set(1)
            # Construct Entry Widgets for each Search Term
            tk.Entry(self.framesList[0], textvariable=self.searchTerms[row][0]).grid(row=row + 1, column=1)
            if row not in [2, 3, 6, 7, 8]:
                # Omit string data rows like Destination / Origin Airport, create Entry 2 for each search term
                tk.Entry(self.framesList[0], textvariable=self.searchTerms[row][1]).grid(row=row + 1, column=2)

        # Construct button to apply search terms to data and obtain matching flights
        tk.Button(self.framesList[0], text='Search Flights', command=lambda: self.SearchFlights()).grid(
            row=len(self.searchTerms) + 1, column=0, columnspan=500)

        self.UpdateSearchFrame()

    def SearchFlights(self):
        """
        Search Through allFlights and identify which flights match all search terms that are entered.
        :return:
        """
        self.searchedFlights = []  # list of flights that match the search data
        suitableFlights = self.host.allFlights.copy()
        # Loop through each search term, and each flight remaining within the suitable flights list
        for termIndex, dataQueryInfo in enumerate(self.searchTerms):
            # Get text strings from the input boxes, assign as SearchValues
            searchValues = [dataQueryInfo[0].get(), dataQueryInfo[1].get()]
            if dataQueryInfo[2].get():  # dqi[2] refers to the IntVar, if 1 then the search term is enabled
                if searchValues[0] != '' and searchValues[1] != '':  # Dealing with a range of values
                    for flIndex, flight in enumerate(suitableFlights):
                        # Obtain the flight's value for searched term, and the data type
                        # then convert flight's value and the user's search values to the data type for comparison
                        fliValue, datType = flight.GetFlightValue(self.host.dataSearchTerms[termIndex])
                        fliValue, convValues = self.host.Converter(datType, fliValue, searchValues)
                        if not ((convValues[0] <= fliValue) and (fliValue <= convValues[1])):
                            suitableFlights[flIndex] = ''

                elif searchValues[0] != '':  # Dealing with matching a single value (Entries only in val 2 are ignored)
                    for flIndex, flight in enumerate(suitableFlights):
                        if type(flight) is Flight:
                            fliValue, datType = flight.GetFlightValue(self.host.dataSearchTerms[termIndex])
                            fliValue, convValues = self.host.Converter(datType, fliValue, [searchValues[0]])
                            if fliValue != convValues[0]:  # Only first converted Search value is required
                                suitableFlights[flIndex] = ''

        for flight in suitableFlights:
            if flight != '':
                self.searchedFlights.append(flight)

        self.UpdateSearchFrame(reoccur=False)

    def UpdateSearchFrame(self, reoccur=True):
        self.host.InsertValuesToDataGrid(self.srCanvasFrameWidgets[2], self.host.dataSearchTerms, self.searchedFlights)
        if reoccur and self.body.winfo_ismapped():
            self.host.root.after(5000, self.UpdateSearchFrame)  # Performs loop every 5 seconds


class AddFlightAirportScreen:
    """
    This Class provides the user with the Flight and Airport Management Screen. From this screen, the user can construct
    new flights, alongside manage the current Airports defined within the program, constructing and destructing Airport
    objects.

    Main is passed as a parameter so that the class can access the variables stored within it, without having to utilise
    inheritance and creation of a new Main instance.
    """
    def __init__(self, host):
        self.host = host
        self.body = tk.Frame(self.host.root)
        self.framesList = [tk.Frame(self.body, relief="raised", borderwidth=5) for _ in range(3)]

        # Flight: Construct tk.StringVar() inputs, and set values to them:
        self.canConstructFlight = False
        self.flightDetailStrings = ["Flight Number", "Origin", "Destination", "Airline", "Aircraft", "Departure Time"]
        self.flightDataEntries = [tk.StringVar() for _ in range(len(self.flightDetailStrings))]
        self.flightDataEntries[0].set("0000")
        self.flightDataEntries[1].set("Select Origin")
        self.flightDataEntries[2].set("Select Destination")
        self.flightDataEntries[3].set("Select Airline")
        self.flightDataEntries[4].set("Select Aircraft")
        self.flightDataEntries[5].set("12:00:00")
        self.numFlights = tk.StringVar()

        # Flight: Construct var-stored Widgets:
        self.originMenu = tk.OptionMenu(self.framesList[0], self.flightDataEntries[1], *self.host.airportNames)
        self.destinationMenu = tk.OptionMenu(self.framesList[0], self.flightDataEntries[2], *self.host.airportNames)
        self.airlineMenu = tk.OptionMenu(self.framesList[0], self.flightDataEntries[3], *self.host.airlineNames,
                                         command=lambda x: self.UpdateAircraftOptions())
        self.aircraftMenu = tk.OptionMenu(self.framesList[0], self.flightDataEntries[4], *[''])
        self.valueInfoBoxes = []  # Error markers to fill in red if value unsuitable
        for row in range(len(self.flightDetailStrings)):
            self.valueInfoBoxes.append(tk.Text(self.framesList[0], width=2, height=1, bg='red'))
            self.valueInfoBoxes[-1].config(state='disabled')

        # Airport: Construct tk.StringVar() inputs, and set values to them:
        self.canConstructAirport = True
        self.canDestroyAirport = True
        self.newAirportName = tk.StringVar()
        self.newAirportName.set("Default Airport Name")
        self.destroyAirportName = tk.StringVar()
        self.destroyAirportName.set('Select Airport')

        # Airport: Construct var-stored Widgets:
        self.nameAvailable = tk.Text(self.framesList[2], width=2, height=1, bg='red', state='disabled')
        self.destroyAirportMenu = tk.OptionMenu(self.framesList[2], self.destroyAirportName, *self.host.airportNames)
        self.airportFound = tk.Text(self.framesList[2], width=2, height=1, bg='red', state='disabled')

    def Construct(self):
        """
        This function is utilised to grid any widgets defined within __init__, alongside constructing and mapping
        Widgets which do not require a variable for storage.
        :return:
        """
        # grid Frames:
        self.framesList[0].grid(row=0, column=0, sticky='nsew')
        self.framesList[1].grid(row=1, column=0, sticky='nsew')
        self.framesList[2].grid(row=0, column=1, rowspan=2, sticky='nsew')

        # Flight Constructor - Create and Grid widgets:
        tk.Label(self.framesList[0], text='Create New Flight').grid(row=0, column=0, columnspan=5)
        tk.Button(self.framesList[0], text='Enter Random Data',
                  command=lambda: self.FillRandomData()).grid(row=1, column=0, columnspan=2, sticky='ew')
        tk.Button(self.framesList[0], text='Create Flight',
                  command=lambda: self.ConstructNewFlight()).grid(row=1, column=2, columnspan=2, sticky='ew')

        # Provide labels for each data element the user puts in.
        for row, fdString in enumerate(self.flightDetailStrings):
            tk.Label(self.framesList[0], text=fdString, width=10, padx=5, pady=5).grid(row=row + 2, column=0)

        tk.Entry(self.framesList[0], textvariable=self.flightDataEntries[0]).grid(row=2, column=1)
        tk.Button(self.framesList[0], text='Use Next Available Flight Number',
                  command=lambda: self.SetToFreeFlightNumber()).grid(row=2, column=2)

        # Grid the user-input widgets for flight creation
        self.originMenu.grid(row=3, column=1, sticky='ew')
        self.destinationMenu.grid(row=4, column=1, sticky='ew')
        self.airlineMenu.grid(row=5, column=1, sticky='ew')
        self.aircraftMenu.grid(row=6, column=1, sticky='ew')
        for row in range(len(self.flightDetailStrings)):
            self.valueInfoBoxes[row].grid(row=row + 2, column=4)
        # Entry for the Departure Time:
        tk.Entry(self.framesList[0], textvariable=self.flightDataEntries[5]).grid(row=7, column=1)

        # Random Flight Batch Creator Widget Construction:
        tk.Label(self.framesList[1], text='Create batch of Random Flights').grid(row=0, column=0, columnspan=500)
        tk.Label(self.framesList[1], text="Number of Flights:").grid(row=1, column=0)
        tk.Entry(self.framesList[1], textvariable=self.numFlights).grid(row=1, column=1)
        tk.Button(self.framesList[1], text='Create Random Flights',
                  command=lambda: self.CreateRandomFlightsBatch()).grid(row=1, column=3)

        # Airport Creation Widget Construction:
        tk.Label(self.framesList[2], text='Construct New Airport').grid(row=0, column=0)
        tk.Label(self.framesList[2], text='Airport Name:').grid(row=1, column=0)
        tk.Entry(self.framesList[2], textvariable=self.newAirportName).grid(row=1, column=1)
        self.nameAvailable.grid(row=1, column=2)  # grid infobox for airport creation
        tk.Label(self.framesList[2], text='Construct Airport:').grid(row=2, column=0)
        tk.Button(self.framesList[2], text='Construct',
                  command=lambda: self.ConstructAirport()).grid(row=2, column=1, sticky='ew')

        # Airport Destructor:
        tk.Label(self.framesList[2], text='Destroy Airport').grid(row=3, column=0)
        tk.Label(self.framesList[2], text='Select Airport:').grid(row=4, column=0)
        self.destroyAirportMenu.grid(row=4, column=1, sticky='ew')
        self.airportFound.grid(row=4, column=2)  # grid infobox for airport destruction
        tk.Label(self.framesList[2], text='Destroy Airport:').grid(row=5, column=0)
        tk.Button(self.framesList[2], text='Destroy',
                  command=lambda: self.DestroyAirport()).grid(row=5, column=1, sticky='ew')

        self.FlightValueSuitableCheck()  # Runs Loop to check that inputted values for the flight are suitable
        self.AirportValueSuitableCheck()  # as with flights, but for adding/removing airports

    def ConstructAirport(self):
        """
        This function constructs a new airport from the user-inputted name.
        :return:
        """
        self.AirportValueSuitableCheck()  # Check that name is valid
        if self.canConstructAirport:
            # Ensure correct formatting of new airport name:
            apNameSections = self.newAirportName.get().strip().split(' ')
            apNameSections = [apNameSect.strip() for apNameSect in apNameSections if apNameSect not in ('', ' ')]
            newAirportName = f"{apNameSections[0]}"
            for apNameSect in apNameSections[1:]:
                newAirportName = f"{newAirportName} {apNameSect}"
            if "airport" not in newAirportName.lower():
                newAirportName = f"{newAirportName} Airport"

            newAirport = Airport(newAirportName, self.host.allFlights)  # Construct new Airport object
            # Update Main's airport information lists
            self.host.airports.append(newAirport)
            self.host.airportNames.append(newAirport.name)

            # Update optionMenus with new airport:
            self.host.UpdateOptionMenuItems(self.host.screenFrames[0].airportMenu, self.host.airportNames,
                                            self.host.screenFrames[0].apSelection, "Select Airport")
            self.host.UpdateOptionMenuItems(self.originMenu, self.host.airportNames,
                                            self.flightDataEntries[1], "Select Origin")
            self.host.UpdateOptionMenuItems(self.destinationMenu, self.host.airportNames,
                                            self.flightDataEntries[2], "Select Destination")
            self.host.UpdateOptionMenuItems(self.destroyAirportMenu, self.host.airportNames,
                                            self.destroyAirportName, "Select Airport")

    def DestroyAirport(self):
        """
        This function destroys a user-selected airport - removing the data from Main's lists, and destroying the Airport
        object.
        :return:
        """
        self.AirportValueSuitableCheck(False)  # Ensure airport is valid
        if self.canDestroyAirport:
            for i, airport in enumerate(self.host.airports):
                if airport.name == self.destroyAirportName.get():
                    # Remove airports from Main's info lists
                    self.host.airports.pop(i)
                    self.host.airportNames.pop(i)
                    del airport  # destroys Airport object

        # Update optionMenus with new airport list:
        self.host.UpdateOptionMenuItems(self.host.screenFrames[0].airportMenu, self.host.airportNames,
                                        self.host.screenFrames[0].apSelection, "Select Airport")
        self.host.UpdateOptionMenuItems(self.originMenu, self.host.airportNames,
                                        self.flightDataEntries[1], "Select Origin Airport")
        self.host.UpdateOptionMenuItems(self.destinationMenu, self.host.airportNames,
                                        self.flightDataEntries[2], "Select Destination Airport")
        self.host.UpdateOptionMenuItems(self.destroyAirportMenu, self.host.airportNames,
                                        self.destroyAirportName, "Select Airport")

    def AirportValueSuitableCheck(self, reoccur=True):
        """
        This function determines if the user's inputs for the airport constructor or airport destructor are valid. It is
        used for both airport construction and destruction, and is called on loop every second, alongside whenever the
        construct / destroy airport button is pressed.
        :param reoccur:
        :return:
        """
        if self.body.winfo_ismapped():  # Only runs if the window is currently shown to the user
            # Assume the details are suitable:
            self.canConstructAirport = True
            self.nameAvailable.config(bg='green')
            self.canDestroyAirport = True
            self.airportFound.config(bg='green')

            # ----Perform checks on new airport creation:----
            # Ensure new airport name fits criteria:
            apNameSections = self.newAirportName.get().strip().split(' ')
            apNameSections = [apNameSect.strip() for apNameSect in apNameSections if apNameSect not in ('', ' ')]
            if len(apNameSections) != 0:  # Only proceed if user entry is made
                # Remove Whitespace and construct full name
                newAirportName = f"{apNameSections[0]}"
                for apNameSect in apNameSections[1:]:
                    newAirportName = f"{newAirportName} {apNameSect}"
                if "airport" not in newAirportName.lower():
                    newAirportName = f"{newAirportName} Airport"

                if newAirportName in self.host.airportNames or newAirportName == "Default Airport Name":
                    # Name already exists / is default prompt, so cannot be used
                    self.canConstructAirport = False
                    self.nameAvailable.config(bg='red')

                if len(newAirportName.strip()) < 13:
                    # name too short (is under 5 chars) and cannot be used
                    self.canConstructAirport = False
                    self.nameAvailable.config(bg='red')

            else:  # No name entered
                self.canConstructAirport = False
                self.nameAvailable.config(bg='red')

            # ----Perform checks on airport deletion:----
            # ensure selected airport for destruction meets criteria
            if self.destroyAirportName.get() in self.host.airportNames:  # Ensures is not prompt value
                for airport in self.host.airports:
                    if airport.name == self.destroyAirportName.get():
                        # Prevent destroying Airport whilst it has inbound and outbound flights
                        if len(airport.inboundFlights) > 0 or len(airport.outboundFlights) > 0:
                            self.canDestroyAirport = False
                            self.airportFound.config(bg='red')

            elif self.destroyAirportName.get() not in self.host.airportNames:
                self.canDestroyAirport = False
                self.airportFound.config(bg='red')

        if reoccur:
            self.host.root.after(1000, self.AirportValueSuitableCheck)  # Performs loop of function every second

    def UpdateAircraftOptions(self):
        """
        This function obtains the aircraft list that belongs to a user-selected airline, and updates the aircraft
        selection optionMenu with the new aircraft list.
        :return:
        """
        aircraftList = []
        for airline in self.host.airlineDataSets:
            if airline[0] == self.flightDataEntries[3].get():  # identify airline
                airlineData = airline
                aircraftList = airlineData[2:int(len(airlineData) / 2) + 1]  # obtain aircraft from airline data

        # update optionMenu
        self.host.UpdateOptionMenuItems(self.aircraftMenu, aircraftList, self.flightDataEntries[4], "Select Aircraft")

    def SetToFreeFlightNumber(self):
        """
        This function is used to obtain the lowest unused flight number from a user-selected airline. The function
        compiles all in-use flight numbers for a given airline in their integer forms, in an ascending sort. After
        obtaining the lowest unused flight number, the program creates a 0-padded flight number which is inserted into
        the Flight Number Entry field.
        :return:
        """
        airlineCode = ''
        for airlineData in self.host.airlineDataSets:
            if airlineData[0] == self.flightDataEntries[3].get():
                airlineCode = airlineData[1]  # Get airline Code

        # Get all flight numbers using that airline code:
        fliNumbers = []
        for flight in self.host.allFlights:
            alCode, fliNum = flight.alCode, flight.fliNum  # Get flight data for comparison
            if alCode == airlineCode:  # Flight belongs to airline check
                fliNumbers.append(int(fliNum))  # Adds flight number to list
        fliNumbers.sort()  # Sort numerically ascending

        # Iterate through list to identify the lowest unused value
        nextNum = 0
        for num in fliNumbers:
            if nextNum == num:
                nextNum = num + 1

        # Create 0 padded flight num and set to fli Number entry:
        strNextNum = f"{nextNum}"
        for i in range(4 - len(strNextNum)):
            strNextNum = f"0{strNextNum}"
        self.flightDataEntries[0].set(strNextNum)

    def FillRandomData(self):
        """
        This function oversees the creation and assignment of random valid data to the Flight Data Entry fields.
        However, the flight number isn't assigned randomly, but instead utilises the SetToFreeFlightNumber function to
        obtain a valid flight number.
        :return:
        """
        # Airline set first so random flight number can be not in use already:
        self.flightDataEntries[3].set(random.choice(self.host.airlineNames))
        # Get next free flight number:
        self.SetToFreeFlightNumber()

        # Get origin/destination as random choice
        airportOptions = self.host.airportNames.copy()
        origin = airportOptions.pop(random.randint(0, len(airportOptions) - 1))  # Removes Origin Airport from list
        destination = airportOptions.pop(random.randint(0, len(airportOptions) - 1))
        self.flightDataEntries[1].set(origin)
        self.flightDataEntries[2].set(destination)

        # Get and then set a random aircraft after retrieving the list of usable aircraft
        for airline in self.host.airlineDataSets:
            if airline[0] == self.flightDataEntries[3].get():
                aircraftList = airline[2:int(len(airline) / 2) + 1]
                self.flightDataEntries[4].set(random.choice(aircraftList))

        # Set Random hours and 15min interval time:
        self.flightDataEntries[5].set(f"{random.randint(0, 23)}:{random.randint(0, 3) * 15}:00")

    def CreateRandomFlightsBatch(self):
        """
        This function is a method for the user to automate the creation of (max 25, min 0) flights utilising random
        data. CreateRandomFlightsBatch utilises FillRandomData and ConstructNewFlight in a loop to repeatedly assign
        random data to the user entry fields, and then construct a flight from that data.
        :return:
        """
        try:  # Ensure num flights is a proper integer
            numFlights = int(self.numFlights.get())
            if numFlights > 25:  # impose limits on max flights (prevents large repeating loops)
                numFlights = 25
            elif numFlights < 0:  # prevent negative value
                raise ValueError
        except ValueError:
            numFlights = 0

        for f in range(numFlights):  # Create the flights using loop
            self.FillRandomData()
            self.ConstructNewFlight()

    def FlightValueSuitableCheck(self, reoccur=True):
        """
        This function determines if the user's entered values for flight construction are valid and acceptable for a
        new Flight object. The function assumes the values are suitable, and attempts to then identify if values break
        the conditions making them unsuitable. This applies to all 6 entry fields (Flight Number, Origin, Destination,
        Airline, Aircraft and Departure Time).
        :param reoccur:
        :return:
        """
        if self.body.winfo_ismapped():  # Only updates if screen is showing
            # Assume values to be suitable, and hence perform checks to see if any values are not
            self.canConstructFlight = True
            for infoBox in self.valueInfoBoxes:
                infoBox.config(bg='green')

            # Ensure flight num entry is a valid integer:
            try:
                if int(self.flightDataEntries[0].get()) < 0:
                    raise ValueError
                if len(self.flightDataEntries[0].get()) > 4:
                    raise ValueError
            except ValueError:
                # flightDataEntry cannot be made into a positive int or is too large
                self.canConstructFlight = False
                self.valueInfoBoxes[0].config(bg='red')

            # Create 0 padded flight num
            paddedFliNum = f"{self.flightDataEntries[0].get()}"
            for i in range(4 - len(paddedFliNum)):
                paddedFliNum = f"0{paddedFliNum}"

            # Check Flight Number by obtaining list of flight numbers currently in use for selected airline:
            for i, airline in enumerate(self.host.airlineDataSets):  # Identify set of airline data to get airline code
                if airline[0] == self.flightDataEntries[3].get():
                    unavailableFlightCodes = []
                    for flight in self.host.allFlights:  # Obtain list of in-use flight Codes
                        unavailableFlightCodes.append(flight.fliCode)

                    fliCode = f"{self.host.airlineDataSets[i][1]}{paddedFliNum}"  # Construct flight's flight Code
                    if fliCode in unavailableFlightCodes or len(self.flightDataEntries[0].get()) > 4:
                        # Code already in use, or was too large
                        self.canConstructFlight = False
                        self.valueInfoBoxes[0].config(bg='red')

            # Check Airports if they are the same and not default values:
            if self.flightDataEntries[1].get() == self.flightDataEntries[2].get():
                self.canConstructFlight = False
                self.valueInfoBoxes[1].config(bg='red')
                self.valueInfoBoxes[2].config(bg='red')

            if self.flightDataEntries[1].get() not in self.host.airportNames:
                self.canConstructFlight = False
                self.valueInfoBoxes[1].config(bg='red')

            if self.flightDataEntries[2].get() not in self.host.airportNames:
                self.canConstructFlight = False
                self.valueInfoBoxes[2].config(bg='red')

            # Check Airline and Aircraft:
            if self.flightDataEntries[3].get() == "Select Airline":  # Ensure value is not equal to default prompt
                self.canConstructFlight = False
                self.valueInfoBoxes[3].config(bg='red')

            if self.flightDataEntries[4].get() == "Select Aircraft":  # Ensure value is not equal to default prompt
                self.canConstructFlight = False
                self.valueInfoBoxes[4].config(bg='red')

            # Check Departure Time is valid Time string:
            try:
                # Attempt to turn string into a time object
                dt.datetime.strptime(self.flightDataEntries[5].get(), "%H:%M:%S")
            except ValueError:
                # Exception Thrown as string unsuited to format
                self.canConstructFlight = False
                self.valueInfoBoxes[5].config(bg='red')

        if reoccur:
            self.host.root.after(1000, lambda: self.FlightValueSuitableCheck())  # performs loop every second

    def ConstructNewFlight(self):
        """
        Constructs a new Flight Object from the data produced within the Create Flight window, either by the user,
        or through the program's own generation. Directly adds the flight to the relevant airports' inbound/outbound
        lists, and to Main's allFlights list.
        :return:
        """
        self.FlightValueSuitableCheck(False)  # Perform check on flight data validity

        # Reject new flight creation if exceed max flights or flight data is invalid
        if not self.canConstructFlight or (len(self.host.allFlights) >= self.host.maxFlights):
            return

        # Get airlineData, aircraftData and index of aircraft/speed
        airlineData, aircraftData, aircraftIndex = [], [], 0
        for i, airline in enumerate(self.host.airlineDataSets):
            if airline[0] == self.flightDataEntries[3].get():
                # Get index of selected Aircraft to match up with aircraft speed
                airlineData = airline
                aircraftData = airline[2:int(len(airline) / 2) + 1]
                for acIndex, aircraft in enumerate(aircraftData):
                    if aircraft == self.flightDataEntries[4].get():
                        # Get Values from airlineData, aircraftData and flightDataEntries:
                        aircraftIndex = acIndex

        # Create 0 padded flight num
        paddedFliNum = f"{self.flightDataEntries[0].get()}"
        for i in range(4 - len(paddedFliNum)):
            paddedFliNum = f"0{paddedFliNum}"

        #Construct Flight and Airline Details:
        fliNum = paddedFliNum
        fliCode = f"{airlineData[1]}{fliNum}"
        fliOrigin = self.flightDataEntries[1].get()
        fliDestination = self.flightDataEntries[2].get()
        fliSpeed = float(airlineData[int(len(airlineData) / 2) + 1:][aircraftIndex])
        fliDist = random.randint(1200, 3500)
        aircraftName = aircraftData[aircraftIndex]
        airlineName = airlineData[0]
        airlineCode = airlineData[1]

        # Convert Departure Time from string to timedelta
        time = dt.datetime.strptime(self.flightDataEntries[5].get(), "%H:%M:%S")
        departureTime = dt.timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)

        # Get approximate Arrival Time
        appxHours = (fliDist / int(fliSpeed))
        appxMins = (appxHours - int(appxHours))*60
        appxSeconds = (appxMins - int(appxMins))*60
        appxFlightTime = dt.timedelta(hours=int(appxHours), minutes=int(appxMins), seconds=int(appxSeconds))
        appxArriveTime = departureTime + appxFlightTime
        if appxArriveTime.days == 1:
            appxArriveTime = appxArriveTime - dt.timedelta(days=1)

        # Create Timetabled arrival time based upon the 15min window that appxArrive is in : 13:32:00 -> 13:45:00
        arriveHour = appxArriveTime.seconds/60/60
        arriveMin = (arriveHour - int(arriveHour))*60
        minWindow = (arriveMin//15)+1
        arrivalTime = dt.timedelta(hours=int(arriveHour), minutes=minWindow * 15)
        if arrivalTime.days == 1:
            arrivalTime = arrivalTime - dt.timedelta(days=1)

        # if program time has already passed the departure time, flight scheduled to depart next day
        if departureTime <= self.host.programTime:
            hasDeparted = False
            isDeparting = False
        else:
            hasDeparted = False
            isDeparting = True

        # Random chane for plane to be late applied:
        if random.randint(0, 100) <= 30:
            fliSpeed *= 0.95  # travel at 95% mov speed
            fliSpeed = round(fliSpeed, 2)

        # Construct new Flight object
        flightDetails = [fliNum, fliCode, fliOrigin, fliDestination, fliSpeed, fliDist]
        airlineDetails = [aircraftName, airlineName, airlineCode]
        timeDetails = [departureTime, arrivalTime, appxArriveTime, "00:00:00", hasDeparted, isDeparting]
        newFlight = Flight(flightDetails, airlineDetails, timeDetails, self.host.dataSearchTerms)
        self.host.allFlights.append(newFlight)  # Add to self.host.allFlights list

        # add to relevant airport's inbound/outbound lists
        for airport in self.host.airports:
            if airport.name == self.flightDataEntries[1].get():
                airport.outboundFlights.append(newFlight)
            elif airport.name == self.flightDataEntries[2].get():
                airport.inboundFlights.append(newFlight)


if __name__ == "__main__":
    Main()
