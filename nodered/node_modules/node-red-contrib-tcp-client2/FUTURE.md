## Ideas for the future

- Improve readme for TCP Server
- Separate control and data input. Use a checkbox in gui for that.
- Separate control and data output. Use a checkbox to enable the separation.
- Separate data node for the server, mimic built in. Always writing msg.payload or configurable. 
- Broadcast in tcp client. Send message to all clients.
- Autostart for server, so it starts listening directly when node red starts. (Easy to do with inject node only)
- Autoconnect for client, so it trys to connect if data arrives and it is not connected (and has the config).
- Progressive timeout for client.