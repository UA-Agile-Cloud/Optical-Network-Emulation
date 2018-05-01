/*
Generate Light-path request and send it to Ryu via HTTP protocol 
Author:   Jiakai Yu (jiakaiyu@email.arizona.edu)
Created:  2017/02/01
Version:  1.0
Last modified by Jiakai: 2017/08/13
*/

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Scanner;
import java.util.PriorityQueue;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class RequestSending {

    final static String[] url = {
            //"http://10.129.36.254:8080/TrafficRequest",
            //"http://192.168.2.0:8080/TrafficRequest",
            //"http://192.168.1.0:8080/TrafficRequest",
	    "http://127.0.0.1:8080/TrafficRequest",

    };

    //set the filepath to read the node info and request
    final static String file_path = "/var/opt/Optical-Network-Emulation/java-app/";

    //==========================start of Dikjstra for domain sequence routing============================
    //define each domain as a node or vertex
    public static class Vertex implements Comparable<Vertex> {
        public final String name;
        public Edge[] adjacencies;
        public double minDistance = Double.POSITIVE_INFINITY;
        public Vertex previous;
        public Vertex(String argName) { name = argName; }
        public String toString() { return name; }
        public int compareTo(Vertex other)
        {
            return Double.compare(minDistance, other.minDistance);
        }

    }

    //define the link between two domains. Unidirecational link.
    public static class Edge {
        public final Vertex target;
        public final double weight;
        public Edge(Vertex argTarget, double argWeight)
        { target = argTarget; weight = argWeight; }
    }

    //Dikjstra algorithm
    public static void computePaths(Vertex source) {
        source.minDistance = 0.;
        PriorityQueue<Vertex> vertexQueue = new PriorityQueue<Vertex>();
        vertexQueue.add(source);
        while (!vertexQueue.isEmpty()) {
            Vertex u = vertexQueue.poll();
            // Visit each edge exiting u
            for (Edge e : u.adjacencies)
            {
                Vertex v = e.target;
                double weight = e.weight;
                double distanceThroughU = u.minDistance + weight;
                if (distanceThroughU < v.minDistance) {
                    vertexQueue.remove(v);
                    v.minDistance = distanceThroughU ;
                    v.previous = u;
                    vertexQueue.add(v);
                }
            }
        }
    }

    //get the Dikjstra path
    public static List<Vertex> getShortestPathTo(Vertex target) {
        List<Vertex> path = new ArrayList<Vertex>();
        for (Vertex vertex = target; vertex != null; vertex = vertex.previous)
            path.add(vertex);
        Collections.reverse(path);
        return path;
    }

    //use the node or vertex name to get the vertex
    public static Vertex ToVertex(String name, Vertex v[]){
        for (int i=0; i<v.length;i++) {
            if (v[i].name.equals(name)){
                return v[i];
            }
        }
        return null;
    }

    //initialization with the topology. Example case: 3 domain connecting eaching other
    public static Vertex[] initial(){

        Vertex v[]= new Vertex[3];
        v[0] = new Vertex("1");
        v[1] = new Vertex("2");
        v[2] = new Vertex("3");
        v[0].adjacencies = new Edge[]{ new Edge(v[1], 1)};
        v[1].adjacencies = new Edge[]{ new Edge(v[2], 1), new Edge(v[0], 1)};
        v[2].adjacencies = new Edge[]{ new Edge(v[1], 1)};
        return v;
    }

    //calculate the routing domain seq with the source and destination domain
    public static List<Vertex> domain_sequence(Vertex x, Vertex y) {
        computePaths(x);
        System.out.println(x + " to " + y + ": " + y.minDistance);
        List<Vertex> path = getShortestPathTo(y);
        System.out.println("Path: " + path);
        return path;
    }
//==============================End of domain sequence calculation==========================

    //post a request with Http protocol
    public static String post(String strURL, String params) {
        //System.out.println(params);
        try {
            URL url = new URL(strURL);
            HttpURLConnection connection = (HttpURLConnection) url
                    .openConnection();
            connection.setDoOutput(true);
            connection.setDoInput(true);
            connection.setUseCaches(false);
            connection.setInstanceFollowRedirects(true);
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.connect();
            OutputStreamWriter out = new OutputStreamWriter(
                    connection.getOutputStream(), "UTF-8");
            out.append(params);
            out.flush();
            out.close();

            int length = (int) connection.getContentLength();
            InputStream is = connection.getInputStream();
            if (length != -1) {
                byte[] data = new byte[length];
                byte[] temp = new byte[512];
                int readLen = 0;
                int destPos = 0;
                while ((readLen = is.read(temp)) > 0) {
                    System.arraycopy(temp, 0, data, destPos, readLen);
                    destPos += readLen;
                }
                String result = new String(data, "UTF-8");
                System.out.println(result);
                return result;
            }
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
        return "error";
    }

    //do token for a request, and store the information of the request
    public static String[] GetRequest(String str) {
        String str_ = str.trim();
        String[] token = str_.split("[\\p{Space}]+");
        //String str1 = token[0];   // message id
        //String str2 = token[1];   // request type (add/tear)
        //String str3 = token[2];   // source node
        //String str4 = token[3];   // dest node
        //String str5 = token[4];   // tear traf when non-zero
        return token;
    }

    //get a node information from a file
    public static String[][] GetNode(Scanner node_list){
        int node_num= Integer.parseInt(node_list.nextLine());
        System.out.println(node_num);
        if (node_num>0)
            System.out.println("reading node information");
        else
            System.out.println("no node");
        String topo_[][]= new String[node_num][4];
        for(int i=0; i<node_num;i++){
            String str = node_list.nextLine();
            String str_ = str.trim();
            String[] token = str_.split("[\\p{Space}]+");
            topo_[i][0] = token[0];  // node id
            topo_[i][1] = token[1];  // node ip
            topo_[i][2] = token[2];  // node domain id
            topo_[i][3] = token[3];  // node domain ip
        }
        return topo_;
    }

    //identify the request if it is intra-domain or crossdomain setup based on source and destination nodes
    public static String rqst_idtf_ (String rqst[], String topo_[][]){
        String result = "no request";
        if (rqst[1].equals("add") && (Integer.parseInt(topo_[Integer.parseInt(rqst[2])-1][2]) != Integer.parseInt(topo_[Integer.parseInt(rqst[3])-1][2]))) {
            result = "CrossDomainRequest";
            return result;
        }
        if (rqst[1].equals("tear") && (Integer.parseInt(topo_[Integer.parseInt(rqst[2])-1][2]) != Integer.parseInt(topo_[Integer.parseInt(rqst[3])-1][2]))) {
            result = "CrossDomainTearDown";
            return result;
        }
        if (rqst[1].equals("add") && (Integer.parseInt(topo_[Integer.parseInt(rqst[2])-1][2]) == Integer.parseInt(topo_[Integer.parseInt(rqst[3])-1][2]))) {
            result = "IntraDomainRequest";
            return result;
        }
        if (rqst[1].equals("tear") && (Integer.parseInt(topo_[Integer.parseInt(rqst[2])-1][2]) == Integer.parseInt(topo_[Integer.parseInt(rqst[3])-1][2]))) {
            result = "IntraDomainTearDown";
            return result;
        }
        return result;
    }


//     public static void main(String[] args) throws IOException, InterruptedException {

//         try {
//             // String traffic_request = args[0];
//             // System.out.println(args.length);
//             String [] request = args; // GetRequest(traffic_request);
//             String params = "";
//             Scanner node_list = new Scanner(new File(file_path + "node_list.txt"));
//             String[][] topo_=GetNode(node_list);
//             if(request[1].equals("add")) {
//                 String rqst_idtf = rqst_idtf_(request, topo_);
//                 //System.out.println("The request is : " + rqst_idtf);
//                 String src_ip = topo_[Integer.parseInt(request[2]) - 1][1];
//                 String src_domain_ip = topo_[Integer.parseInt(request[2]) - 1][3];
//                 String dst_ip = topo_[Integer.parseInt(request[3]) - 1][1];
//                 String dst_domain_ip = topo_[Integer.parseInt(request[3]) - 1][3];

//                 params = "{\"Msg_ID\": " + "\"" + request[0] + "\""
//                         + ", \"Source_Node\": " + "\"" + request[2] + "\""
//                         + ", \"Source_Node_IP\": " + "\"" + src_ip + "\""
//                         + ", \"Source_Node_Domain_IP\": " + "\"" + src_domain_ip + "\""
//                         + ", \"Destination_Node\": " + "\"" + request[3] + "\""
//                         + ", \"Destination_Node_IP\": " + "\"" + dst_ip + "\""
//                         + ", \"Destination_Node_Domain_IP\": " + "\"" + dst_domain_ip + "\""
//                         + ", \"Request_Class\": " + "\"" + rqst_idtf + "\""
//                         + ", \"Domain_Num\": " + "1"//domain_num
//                         + ", \"Domain_Sequence\": " + "[1]"//path
//                         + ", \"TearTraf\": " + "\"" + request[4] + "\"" + "}";
//             }
//             else {
//                 params = "{\"Msg_ID\": " + "\"" + request[0] + "\""

//                         + ", \"Request_Class\": " + "\"" + "IntraDomainTearDown" + "\""

//                         + ", \"TearTraf\": " + "\"" + request[2] + "\"" + "}";
//             }
//             for(int j=0; j<url.length;j++) {
//                 post(url[j], params);
//             }

//         } catch (FileNotFoundException e) {
//             e.printStackTrace();
//         }
//     }
// }
    public static void main(String[] args) throws IOException, InterruptedException{
        try {
            Scanner in = new Scanner(new File(file_path + "user_request.txt"));
            //Scanner in = new Scanner(new File(file_path + "single_request.txt"));
            //BufferedReader in = new BufferedReader(new FileReader(new File(file_path + "user_request.txt")));
            //BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream(file_path + "user_request.txt")));
            Scanner node_list = new Scanner(new File(file_path + "node_list.txt"));
            String[][] topo_=GetNode(node_list);
            //System.out.println(topo_[20][3]);
            //String a =in.readLine();
            while (in.hasNextLine()) {
            //while(in.readLine()!=null){
            //while(in.readLine() != null){
                String  str = in.nextLine();
                System.out.println(str);
                String [] request = GetRequest(str);
                String params = "";
                if(request[1].equals("add")) {
                    String rqst_idtf = rqst_idtf_(request, topo_);
                    //System.out.println("The request is : " + rqst_idtf);
                    String src_ip = topo_[Integer.parseInt(request[2]) - 1][1];
                    String src_domain_ip = topo_[Integer.parseInt(request[2]) - 1][3];
                    String dst_ip = topo_[Integer.parseInt(request[3]) - 1][1];
                    String dst_domain_ip = topo_[Integer.parseInt(request[3]) - 1][3];
                    //Vertex[] v = initial();
                    //Vertex src_v = ToVertex(topo_[Integer.parseInt(request[2])-1][2],v);
                    // System.out.println(src_v);
                    //Vertex dst_v = ToVertex(topo_[Integer.parseInt(request[3])-1][2],v);
                    //System.out.println(dst_v);
                    //List<Vertex> path = domain_sequence(src_v, dst_v);
                    //int domain_num = path.size();//(int)dst_v.minDistance;
                    //System.out.println(Integer.toString(domain_num));
                    params = "{\"Msg_ID\": " + "\"" + request[0] + "\""
                            + ", \"Source_Node\": " + "\"" + request[2] + "\""
                            + ", \"Source_Node_IP\": " + "\"" + src_ip + "\""
                            + ", \"Source_Node_Domain_IP\": " + "\"" + src_domain_ip + "\""
                            + ", \"Destination_Node\": " + "\"" + request[3] + "\""
                            + ", \"Destination_Node_IP\": " + "\"" + dst_ip + "\""
                            + ", \"Destination_Node_Domain_IP\": " + "\"" + dst_domain_ip + "\""
                            + ", \"Request_Class\": " + "\"" + rqst_idtf + "\""
                            + ", \"Domain_Num\": " + "1"//domain_num
                            + ", \"Domain_Sequence\": " + "[1]"//path
                            + ", \"TearTraf\": " + "\"" + request[4] + "\"" + "}";
                }
                else {
                    params = "{\"Msg_ID\": " + "\"" + request[0] + "\""

                            + ", \"Request_Class\": " + "\"" + "IntraDomainTearDown" + "\""

                            + ", \"TearTraf\": " + "\"" + request[2] + "\"" + "}";
                }
                for(int j=0; j<url.length;j++) {
                    System.out.println(j);
                    post(url[j], params);   //posting to all domains
                    TimeUnit.SECONDS.sleep(10);
                    //System.out.println(params);
                }
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
    }
}
