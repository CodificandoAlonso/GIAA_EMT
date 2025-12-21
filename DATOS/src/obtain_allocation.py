import pandas as pd
import numpy as np
import sys


def format_string_list(list_input):
    ret_str = ""
    for item in list_input:
        ret_str += f"\t- {item}\n"

    return ret_str





class Allocation:

    def __init__(self, data, day: str):
        self.buses = []
        self.allocation = {}
        self.allocation_per_timeslot = {}
        self.data = pd.read_csv(data) if not isinstance(data, pd.DataFrame) else data
        self.__day = day
        self.calculate_allocation()
        self.ordered_allocation()




    @property
    def day(self):
        return self.__day


    @day.setter
    def day(self, value):
        self.__day = value
        self.buses = []
        self.allocation = {}
        self.allocation_per_timeslot = {}
        self.calculate_allocation()
        self.ordered_allocation()




    def calculate_allocation(self):
        self.only_day_data = self.data[self.data["EventDate"] == self.__day]
        self.buses = self.only_day_data["LogicVehicle"].unique()
        for bus in self.buses:
            self.allocation[bus] = []
            itinerary = self.only_day_data[self.only_day_data["LogicVehicle"] == bus]
            for idx, row in itinerary.iterrows():
                self.allocation[bus].append(row.EventTime)
    
    
    
    
    

    def ordered_allocation(self):
        for i in range(5,24):
            self.allocation_per_timeslot[i] = 0

        for idx, bus in self.only_day_data.iterrows():
            self.allocation_per_timeslot[bus.TimeSlot] += 1

    def __str__(self):
        return f"Class containing the Allocation of {self.__day} events"




    def __format__(self, spec):
        """

        :param spec: Can be:
        - "logicBus" to have all the info about how many different logic buses there are distributed, and when they depart the header stop
        - "TimeSeries" to have a key, value output where it get shown the logic bus and the departure time ordered by daytime
        :return: The formatted string depending of the spec parameter
        """
        if spec not in ["LogicBus", "TimeSeries"]:
            raise ValueError("Spec must be either 'logicBus' or 'TimeSeries'")
        return_str = ""
        if spec == "LogicBus":
            return_str += f"For day: {self.__day}, we have {len(self.buses)} different Logical Buses\n\n"
            for key, value in self.allocation.items():
                return_str += f" The bus {key}, has the following Exit Times from Header Stop:\n{format_string_list(value)}\n"
            return return_str

        if spec == "TimeSeries":
            return_str += f"For day: {self.__day}, we have {sum(len(v) for v in self.allocation.values())} different header stop departures\n\n"
            time_to_bus = {}
            for bus, times in self.allocation.items():
                for time in times:
                    time_to_bus[time] = bus
            ordered = dict(sorted(time_to_bus.items(), key=lambda x: x[0]))

            for time, bus in ordered.items():
                return_str += f"\t- {time}: Bus {bus}\n"

            return return_str

        return None




if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usa la instrucciones python3 obtain_allocation.py <data> <day>")
    test = Allocation(data=sys.argv[1], day=sys.argv[2])
    print(test)
    print(f"{test:TimeSeries}")