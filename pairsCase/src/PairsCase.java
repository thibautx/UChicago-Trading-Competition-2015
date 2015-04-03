import java.util.ArrayList;

import com.optionscity.freeway.api.IDB;
import com.optionscity.freeway.api.IJobSetup;
import org.uchicago.pairs.core.AbstractPairsCase;
import org.uchicago.pairs.PairsHelper.OrderState;
import org.uchicago.pairs.PairsHelper.Order;
import org.uchicago.pairs.PairsHelper.Quote;
import org.uchicago.pairs.PairsHelper.Ticker;
import org.uchicago.pairs.core.PairsInterface;
import org.uchicago.pairs.PairsUtils;


public class PairsCase extends AbstractPairsCase implements PairsInterface {

    private IDB myDatabase;

    /* Algorithm Parameters */
    int slow_mavg_window, fast_mavg_window, momentum_mavg_window, std_window;
    double entry_threshold, exit_threshold, risk_threshold, momentum_threshold;

    /* Global Data */
    int tick; // current tick
    int numSymbols;
    int numPairs;
    int positionLimit; // per stock in the pair - i.e. absolutelimit/numpairs/2
    Order[] orders;
    double[] prices;
    double priceHuron, priceSuperior, priceMichigan, priceOntario, priceErie; //variables to store current price information
    
    boolean foundPairs;
    double pnl;
    int n_win;
    int n_lose;
    
    
    ArrayList<StockPair> allPairs;
    // These are our found pairs
    StockPair pair1;
    StockPair pair2;

    @Override
    public void addVariables(IJobSetup setup) {
        setup.addVariable("Strategy", "Strategy to use", "string", "one");
    }

    @Override
    public void initializeAlgo(IDB dataBase) {
        log("Initializing Algo");
        /* Intialize Parameters */
        slow_mavg_window = 500;
        fast_mavg_window = 50;
        momentum_mavg_window = 20;
        entry_threshold = 2.0;
        exit_threshold = 0.0;
        risk_threshold = 5.0;
        momentum_threshold = 0.0;
        std_window = 20;
        log("Initialized parameters");
        /* Initialize Data */
        tick = -1; 
        prices = new double[5];
        foundPairs = false;
        pnl = 0;
        n_win = 0;
        n_lose = 0;
        log("Initialized Data");

        String strategy = getStringVar("Strategy");
        if (strategy.contains("one")) {
            // do strategy one
        }
    }

    @Override
    public void currentSymbols(Ticker[] symbols) {
        String rv="";
        numSymbols = symbols.length;
        for (Ticker s : symbols){
            rv = rv + s.name() + " ";
        }
        log("The tickers available for this round is " + rv);
        initializePairs();
        //initiate Order[]
        orders = PairsUtils.initiateOrders(symbols);
    }

    @Override
    public Order[] getNewQuotes(Quote[] quotes) {
        log("Tick " + tick);
        log("Current PnL " + pnl);
        tick++; // update the tick
        log("Current position is " + pair1.position + " Stock 1 holdings: " + pair1.stock1holdings + "Stock 2 holdings: " + pair1.stock2holdings);
        if (numSymbols == 2) {
            priceHuron = quotes[0].bid;
            priceSuperior = quotes[1].bid;
            updatePrices();
            updatePair(pair1);
            return roundOneStrategy(priceHuron, priceSuperior);

        } else if (numSymbols == 3){
            priceHuron = quotes[0].bid;
            priceSuperior = quotes[1].bid;
            priceMichigan = quotes[2].bid;
            updatePrices();
            return roundTwoStrategy(priceHuron, priceSuperior, priceMichigan);
        } else {
            priceHuron = quotes[0].bid;
            priceSuperior = quotes[1].bid;
            priceMichigan = quotes[2].bid;
            priceOntario = quotes[3].bid;
            priceErie = quotes[4].bid;
            updatePrices();
            return roundThreeStrategy(priceHuron, priceSuperior, priceMichigan, priceOntario, priceErie);
        }
        
    }

    //helper function that implements a dummy strategy for round 1
    public Order[] roundOneStrategy (double priceHuron, double priceSuperior){
        if(tick >= fast_mavg_window){
            adjustPosition(pair1);
        }
        return orders;
    }
    //helper function that implements a dummy strategy for round 2
    public Order[] roundTwoStrategy(double priceHuron, double priceSuperior, double priceMichigan) {  
        if(!foundPairs){
            return orders;
        }
        adjustPosition(pair1);
        adjustPosition(pair2);
        return orders;
    }
    //helper function that implements a dummy strategy for round 2
    public Order[] roundThreeStrategy(double priceHuron, double priceSuperior, double priceMichigan, double priceOntario, double priceErie){
        if(!foundPairs){
            return orders;
        }
        //TODO - what if only one pair was found, not the second yet?
        adjustPosition(pair1);
        adjustPosition(pair2);
        return orders;
    }

