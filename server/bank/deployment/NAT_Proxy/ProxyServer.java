// Copyright (c) 2018 by SMU

import java.io.*;
import java.net.*;
import java.util.*;
 
/**
 * This class provides a relatively simple multi-threaded reverse proxy service.
 * The main() method starts up the server.
 **/
public class ProxyServer {

    ConnectionManager connectionManager; // The ConnectionManager object
    ThreadGroup threadGroup;             // The threadgroup for all our threads
    int maxConnections = 100;             // Maximum number of connections allowed
    String host;                         // host of this proxy server
    int remoteport;                      // remoteport of the actual backend server

    /**
     * Create a ProxyServer object as specified by the command-line arguments.
     **/
    public static void main(String[] args) {
        try {
            // Check number of args.  Must be a multiple of 4 and > 0.
            if ((args.length == 0) || (args.length % 3 != 0))
                throw new IllegalArgumentException("Wrong number of arguments");
            
            // Loop through the arguments parsing (host, remoteport, localport)
            // tuples.  Create a ProxyServer object.
            int i = 0;
            while(i < args.length) {
                String host = args[i++];
                int remoteport = Integer.parseInt(args[i++]);
                int localport = Integer.parseInt(args[i++]);
                ProxyServer ps = new ProxyServer(host, remoteport, localport);
            }
        }
        catch (Exception e) {  // Print an error message if anything goes wrong.
            System.err.println(e);
            System.err.println("Usage: java ProxyServer " +
                               "<host> <remoteport> <localport> ...");
            System.exit(1);
        }
    }
    
    /**
     * Constructor for the ProxyServer object.
     **/
    public ProxyServer(String host, int remoteport, int localport) throws IOException {
        this.host = host;
        this.remoteport = remoteport;
        
        System.out.println("Starting Server");
        threadGroup = new ThreadGroup("Server");
        connectionManager = new ConnectionManager(threadGroup, maxConnections);
        connectionManager.start();
        
        // Create a Listener object to listen for connections on the port
        Listener listener = new Listener(threadGroup, localport);
                
        // Start the listener running.
        listener.start();
		
		System.out.println("Starting listening service on port " + localport);

    }
    
    /** The server invokes this method when a client connects. */
    public void serve(InputStream in, OutputStream out, Socket client) {
        
        final InputStream from_client = in;
        final OutputStream to_client = out;
        final InputStream from_server;
        final OutputStream to_server;
		
        System.out.println("Incoming requests...connected to CLIENT " + client.getInetAddress().getHostAddress() + ":" + client.getPort() + " on local port " + client.getLocalPort() + "." );
        
        // Try to establish a connection to the specified server and port
        // and get sockets to talk to it.  Tell our client if we fail.
        Socket server;
        try {
            server = new Socket(host, remoteport);
	    System.out.println("Outgoing requests...connected to Server " + host + ":" + remoteport + " on remote port " + server.getLocalPort() + "." );

            from_server = server.getInputStream();
            to_server = server.getOutputStream();
        }
        catch (Exception e) {
            PrintWriter pw = new PrintWriter(new OutputStreamWriter(out));
            pw.println("Proxy server could not connect to " + host + ":" + remoteport);
            pw.flush();
            pw.close();
            try { in.close(); } catch (IOException ex) {}
            return;
        }
        
        // Create an array to hold two Threads.  
        final Thread[] threads = new Thread[2];
        
        // Define and create a thread to transmit bytes from client to server
        Thread c2s = new Thread() {
            public void run() {
                byte[] buffer = new byte[2048];
                int bytes_read;
                try {
                    while((bytes_read = from_client.read(buffer)) != -1) {
                        to_server.write(buffer, 0, bytes_read);
                        to_server.flush();
                    }
                }
                catch (IOException e) {}
                
                // if the client closed its stream to us, we close our stream
                // to the server.
                try { to_server.close(); } catch (IOException e) {}
            }
        };
        
        // Define and create a thread to copy bytes from server to client.
        Thread s2c = new Thread() {
            public void run() {
                byte[] buffer = new byte[2048];
                int bytes_read;
                try {
                    while((bytes_read = from_server.read(buffer)) != -1) {
                        to_client.write(buffer, 0, bytes_read);
                        to_client.flush();
                    }
                }
                catch (IOException e) {}
                
                // if the server closed its stream to us, we close our stream
                // to the client.
                try { to_client.close(); } catch (IOException e) {}
            }
        };
        
        // Store the threads into the final threads[] array, so that the
        // anonymous classes can refer to each other.
        threads[0] = c2s; threads[1] = s2c;
        
        // start the threads
        c2s.start(); s2c.start();
        
        // Wait for them to exit
        try { c2s.join(); s2c.join(); } catch (InterruptedException e) {}
    }
    
    // The nested classes below are implemented for the ProxyServer to listen to incoming requests,
    // create and manage the connections.
    
    /**
     * This nested class provides the listener to listen to incoming socket requests.
     **/
    public class Listener extends Thread {
        ServerSocket listen_socket;   // The socket we listen for connections on
        int port;                     // The port we're listening on

