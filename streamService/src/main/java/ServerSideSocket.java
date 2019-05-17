import com.mongodb.*;
import com.mongodb.util.JSON;


import java.net.*;
import java.io.*;
import java.util.LinkedList;
import java.util.List;

public class ServerSideSocket {
    private MongoClient mongoClient;
    private DBCollection collection;
    private String[] formatFields;

    private final int queueСapacity = 10;
    List<boolean[]> samplesState;

    ServerSideSocket(){
        try {
            mongoClient = new MongoClient();
        } catch (UnknownHostException e){
            e.printStackTrace();
        }
        DB tmpBase = mongoClient.getDB("ExpBase");
        collection = tmpBase.getCollection("Samples");
        samplesState = new LinkedList<>();
    }

    private boolean validateJson(DBObject sample) throws Exception { // true if client said exp is finished
        for(int i = 0; i < formatFields.length; i++) {
           if(!sample.containsField(formatFields[i])) {
               if(sample.containsField("finish") && sample.get("finish").equals("yes"))
                   return true;
               throw new Exception("Bad data");
           }
        }
        return false;
    }

    public void run() {
        try {
            int serverPort = 4020;
            ServerSocket serverSocket = new ServerSocket(serverPort);

            while(true) {
                System.out.println("Waiting for client on port " + serverSocket.getLocalPort() + "...");
                new serverInstance(serverSocket.accept()).start();
            }
        } catch(IOException e) {
            e.printStackTrace();
        }
    }
    public class serverInstance extends Thread {
        private Socket server;
        public serverInstance(Socket socket) {
            this.server = socket;
        }

        public void start() {
            boolean sessionFinished = false;
            try {
                PrintWriter toClient = new PrintWriter(server.getOutputStream(), true);
                BufferedReader fromClient = new BufferedReader(new InputStreamReader(server.getInputStream()));

                String line = fromClient.readLine();
                formatFields = line.substring(1,line.length() - 1).split(", ");

                toClient.println("Connection succeeded");

                int messageCount = 0;
                boolean[] state = new boolean[queueСapacity];
                for (int i = 0; i < queueСapacity; i++) state[i] = false;

                while (true) {
                    line = fromClient.readLine();
                    System.out.println("Server received: " + line);
                    messageCount++;

                    if(messageCount % queueСapacity == 1) {
                        samplesState.add(state);
                        state = new boolean[queueСapacity];
                        for (int i = 0; i < queueСapacity; i++) state[i] = false;
                    }

                    try {
                        DBObject sample = (DBObject)JSON.parse(line);
                        sessionFinished = validateJson(sample);

                        if(!sessionFinished) {
                            collection.insert(sample);
                            state[Integer.parseInt(sample.get("id").toString()) % queueСapacity] = true;
                        }
                    } catch (Exception e) {

                    }

                    if (sessionFinished) {
                        toClient.println("Finish successfully");
                        break;
                    }
                }
            } catch(IOException e) {
                e.printStackTrace();
            }
        }
    }
    public static void main(String[] args) {
        ServerSideSocket srv = new ServerSideSocket();
        srv.run();
    }
}