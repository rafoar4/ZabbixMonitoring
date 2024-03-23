def convert_seconds_to_dhms(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return days, hours, minutes, seconds

def calculate_ont_availability(ont_events, ont_type, start_time, total_time_seconds,maintenance_windows):
    
    #stdscr.addstr(row, 0, f"{ont_type} Network Availability:")
    downtime_seconds = 0
    downtime_values = []
    # Sort the events by their start time
    ont_events.sort(key=lambda event: event["int_time"])
    
    current_downtime = None
    if ont_events:
        for event in ont_events:
            event_start_time = event["int_time"]  # Start time of the event
            event_end_time = event["end_time"]  # End time of the event

            # Convert event times to datetime objects
            event_start_time = datetime.datetime.fromtimestamp(int(event_start_time))
            event_end_time = datetime.datetime.fromtimestamp(int(event_end_time))
            
            # Check if the event overlaps with the total time
            if event_start_time < start_time:
                event_start_time = start_time
            if event_end_time > datetime.datetime.now():
                event_end_time = datetime.datetime.now()
            # Calculate downtime for the event
            # Initialize variables to track maintenance window overlap
            overlap_before = False
            overlap_during = False
            overlap_after = False
            # Check if the event overlaps with any maintenance window
            for maintenance_window in maintenance_windows:
                window_start = maintenance_window[0]
                window_end = maintenance_window[1]
                if event_start_time < window_end and event_end_time > window_start:
                    # There is an overlap between the event and the maintenance window
                    overlap_during = True
                    if event_start_time < window_start:
                        overlap_before = True
                    if event_end_time > window_end:
                        overlap_after = True

            # Calculate downtime for the event
            if current_downtime:
                # If there is an ongoing downtime, adjust the end time
                if event_start_time <= current_downtime["end_time"]:
                    current_downtime["end_time"] = event_end_time
                else:
                    
                    if not downtime_values:
                        downtime = (current_downtime["end_time"] - current_downtime["start_time"]).total_seconds()
                        downtime_values.append(downtime)
                        downtime_seconds += downtime
                    current_downtime = {"start_time": event_start_time, "end_time": event_end_time}
                    for maintenance_window in maintenance_windows:
                        window_start = maintenance_window[0]
                        window_end = maintenance_window[1]

                        # Check for overlap with maintenance window
                        if event_start_time < window_end and event_end_time > window_start:
                            # There is an overlap between the event and the maintenance window
                            overlap_start = max(window_start, event_start_time)
                            overlap_end = min(window_end, event_end_time)
                            overlap_seconds = (overlap_end - overlap_start).total_seconds()

                            # Deduct overlap time from downtime
                            current_downtime["start_time"] = overlap_end
                            downtime_seconds += overlap_seconds
                    # Calculate downtime for the event
                    
                    downtime = (event_end_time - current_downtime["start_time"]).total_seconds()
                    downtime_seconds += downtime
                    downtime_values.append(downtime)
            
            else:
                current_downtime = {"start_time": event_start_time, "end_time": event_end_time}
            # Output the event details including maintenance window overlap
            
            """ stdscr.addstr(row, 30, f"Problem: {event['name']}")
            stdscr.addstr(row, 70, f"Problem Duration: {event['problem_duration']}")
        
            if overlap_before:
                stdscr.addstr(row, 140, "Overlap Before Maintenance Window")
            if overlap_during:
                stdscr.addstr(row, 160, "Overlap During Maintenance Window")
            if overlap_after:
                stdscr.addstr(row, 190, "Overlap After Maintenance Window")

            row += 2 """
        
    # Calculate uptime based on downtime and total time
    uptime_seconds = total_time_seconds - downtime_seconds
    

    # Calculate network availability as a percentage
    network_availability = (uptime_seconds / total_time_seconds) * 100

    print(f"{ont_type} Uptime: {uptime_seconds} seconds")
    
    print(f"{ont_type} Downtime: {downtime_seconds} seconds")
    
    print(f"{ont_type} Total Time: {total_time_seconds} seconds")
    
    print(f"{ont_type} Network Availability: {network_availability:.5f}%")
    
    # Display all downtime values
    if downtime_values:
        print(f"{ont_type} Downtime Values (in seconds): {downtime_values}")


def calculate_ont_network_availability(black_ont, white_ont,start_time,current_time):
    
    total_time = current_time - start_time
    total_time_seconds = total_time.total_seconds()
    # Read maintenance windows from the file
    maintenance_windows = []
    #print(total_time_seconds)
    if os.path.isfile(MAINTENANCE_FILE):
        with open(MAINTENANCE_FILE, "r") as file:
            for line in file:
                #print(line)
                start_time_w, end_time_w = line.strip().split(",")
                start_time_w = datetime.datetime.strptime(start_time_w, "%Y-%m-%d %H:%M:%S")
                end_time_w = datetime.datetime.strptime(end_time_w, "%Y-%m-%d %H:%M:%S")
                maintenance_windows.append((start_time_w, end_time_w))
    maintenance_window_seconds = []
    #print(maintenance_windows)
    # Subtract the seconds of maintenance windows from total_time_seconds
    for maintenance_window in maintenance_windows:
        window_start = maintenance_window[0]
        window_end = maintenance_window[1]
        overlap_seconds=0
        if window_start < current_time and window_end > start_time:
            # There is an overlap between the maintenance window and the total time
            overlap_start = max(window_start, start_time)
            overlap_end = min(window_end, current_time)
            overlap_seconds = (overlap_end - overlap_start).total_seconds()
            #print(overlap_seconds) 
            maintenance_window_seconds.append(overlap_seconds)
    total_time_seconds -= overlap_seconds
    #print(total_time_seconds)
    # Calculate network availability for black_ont events
    calculate_ont_availability(black_ont, "Black_ONT", start_time, total_time_seconds,maintenance_windows)
    print("\n")
    # Calculate network availability for white_ont events
    calculate_ont_availability(white_ont, "White_ONT", start_time, total_time_seconds,maintenance_windows)
    # Display the seconds from each maintenance window
    if maintenance_window_seconds:
        print("\n")
        print("Maintenance Window Seconds:")
        for i, seconds in enumerate(maintenance_window_seconds):
            print(f"Window {i + 1}: {seconds} seconds")


def calculate_network_availability(zapi,option):
    print("Calculating Network Availability:")
    selected_events = []
    try:
        # Define the date filter as 09/10/2023
        date_filter = datetime.datetime(2023, 10, 9)
        # Define the problem severity as "Disaster" (severity level 5)
        severity_filter = 5
        start_time = datetime.datetime(2023, 10, 9, 0, 0)
        # Get the current time
        current_time = datetime.datetime.now()

        # Calculate the total time duration (from start_time to current_time)
        total_time = current_time - start_time
        total_time_seconds = total_time.total_seconds()
        events = zapi.event.get(
            source=0,  # 0 means events generated by triggers
            object=0,  # 0 means events associated with hosts
            value=1,  # 1 means events with problems
            time_from=int(date_filter.timestamp()),  # Convert to Unix timestamp
            priority=severity_filter,  # Filter by severity level
            output=["eventid", "clock", "name", "severity", "r_eventid"],
            selectHosts=["host"],
            selectRelatedObject=["r_eventid", "clock"],  # Select recovery event info
            sortfield=["clock"],
            sortorder="DESC",
        )
        for event in events:
            event_id = event["eventid"]
            event_time = datetime.datetime.fromtimestamp(int(event["clock"])).strftime("%Y-%m-%d %H:%M:%S")
            event["int_time"]=str(event["clock"])
            event_name = event["name"]
            event_severity = event["severity"]
            if "hosts" in event and len(event["hosts"]) > 0:
                host_name = event["hosts"][0]["host"]
            else:
                host_name = "N/A"
            r_eventid = event.get("r_eventid", None)
            r_event_time = "N/A"  # Default value for recovery time
            problem_duration = "N/A"  # Default value for problem duration
            if r_eventid is not None:
                # If there is a recovery event, retrieve its time
                recovery_event = zapi.event.get(
                    eventids=[r_eventid],
                    output=["clock"]
                )
                if recovery_event:
                    r_event_time = datetime.datetime.fromtimestamp(int(recovery_event[0]["clock"])).strftime("%Y-%m-%d %H:%M:%S")
                    event_time_obj = datetime.datetime.fromtimestamp(int(event["clock"]))
                    recovery_time_obj = datetime.datetime.fromtimestamp(int(recovery_event[0]["clock"]))
                    duration = recovery_time_obj - event_time_obj
                    problem_duration = str(duration)   
                    event["problem_duration"] = str(duration)  
                    event["time_cl"]=str(event_time_obj)     
                    event["end_time"]=str(recovery_event[0]["clock"])
            if host_name in ["OLT_TPLINK", "Router"]:
                selected_events.append(event)
            black_ont = []
            white_ont = []
            for event in selected_events:
                event_name = event["name"]
                #print(event_name)
                # Check for the presence of "white" or "black" in the event_name
                if "white" not in event_name.lower():
                    black_ont.append(event)
                if "black" not in event_name.lower():
                    white_ont.append(event)
        if option=="":
            # Calculate the total time duration (from start_time to current_time)
            calculate_ont_network_availability(black_ont, white_ont,start_time,current_time) 
        if option=="option2":
            return black_ont,white_ont
        if not events:
            print("No 'Disaster' events found after 09/10/2023.")
        
    except Exception as e:
        print(f"Error fetching information: {str(e)}")
    input("Press Enter to return to the main menu...")


from pyzabbix import ZabbixAPI
import datetime
import os

MAINTENANCE_FILE = "maintenance_dates.txt"
zabbix_url = 'http://172.27.228.162/zabbix/'

def calculate_network_availability_option(zapi):
    print("Calculating Network Availability:")

    try:
        current_date = datetime.datetime.now()
        # Calculate the start of the week
        start_of_week = current_date - datetime.timedelta(days=current_date.weekday())

        # Set the time to midnight
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        #print(start_of_week)
        date_filter = start_of_week
        severity_filter = 5
        start_time = start_of_week
        current_time = datetime.datetime.now()

        total_time = current_time - start_time
        total_time_seconds = total_time.total_seconds()
        events = zapi.event.get(
            source=0,
            object=0,
            value=1,
            time_from=int(date_filter.timestamp()),
            priority=severity_filter,
            output=["eventid", "clock", "name", "severity", "r_eventid"],
            selectHosts=["host"],
            selectRelatedObject=["r_eventid", "clock"],
            sortfield=["clock"],
            sortorder="DESC",
        )
        selected_events = []
        for event in events:
            event_time = datetime.datetime.fromtimestamp(int(event["clock"]))
            event["int_time"] = str(event["clock"])
            if "hosts" in event and len(event["hosts"]) > 0:
                host_name = event["hosts"][0]["host"]
            else:
                host_name = "N/A"
            r_eventid = event.get("r_eventid", None)
            if r_eventid is not None:
                recovery_event = zapi.event.get(
                    eventids=[r_eventid],
                    output=["clock"]
                )
                if recovery_event:
                    event["end_time"] = str(recovery_event[0]["clock"])

            if host_name in ["OLT_TPLINK", "Router"]:
                selected_events.append(event)

        black_ont = []
        white_ont = []
        for event in selected_events:
            event_name = event["name"]
            if "white" not in event_name.lower():
                black_ont.append(event)
            if "black" not in event_name.lower():
                white_ont.append(event)

        # Run the calculation based on provided data
        calculate_ont_network_availability(black_ont, white_ont, start_time, current_time)

        if not events:
            print("No 'Disaster' events found after 09/10/2023.")

    except Exception as e:
        print(f"Error fetching information: {str(e)}")

    
# Connect to Zabbix API and invoke option 2 for Network Availability calculation
def run_option_2():
    try:
        zapi = ZabbixAPI(zabbix_url)
        zapi.login(user="Admin", password="zabbix")
        print(f"Logged in successfully at {datetime.datetime.now()} ")
        print("\n")
        calculate_network_availability_option(zapi)
        
    except Exception as e:
        print(f"Error: {str(e)}")

# Run the function to simulate the option 2 execution
run_option_2()
