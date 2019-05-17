import com.mongodb.BasicDBObject;
import com.mongodb.DBObject;

import java.io.*;
import java.net.*;
import java.util.Arrays;

public class ClientSocket {
    private int maxRepeatTriesCount = 3;

    PrintWriter toServer;
    BufferedReader fromServer;

    private Socket acquaintance(String[] inJsonFields) throws IOException {
        int serverPort = 4020;
        InetAddress host = InetAddress.getByName("localhost");
        Socket socket = new Socket(host,serverPort);

        System.out.println("Just connected to " + socket.getRemoteSocketAddress());

        toServer = new PrintWriter(socket.getOutputStream(),true);
        fromServer = new BufferedReader(new InputStreamReader(socket.getInputStream()));

        toServer.println(Arrays.toString(inJsonFields));
        String line = fromServer.readLine();

        if (!line.equals("Connection succeeded")) {
            parting(toServer, fromServer, socket);
            throw new IOException();
        }

        return socket;
    }

    private void  parting(PrintWriter toServer ,BufferedReader fromServer, Socket socket) throws IOException {
        toServer.close();
        fromServer.close();
        socket.close();
    }

    /**
     * @param callBack description of experiment data
     */
    public void run(String[] inJsonFields, ExpGenerator callBack) {
        boolean finish = false;
        int tryCount = 0;
        boolean canSendNew = true;
        DBObject sample = null;
        int samplesCount = 0;

        try {
            Socket socket = acquaintance(inJsonFields);

            while (!finish) {
                if(canSendNew) {
                    if(samplesCount < 100) {
                        sample = callBack.generateSample();
                        samplesCount++;
                    } else {
                        sample = new BasicDBObject("finish", "yes");
                    }
                }
                toServer.println(sample);

                String line = fromServer.readLine();
                switch (line) {
                    case "Finish with problems":
                        finish = true;
                        break;

                    case "Finish successfully":
                        parting(toServer, fromServer, socket);
                        finish = true;
                        break;

                    case "-1":
                        tryCount++;
                        if(tryCount < maxRepeatTriesCount) {
                            canSendNew = false;
                        } else {
                            canSendNew = true;
                            tryCount = 0;
                        }
                        break;

                    case "0": tryCount = 0; canSendNew = true; break;
                    default:
                }

                System.out.println("Client received: " + line + " from Server");
            }

        }
        catch(IOException e){
            System.out.println("Connection failed");
        }
    }

    public static void main(String[] inJsonFields0) {
        String[] inJsonFields = {"id" , "time" , "coordinates", "density"}; // TODO: develop validation
        ClientSocket client = new ClientSocket();

        client.run(inJsonFields, new ExpGenerator());
    }
}