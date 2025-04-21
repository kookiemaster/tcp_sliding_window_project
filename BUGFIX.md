# TCP Sliding Window Protocol Implementation - Bug Fix

This update addresses a critical bug in the server-client communication protocol that was causing "Invalid JSON data received" errors during the initial connection handshake.

## Bug Description

The server was attempting to parse all incoming data as JSON, including the initial "network" string sent by the client during connection establishment. This caused a JSON parsing error since "network" is not valid JSON.

## Fix Implementation

1. Modified the server's `handle_client` method to:
   - First receive and process the initial string from the client
   - Log the initial message for debugging
   - Then send the "Connection setup success" message
   - Only after that enter the JSON processing loop

2. Created a start.sh script that:
   - Kills any existing processes on port 12345 to avoid conflicts
   - Installs the fixed server implementation
   - Starts the server in the background
   - Waits for server initialization
   - Starts the client
   - Provides clear status messages throughout execution

## How to Run

Simply execute the start.sh script:

```bash
./start.sh
```

This will automatically:
1. Install the fixed server implementation
2. Start the server on port 12345
3. Start the client to connect to the server
4. Generate visualizations in the output directory

## Technical Details

The root cause of the bug was a protocol mismatch between client and server:

- The client correctly sends "network" as its first message
- The server was expecting JSON data immediately
- The fix ensures the server properly handles the initial string before expecting JSON

This update maintains all the original functionality while fixing the communication protocol issue.
