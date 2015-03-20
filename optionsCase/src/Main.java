import org.uchicago.options.OptionsHelpers.*;

import java.io.*;

/**
 * Created by Greg Pastorek on 3/11/2015.
 */
public class Main {

    final static boolean USE_REAL_VOL = false;
    static double alpha = 1.3;
    static double xi = 1.0;
    static double ema_decay = 0.1;
    static double edge_estimate = 0.04;
    static double beta = 0.05;
    static double beta_decay = 0.9;
    static int hit_weight = 3;
    static int miss_streak_weight = 5;
    static int miss_count_trigger = 3;

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
        }

        mycase.initializeAlgo(alpha, xi, ema_decay, edge_estimate, beta, beta_decay, hit_weight,miss_streak_weight, miss_count_trigger);

        File file = new File("C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\optionsCase\\python\\case_data.csv");
        File vol_file = new File("C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\optionsCase\\python\\vol_data.txt");

        BufferedReader br = new BufferedReader(new FileReader(file));
        BufferedReader vol_br = new BufferedReader(new FileReader(vol_file));
        br.readLine();
        String line;
        while ((line = br.readLine()) != null) {
            String[] line_split = line.split(",");
            String vol_line = vol_br.readLine();
            double real_vol = Double.parseDouble(vol_line);
            if(USE_REAL_VOL) {
                for (int x = 0; x < 20; x++) {
                    mycase.impliedVolEMA.average(real_vol);
                }
            }
            int direction = Integer.parseInt(line_split[0]);
            int strike = Integer.parseInt(line_split[1]);
            double price = Double.parseDouble(line_split[2]);
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
            System.out.println("Real vega = " + real_vega);
        }

    }

}
