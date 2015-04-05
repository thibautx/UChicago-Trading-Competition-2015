import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;

import org.uchicago.pairs.PairsHelper;
import org.uchicago.pairs.PairsHelper.OrderState;
import org.uchicago.pairs.PairsHelper.Order;
import org.uchicago.pairs.PairsHelper.Quote;
import org.uchicago.pairs.PairsHelper.Ticker;
import org.uchicago.pairs.PairsUtils;

/**
 * Created by Greg Pastorek on 4/5/2015.
 */
public class Main {

    static File file = new File("C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\pairsCase\\python\\PairsRound1.csv");

    static Ticker[] tickers = {
            Ticker.ERIE,
            Ticker.HURON,
            Ticker.MICHIGAN,
            Ticker.ONTARIO,
            Ticker.SUPERIOR
    };

    public static void main(String args[]) throws IOException {

        double pnl = 0;

        double cash = 0;

        HashMap<Ticker, Integer> positions = new HashMap<Ticker, Integer>();

        for(Ticker ticker : tickers) {
            positions.put(ticker, 0);
        }

        BufferedReader br = new BufferedReader(new FileReader(file));

        TestPairsCase mycase = new TestPairsCase();

        mycase.initializeAlgo();

        String line;
        while((line = br.readLine()) != null) {

            String[] line_split = line.split(";");

            Quote[] quotes = new Quote[line_split.length];

            for(int i = 0; i < line_split.length; i++) {
                double p = Double.parseDouble(line_split[i]);
                quotes[i] = new Quote(tickers[i] , p - 0.5, p + 0.5);
            }

            Order[] orders = mycase.getNewQuotes(quotes);

            for(int i = 0; i < orders.length; i++) {
                Order o = orders[i];
                if(o.quantity != 0) {
                    int pos = positions.get(o.ticker);
                    positions.put(o.ticker, pos+o.quantity);
                    cash -= 0.5 * o.quantity;
                    if(o.quantity > 0){
                        cash -= (1.0 + quotes[i].bid) * o.quantity;
                    } else {
                        cash -= quotes[i].bid * o.quantity;
                    }
                }
            }

        }

    }



}