    @Override
    public void ordersConfirmation(Order[] orders) {
        for (Order o : orders){
            if (o.state != OrderState.FILLED){
                if (o.state == OrderState.REJECTED){
                    log("My order for " + o.ticker + "is rejected, time to check my position/limit");
                }
            }else{
                log("My order for " + o.ticker + "is filled");
            }
        }
    }

    @Override
    public PairsInterface getImplementation() {
        return this;
    }

    /* Intialize the Pairs Objects */
    private void initializePairs(){
        log("There are " + numSymbols + " symbols in this round.");
        allPairs = new ArrayList<StockPair>();
        if(numSymbols == 2){
            log("Round 1");
            positionLimit = 20;
            pair1 = new StockPair(0, 1); // there is only one pair
        }
        else if(numSymbols == 3){
            positionLimit = 30;
            allPairs.add(new StockPair(0,1));
            allPairs.add(new StockPair(0,2));
            allPairs.add(new StockPair(1,2));
        }
        else if(numSymbols == 5){
            positionLimit = 25; 
            for(int i = 0; i < 5; i++){
                for(int j = i+1; j <= 5; j++){
                    allPairs.add(new StockPair(i, j));
                }
            }
        }
    }
    /* Signals */
    //@TODO: find the correlated pairs...return type?
    private void findCorrelatedPairs(){

    }

    private void adjustPosition(StockPair pair){
        /*
        orders[pair.index1].quantity = 0;
        orders[pair.index2].quantity = 0;
        */
        if(pair.position == "cash"){
            // Look for entry
            checkCashEntry(pair);
        }
        else if(pair1.position == "long"){
            // Look for exit
            checkLongExit(pair);
        }
        else if(pair.position == "short"){
            // Look for exit
            checkShortExit(pair);
        }
    }
    // @TODO: update the std
    private void checkCashEntry(StockPair pair){
        // we want to go short
        log("spread" + pair.spread[tick] + "diff (spread-slow_mavg): " + pair.diff + "entry_threshold: " + entry_threshold + "std: " + pair.std + "momentum_mavg: " + pair.momentum_mavg + "momentum threshold: " + momentum_threshold);
        if(pair.diff >= entry_threshold*pair.std && entry_threshold*pair.std >= 2.0*pair.spread[tick] && pair.momentum_mavg <= momentum_threshold){
            pair.entry_spread = pair.spread[tick];
            // Make the order
            orders[pair.index1].quantity = -positionLimit;
            orders[pair.index2].quantity = positionLimit;
            // Update data
            pair.position = "short";
            pair.stock1holdings = -positionLimit;
            pair.stock2holdings = positionLimit;
            // Log info
            log("Long " + -positionLimit + "of stock 1");
            log("short " + positionLimit + " of stock 2");
            log("tick " + tick+  " open short spread at " + pair.entry_spread);
        }
        // we want to go long
        else if(-pair.diff >= entry_threshold*pair.std && entry_threshold*pair.std >= 2.0*pair.spread[tick] && pair.momentum_mavg >= momentum_threshold){
            pair.entry_spread = pair.spread[tick];
            
            // Make the Order
            orders[pair.index1].quantity = positionLimit;
            orders[pair.index2].quantity = -positionLimit;
            // Update data
            pair.stock1holdings = positionLimit;
            pair.stock2holdings = -positionLimit;
            pair.position = "long";
            //Log Info
            log("Long " + positionLimit + "of stock 1");
            log("Short " + -positionLimit + " of stock 2");
            log("tick " + tick + " open long spread at " + pair.entry_spread);
        }
    }
    private void checkLongExit(StockPair pair){
        // we close the position for a profit
        if( pair.diff >= exit_threshold*pair.std && pair.momentum_mavg <= -momentum_threshold){
            pair.position = "cash";
            orders[pair.index1].quantity = -positionLimit;
            orders[pair.index2].quantity = positionLimit;
            n_win ++;
            double profit = pair.entry_spread-pair.spread[tick];
            pnl += profit;
            log("tick " + tick + " close long spread at " + pair.spread[tick] +" profit of" + profit);
        }
        // we close the trade for a loss
        else if(-pair.diff >= risk_threshold*pair.std){
            pair.position = "cash";
            log("Positionlimit: " + positionLimit);
            orders[pair.index1].quantity = -positionLimit;
            orders[pair.index2].quantity = positionLimit;
            n_lose ++;
            double loss = pair.entry_spread-pair.spread[tick];
            pnl += loss;
            log("tick " + tick + " close long spread at " + pair.spread[tick] +" loss of" + loss);

        }
    }
    private void checkShortExit(StockPair pair){
        // we close the position for a gain
        if(pair.diff <= exit_threshold*pair.std && pair.momentum_mavg >= momentum_threshold){
            pair.position = "cash";
            orders[pair.index1].quantity = positionLimit;
            orders[pair.index2].quantity = -positionLimit;
            n_win++;
            double profit = pair.entry_spread-pair.spread[tick];
            pnl += profit;
            log("tick " + tick + " close short spread at " + pair.spread[tick] +"profit of" + profit);

        }
        // we close the position for a loss
        else if (-pair.diff >= risk_threshold*pair.std){
            pair.position = "cash";
            orders[pair.index1].quantity = positionLimit;
            pair.stock1holdings = positionLimit;
            orders[pair.index2].quantity = -positionLimit;
            pair.stock1holdings = -positionLimit;
            n_lose++;
            double loss = pair.entry_spread-pair.spread[tick];
            pnl += loss;
            log("tick " + tick + " close short spread at " + pair.spread[tick] +"loss of" + loss);

        }
    }

