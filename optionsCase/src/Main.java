import org.uchicago.options.OptionsHelpers.*;

import java.io.*;
import java.util.LinkedList;
import java.util.Queue;

/**
 * Created by Greg Pastorek on 3/11/2015.
 */
public class Main {

    final static boolean USE_REAL_VOL = false;
    static double alpha = 1.0;
    static double xi = 2.0;
    static double ema_decay = 0.99;
    static double edge_estimate = 0.04;
    static double iota = 0.000;
    static double beta = 0.01;
    static double beta_decay = 1.2; //1.2
    static int hit_weight = 5;
    static int miss_streak_weight = 3;
    static int miss_count_trigger = 3;
    static int fucked_up_trigger = 7; //7

    static LinkedList<Double> vegaQueue = new LinkedList<Double>();

    public static void main(String args[]) throws IOException {

        TestOptionsCase mycase = new TestOptionsCase();
        if(args.length > 0) {
            alpha = Double.parseDouble(args[0]);
            xi = Double.parseDouble(args[1]);
            ema_decay = Double.parseDouble(args[2]);
            edge_estimate  = Double.parseDouble(args[3]);
            beta = Double.parseDouble(args[4]);
            beta_decay = Double.parseDouble(args[5]);
            hit_weight = Integer.parseInt(args[6]);
            miss_streak_weight = Integer.parseInt(args[7]);
            miss_count_trigger = Integer.parseInt(args[8]);
            iota = Double.parseDouble(args[9]);
            fucked_up_trigger = Integer.parseInt(args[10]);
        }

        mycase.initializeAlgo(alpha, xi, ema_decay, edge_estimate, iota, beta, beta_decay, hit_weight,miss_streak_weight, miss_count_trigger, fucked_up_trigger);

        File file = new File("C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\optionsCase\\python\\case_data.csv");
        //File file = new File("C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\Sample Data\\Options Case\\case1SampleData.csv");
        File vol_file = new File("C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\optionsCase\\python\\vol_data.txt");

        BufferedReader br = new BufferedReader(new FileReader(file));
        BufferedReader vol_br = new BufferedReader(new FileReader(vol_file));
        br.readLine();
        String line;
        int tick = 0;
        while ((line = br.readLine()) != null) {
            String[] line_split = line.split(",");
            String vol_line = vol_br.readLine();
            double real_vol = Double.parseDouble(vol_line);
            int direction = Integer.parseInt(line_split[0]);
            int strike = Integer.parseInt(line_split[1]);
            double price = Double.parseDouble(line_split[2]);
            double iv_price;
            if(direction == 1){
                iv_price = price / 0.95;
            } else {
                iv_price = price / 1.05;
            }
            //double real_vol = mycase.impliedVolatility(iv_price, strike);
            System.out.println("Real Vol = " + real_vol);
            if(USE_REAL_VOL) {
                for (int x = 0; x < 20; x++) {
                    mycase.impliedVolEMA.average(real_vol);
                }
            }
            System.out.println("Order: " + strike + "|" + price + "|" + direction + "|" + tick);
            QuoteList qlist = mycase.getCurrentQuotes();
            Quote q = null;
            switch (strike){
                case 80:
                    q = qlist.quoteEighty;
                    break;
                case 90:
                    q = qlist.quoteNinety;
                    break;
                case 100:
                    q = qlist.quoteHundred;
                    break;
                case 110:
                    q = qlist.QuoteHundredTen;
                    break;
                case 120:
                    q = qlist.quoteHundredTwenty;
                    break;
            }
            if(direction == -1){
                /* broker buys */
                double ask = q.offer;
                if(ask <= price){
                    mycase.newFill(strike, -1 * direction, ask);
                    System.out.println("Fill diff = " + (price - ask));
                } else {
                    mycase.noBrokerFills();
                    System.out.println("Fill diff = 0");
                }
            } else {
                /* broker sells */
                double bid = q.bid;
                if (bid >= price){
                    mycase.newFill(strike, -1*direction, bid);
                    System.out.println("Fill diff = " + (price - bid));
                } else {
                    mycase.noBrokerFills();
                    System.out.println("Fill diff = 0");
                }
            }
            double real_pnl = mycase.getPnL(real_vol);
            System.out.println("Real PnL = " + real_pnl);
            double real_vega = mycase.getTotalVegaRisk(real_vol);
            vegaQueue.add(real_vega);
            if(vegaQueue.size() > 10){
                vegaQueue.poll();
                String str = "";
                for(Double v : vegaQueue){
                    str += v + "|";
                }
                System.out.println("vega series = " + str);
                System.out.println("Vol diff = " + (real_vol - mycase.impliedVolEMA.get()));
            }
            System.out.println("Real vega = " + real_vega);
            tick++;
        }

    }

}
