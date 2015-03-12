import org.uchicago.options.OptionsHelpers.*;

import java.io.*;

/**
 * Created by Greg Pastorek on 3/11/2015.
 */
public class Main {

    static double alpha = 1.0;
    static double xi = 1.0;
    static double ema_decay = 0.05;
    static double beta = 2;

    public static void main(String args[]) throws IOException {

        TestOptionsCase mycase = new TestOptionsCase();

        mycase.initializeAlgo(alpha, xi, ema_decay, beta);

        File file = new File("C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\optionsCase\\python\\case_data.csv");

        BufferedReader br = new BufferedReader(new FileReader(file));
        br.readLine();
        String line;
        while ((line = br.readLine()) != null) {
            String[] line_split = line.split(",");
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
                    mycase.newFill(strike, -1*direction, price);
                } else {
                    mycase.noBrokerFills();
                }
            } else {
                /* broker sells */
                double bid = q.bid;
                if (bid >= price){
                    mycase.newFill(strike, -1*direction, price);
                } else {
                    mycase.noBrokerFills();
                }
            }
        }

    }

}
