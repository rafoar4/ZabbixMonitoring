#!/bin/bash

# Get the current date
current_date=$(date +"%Y-%m-%d")

# Check if it's the end of the month
end_of_month=$(date -d "$(date -d '+1 month' +'%Y-%m-01') - 1 day" +'%d')

# Run the Python script for the specified options
if [ "$(date +%H:%M)" == "23:59" ]; then
    # Run the script for the daily report at 23:59
    python3 daily_task.py > "daily_report_${current_date}.txt"
    python3 create_graph_reports.py daily "daily_report_${current_date}.txt"
fi

if [ "$(date +%u)" == 7 ] && [ "$(date +%H:%M)" == "23:59" ]; then
    # Run the script for the weekly report on Sundays at 23:59
    python3 weekly_task.py > "weekly_report_${current_date}.txt"
    python3 create_graph_reports.py weekly "weekly_report_${current_date}.txt"
fi

if [ "$end_of_month" == "01" ] && [ "$(date +%H:%M)" == "23:59" ]; then
    # Run the script for the monthly report at the end of the month at 23:59
    python3 monthly_task.py > "monthly_report_${current_date}.txt"
    python3 create_graph_reports.py monthly "monthly_report_${current_date}.txt"
fi