        boolean stop = false;         // Whether we've been asked to stop
        
        /**
         * The Listener constructor creates a ServerSocket to listen for connections
         * on the specified port.  
         **/
        //public Listener(ThreadGroup group, int port)
        public Listener(ThreadGroup group, int port) throws IOException {

            super(group, "Listener:" + port);
            listen_socket = new ServerSocket(port);
            
            // give the socket a non-zero timeout so accept() can be interrupted
            listen_socket.setSoTimeout(600000);
            this.port = port;
        }
        
        /** This is the nice way to get a Listener to stop accepting connections */
        public void pleaseStop() {
            this.stop = true;   // set the stop flag
            this.interrupt();   // and make the accept() call stop blocking
        }
        
        /**
         * A Listener is a Thread, and this is its body.
         * Wait for connection requests, accept them, and pass the socket on
         * to the ConnectionManager object of this server
         **/
        public void run() {
            while(!stop) {      // loop until we're asked to stop.
                try {
                    Socket client = listen_socket.accept();
                    connectionManager.addConnection(client);
                }
                catch (InterruptedIOException e) {}
                catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
    }
    
    /**
     * This nested class  manages client connections for the server.
     **/
    public class ConnectionManager extends Thread {
        int maxConnections;  // The maximum number of allowed connections
        Vector<Connection> connections;  // The current list of connections
        
        /**
         * Create a ConnectionManager in the specified thread group to enforce
         * the specified maximum connection limit.  Make it a daemon thread so
         * the interpreter won't wait around for it to exit.
         **/
        public ConnectionManager(ThreadGroup group, int maxConnections) {
            super(group, "ConnectionManager");
            this.setDaemon(true);
            this.maxConnections = maxConnections;
            connections = new Vector<Connection>(maxConnections);
            System.out.println("Starting connection manager.  Max connections: " + maxConnections);
            
        }
        
        /**
         * This is the method that Listener objects call when they accept a
         * connection from a client.  It either creates a Connection object
         * for the connection and adds it to the list of current connections,
         * or, if the limit on connections has been reached, it closes the
         * connection.
         **/
        synchronized void addConnection(Socket s) {
            // If the connection limit has been reached
            if (connections.size() >= maxConnections) {
                try {
                    PrintWriter out = new PrintWriter(s.getOutputStream());
                    // Then tell the client it is being rejected.
                    out.println("Connection refused; " +
                                "server has reached maximum number of clients.");
                    out.flush();
                    // And close the connection to the rejected client.
                    s.close();

                    System.out.println("Connection refused to " + s.getInetAddress().getHostAddress() + ":" + s.getPort() + ": max connections reached.");
                } catch (IOException e) {//log(e);
                    e.printStackTrace();
                }
            }
            else {
                // Otherwise, if the limit has not been reached
                // Create a Connection thread to handle this connection
                Connection c = new Connection(s);
                
                // Add it to the list of current connections
                connections.addElement(c);
                
                // And start the Connection thread running to provide the service
                c.start();
            }
        }
        
        /**
         * A Connection object calls this method just before it exits.
         * This method uses notify() to tell the ConnectionManager thread
         * to wake up and delete the thread that has exited.
         **/
        public synchronized void endConnection() { this.notify(); }
        
        /** Change the current connection limit */
        public synchronized void setMaxConnections(int max) { maxConnections=max; }
        
        /**
         * The ConnectionManager is a thread, and this is the body of that
         * thread.  While the ConnectionManager methods above are called by other
         * threads, this method is run in its own thread.  The job of this thread
         * is to keep the list of connections up to date by removing connections
         * that are no longer alive. 
         **/
        public void run() {
            while(true) {  // infinite loop
                // Check through the list of connections, removing dead ones
                for(int i = 0; i < connections.size(); i++) {
                    Connection c = (Connection)connections.elementAt(i);
                    if (!c.isAlive()) {
                        connections.removeElementAt(i);
                        System.out.println("Connection to " + c.client.getInetAddress().getHostAddress() + ":" + c.client.getPort() + " closed.");
                    }
                }
                // Now wait to be notify()'d that a connection has exited
                // When we wake up we'll check the list of connections again.
                try { synchronized(this) { this.wait(); } }
                catch(InterruptedException e) {}
            }
        }
    }
    
    /**
     * This nested class is a subclass of Thread that handles an individual connection
     * between a client and the proxy server.  
     **/
    public class Connection extends Thread {
        Socket client;     // The socket to talk to the client through
         
        /**
         * This constructor just saves the client state and calls the superclass
         * constructor to create a thread to handle the connection. 
         **/
        public Connection(Socket client) {
            
            super("Server.Connection:" + client.getInetAddress().getHostAddress() +
                  ":" + client.getPort()); 
            this.client = client;
        }
        
        /**
         * Pass the client input and output streams to the
         * serve() method of the specified Service object.  
         **/
        public void run() {
            try {
                InputStream in = client.getInputStream();
                OutputStream out = client.getOutputStream();
                serve(in,out, client);
            }
            catch (IOException e) {
                e.printStackTrace();
            }
            finally { connectionManager.endConnection(); }
        }
    }
}
