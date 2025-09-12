/*!
 * Copyright (c) 2024 Jörgen Karlsson
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
'use strict';

module.exports = function (RED) {
    const net = require('net');
    const LogHelper  = require('./loghelper');

    class TcpServerNode {
        constructor(config) {
            RED.nodes.createNode(this, config);0
            this.logger = new LogHelper(this, config.debug);
            this.clients = new Map(); // To keep track of connected clients
            this.datatype = config.datatype || 'utf8';
            this.server = null;
            this.keepAliveTimeout = config.keepAliveTimeout !== undefined ? parseInt(config.keepAliveTimeout, 10) : 6000;
            this.socketTimeout = config.socketTimeout !== undefined ? parseInt(config.socketTimeout, 10) : 60000;
            this.logger.info(`Server Configuration: Keep-Alive Timeout: ${this.keepAliveTimeout} ms, Socket Timeout: ${this.socketTimeout} ms, Datatype ${this.datatype}`);


            this.on('input', (msg, send, done) => {
                let action = RED.util.evaluateNodeProperty(config.action, config.actionType, this, msg);
                let port = parseInt(RED.util.evaluateNodeProperty(config.port, config.portType, this, msg), 10);
                let data = RED.util.evaluateNodeProperty(config.write, config.writeType, this, msg);
                this.logger.debug("action: " + action + " port " + port);
                this.logger.debug( "port " + config.port);
                this.logger.debug( "msg " + JSON.stringify(msg));

                switch (action) {
                    case 'open':
                        this.open(port, msg, done);
                        break;
                    case 'write':
                        this.write(msg, data, done);
                        break;
                    case 'broadcast':
                        this.broadcast(data, done);
                        break;
                    case 'close':
                        this.close(done);
                        break;
                    default:
                        this.logger.warning(`Unrecognized action: ${action}`);
                        done();
                }
            });

            this.on('close', (done) => {
                this.close(done);
            });

        }

        doDone(error = null){
            if (this.done && typeof this.done === 'function') {
                this.done(error); // Call 'done' to complete the node operation
                this.done = null;
            }
        }
        open(port, msg, done) {
            if (this.server !== null) {
                this.logger.warning("Server already running.");
                if (done) done(); // Indicate that the operation is complete
                return;
            }
        
            this.server = net.createServer();
            this.server.on('connection', (socket) => {
                // New client connection has been established
                const clientId = `${socket.remoteAddress}:${socket.remotePort}`;
                this.logger.info(`Client connected: ${clientId}`);
                this.clients.set(clientId, socket); // Track this new client
                this.status({fill: "green", shape: "dot", text: `Listening, ${this.clients.size} connections`})
                if (this.keepAliveTimeout > 0) {
                    socket.setKeepAlive(true, this.keepAliveTimeout);
                }
                if (this.socketTimeout > 0) {
                    socket.setTimeout(this.socketTimeout);
                }
                
                socket.on('timeout', () => {
                    this.logger.info(`Connection timeout: ${clientId}`);
                    socket.end(); // Close the connection
                    this.clients.delete(clientId); // Remove the client from tracking
                    if (this.server) {
                        // during closing, sockets can close after the server is gone, this might be confusing 
                        this.status({fill: "green", shape: "dot", text: `Listening, ${this.clients.size} connections`})
                    }
                });
        
                socket.on('data', (data) => {
                    if (this.socketTimeout > 0) {
                        socket.setTimeout(this.socketTimeout);// reset timeout
                    }
                    let parsedData = data.toString(this.datatype);
                    this.logger.debug("Got data :" + parsedData);
                    this.send({payload: parsedData, topic: clientId});
                });
        
                socket.on('close', () => {
                    this.clients.delete(clientId); // Remove the client from tracking
                    this.logger.info(`Client disconnected: ${clientId}`);
                    if (this.server) {
                        // during closing, sockets can close after the server is gone, this might be confusing 
                        this.status({fill: "green", shape: "dot", text: `Listening, ${this.clients.size} connections`})
                    }
                });
        
                socket.on('error', (err) => {
                    this.logger.error(`Error from client ${clientId}: ${err.message}`);
                });
            });

            this.server.on('listening', () => {
                this.logger.debug(`TCP Server listening`);
            });

            this.server.on('close', () => {
                this.logger.info('Server has closed');
                this.status({fill: "red", shape: "dot", text: "closed"});
            });

            this.server.on('error', (err) => {
                this.logger.error(`Server error: ${err.message}`);
                if (done) done(err);
            });
        
            this.server.listen(port, () => {
                this.logger.info(`TCP Server listening on port ${port}`);
                this.status({ fill: "green", shape: "dot", text: `Listening on port ${port}` });
                if (done) done(); // Successfully started the server
            });
        }
        
 
        write(msg, data, done) {
            this.done = done;
            const client = msg.topic;
            if (client && this.clients.has(client)) {
                this.logger.debug(`Sending to client ${client}: ${data}`);
                const clientSocket = this.clients.get(client);
                try {
                    clientSocket.write(data, this.datatype); 
                    this.logger.debug(`Data sent to client ${client}`);
                    this.doDone();
                } catch (error) {
                    this.logger.error(`Error sending data to client ${client}: ${error.message}`);
                    this.doDone(error); 
                }
            } else {
                this.logger.warning(`Client ${client} not found or topic not provided`);
                if (done) done(new Error(`Client ${client} not found or topic not provided`));
            }
        }


        close(done) {
            // Close all client connections
            this.status({fill: "yellow", shape: "dot", text: `Closing ${this.clients.size} connections`})
            this.clients.forEach((socket, clientId) => {
                this.logger.info(`Closing connection for client: ${clientId}`);
                socket.end(); 
                this.clients.delete(clientId); 
                this.status({fill: "yellow", shape: "dot", text: `Closing ${this.clients.size} connections`})
            });
        
            // Check if the server is initialized and listening
            if (this.server) {
                this.server.close(() => {
                    this.logger.info("TCP Server has been closed.");
                    this.status({fill: "red", shape: "dot", text: "closed"});
                    this.server = null;
                    if (done) done(); // Callback to signal Node-RED that the operation is complete
                });
            } else {
                if (done) done();
            }
        }
        
    }

    RED.nodes.registerType("tcp-server", TcpServerNode);
};
