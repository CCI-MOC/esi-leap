#!/bin/bash

# Function to stop all processes gracefully
function stop_all_processes {
    echo "Stopping all processes..."
    kill -SIGTERM $manager_pid $api_pid
    wait $manager_pid $api_pid
    echo "All processes stopped."
    exit 0
}

# Register the stop_all_processes function to run on SIGTERM signal
trap stop_all_processes SIGTERM

# Start the first process
esi-leap-dbsync create_schema
dbsync_exit_code=$?

# Check if esi-leap-dbsync create_schema was successful
if [ $dbsync_exit_code -ne 0 ]; then
    echo "Failed to create schema. Exiting..."
    exit $dbsync_exit_code
fi

# Start the remaining processes
esi-leap-manager &
manager_pid=$!
esi-leap-api &
api_pid=$!

# Wait for child processes to exit
wait $manager_pid $api_pid
echo "All processes stopped."