    /* Indicator Methods */
    private void updatePrices(){
        if(numSymbols == 1){
            prices[0] = priceHuron;
            prices[1] = priceSuperior;
        }
        else if(numSymbols == 3){
            prices[0] = priceHuron;
            prices[1] = priceSuperior;
            prices[2] = priceMichigan;
        }
        else{
            prices[0] = priceHuron;
            prices[1] = priceSuperior;
            prices[2] = priceMichigan;
            prices[3] = priceOntario;
            prices[4] = priceErie;
        }
    }
    private void updatePair(StockPair pair){
        // After every tick, we update the data contained in the StockPair object
        pair.price1 = prices[pair.index1];
        pair.price2 = prices[pair.index2];
        pair.spread[tick] = pair.price1 - pair.price2;
        pair.slow_mavg = movingAverage(pair, slow_mavg_window);
        pair.fast_mavg = movingAverage(pair, fast_mavg_window);
        pair.momentum_mavg = momentumMovingAverage(pair);
        pair.diff = pair.spread[tick] - pair.slow_mavg;
        pair.std = standardDeviation(pair); // check the std function

    }

    private double movingAverage(StockPair pair, int window){
        if(tick <= window){
            double cum_sum = 0;
            for(int i = 0; i < tick; i++){
                cum_sum += pair.spread[i];
            }
            return cum_sum/tick;
        }
        else{
            double cum_sum = 0;
            for(int i = tick-window; i < tick; i++){
                cum_sum += pair.spread[i];
            }
            return cum_sum/window;
        }
    }   

    private double momentumMovingAverage(StockPair pair){
        ArrayList<Double> derivs = new ArrayList<Double>();
        for(int i = 0; i < momentum_mavg_window /*-1*/; i++){
            derivs.add(pair.spread[i+1]-pair.spread[i]);
        }
        if(tick <= momentum_mavg_window){
            double cum_sum = 0;
            for(int i = 0; i < tick; i++){
                cum_sum += derivs.get(i);
            }
            return cum_sum / tick;
        }
        else{
            double cum_sum = 0;
            for(int i = 0; i < momentum_mavg_window; i++){
                cum_sum += derivs.get(i);
            }
            return cum_sum / momentum_mavg_window;
        }
    }

    private double standardDeviation(StockPair pair){
        double total = 0;
        for(int i = std_window; i < pair.spread.length; i++){
            total += pair.spread[i];
        }
        return Math.sqrt(total/(pair.spread.length-std_window));

    }

    public class StockPair{
        String position;
        int stock1holdings;
        int stock2holdings;
        int index1;
        int index2;
        double price1;
        double price2;
        double entry_spread;
        double[] spread; // timeseries of the spread
        /* Indicators */
        double diff;
        double slow_mavg;
        double fast_mavg;
        double momentum_mavg;
        double std;
        public StockPair(int index1, int index2){
            this.spread = new double[1000];
            this.position = "cash"; // starting position is cash
            this.index1 = index1;
            this.index2 = index2;
            stock1holdings = 0;
            stock2holdings = 0;
        }

    }

}
