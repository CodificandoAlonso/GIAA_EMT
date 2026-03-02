import pandas as pd
import sys


def format_string_list(list_input):
    ret_str = ""
    for item in list_input:
        ret_str += f"\t- {item}\n"

    return ret_str





class Allocation:

    def __init__(self, data1, data2, day: str):
        self.only_day_data = None
        self.buses = []
        self.allocation = {}
        self.allocation_per_timeslot = {}
        self.data1 = pd.read_csv(data1) if not isinstance(data1, pd.DataFrame) else data1
        self.data2 = pd.read_csv(data2) if not isinstance(data2, pd.DataFrame) else data2
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
        self.only_day_data1 = self.data1[self.data1["EventDate"] == self.__day]
        self.only_day_data2 = self.data2[self.data2["EventDate"] == self.__day]

        self.buses = self.only_day_data1["LogicVehicle"].unique()

        stop_code_1 = "2646"
        stop_code_2 = "5727"

        for bus in self.buses:
            self.allocation[bus] = []
            itinerary = self.only_day_data1[self.only_day_data1["LogicVehicle"] == bus]
            itinerary_turnaround = self.only_day_data2[self.only_day_data2["LogicVehicle"] == bus]

            # Find absolute earliest EventTime across both datasets for this bus
            earliest_time = None
            earliest_source = None
            earliest_row = None

            for idx, row in itinerary.iterrows():
                if earliest_time is None or row.EventTime < earliest_time:
                    earliest_time = row.EventTime
                    earliest_source = stop_code_1
                    earliest_row = row

            for idx, row in itinerary_turnaround.iterrows():
                if earliest_time is None or row.EventTime < earliest_time:
                    earliest_time = row.EventTime
                    earliest_source = stop_code_2
                    earliest_row = row

            # Case 2: earliest record has EventTime != EventTime.1 → hidden departure from opposite stop
            if earliest_row is not None and earliest_row.EventTime != earliest_row["EventTime.1"]:
                opposite = stop_code_2 if earliest_source == stop_code_1 else stop_code_1
                self.allocation[bus].append([earliest_row.EventTime, opposite])

            # Case 1: all records where EventTime == EventTime.1 → confirmed departures
            for idx, row in itinerary.iterrows():
                if row.EventTime == row["EventTime.1"]:
                    self.allocation[bus].append([row.EventTime, stop_code_1])

            for idx, row in itinerary_turnaround.iterrows():
                if row.EventTime == row["EventTime.1"]:
                    self.allocation[bus].append([row.EventTime, stop_code_2])


    
    
    
    
    

    def ordered_allocation(self):
        for i in range(5,24):
            self.allocation_per_timeslot[i] = 0

        for idx, bus in self.only_day_data1.iterrows():
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
            import json
            output = {}
            for bus, departures in self.allocation.items():
                # Sort by departure time, then build [stop_code, departure_time] pairs
                sorted_deps = sorted(departures, key=lambda x: x[0])
                output[str(bus)] = [[dep[1], dep[0]] for dep in sorted_deps]


            with open("../../GAMA/src/TEST_MOBILITY/includes/INPUTS/input_data_buses.json", "w") as f:
                json.dump(output,f, indent=2)

            return json.dumps(output, indent=2)
        return None




if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usa la instrucciones python3 obtain_allocation.py <data> <data2> <day>")
    test = Allocation(data1=sys.argv[1],data2= sys.argv[2], day=sys.argv[3])
    print(f"LogicBus: {test:TimeSeries}")
