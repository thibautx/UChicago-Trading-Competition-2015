import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

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
    double entry_threshold, exit_threshold, risk_threshold, momentum_threshold, alpha, ema_alpha;

    /* Global Data */
    int tick; // current tick
    double min_spread;
    int numSymbols;
    int numPairs;
    int pos_limit; // per stock in the pair - i.e. absolutelimit/numpairs/2
    Order[] orders;
    double[] prices;
    double priceHuron, priceSuperior, priceMichigan, priceOntario, priceErie; //variables to store current price information
    
    /* Tracking Data*/
    boolean foundPairs;
    double pnl;
    int n_win;
    int n_lose;
    
    
    Map<StockPair, Integer> allPairs;
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
        fast_mavg_window = 20;
        momentum_mavg_window = 20;
        entry_threshold = 1.0;
        exit_threshold = 0.7;
        momentum_threshold = 0.0;
        ema_alpha = .075;
        std_window = 20;
        alpha = 1.0;
        log("Initialized parameters");
        /* Initialize Tracking Data */
        tick = -1; 
        min_spread = 1.0;
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
        tick++; // update the tick
        log("Tick " + tick + " Current PnL " + pnl);
        //log("Current position is " + pair1.position + " Stock 1 holdings: " + pair1.stock1holdings + "Stock 2 holdings: " + pair1.stock2holdings);
        if (numSymbols == 2) {
            log("Current position " + pair1.position);
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
            for(StockPair pair : allPairs.keySet()){
                updatePair(pair);
            }
            return roundTwoStrategy(priceHuron, priceSuperior, priceMichigan);
        } else {
            priceHuron = quotes[0].bid;
            priceSuperior = quotes[1].bid;
            priceMichigan = quotes[2].bid;
            priceOntario = quotes[3].bid;
            priceErie = quotes[4].bid;
            updatePrices();
            for(StockPair pair : allPairs.keySet()){
                updatePair(pair);
            }
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
        allPairs = new HashMap<StockPair, Integer>();
        if(numSymbols == 2){
            log("Round 1");
            pos_limit = 20;
            pair1 = new StockPair(0, 1); // there is only one pair
        }
        else if(numSymbols == 3){
            pos_limit = 30;
            allPairs.put(new StockPair(0,1), 0);
            allPairs.put(new StockPair(0,2), 0);
            allPairs.put(new StockPair(1,2), 0);
        }
        else if(numSymbols == 5){
            pos_limit = 25; 
            for(int i = 0; i < 5; i++){
                for(int j = i+1; j <= 5; j++){
                    allPairs.put(new StockPair(i, j), 0);
                }
            }
        }
    }
    /* Signals */
    private void findCorrelatedPairs(){
        // Implement ADF test
    }

    private void adjustPosition(StockPair pair){
        if(Math.abs(2*pair.position) < pos_limit){
            checkCashEntry(pair);
        }
        else if(pair1.position > 0){
            checkLongExit(pair);
        }
        else if(pair.position < 0){
            checkShortExit(pair);
        }
    }
    private void checkCashEntry(StockPair pair){
        log("diff " + pair.diff + "entry_threshold: " + entry_threshold + 
            "std: " + pair.std[tick] + "momentum_mavg t:" + pair.momentum_mavg[tick] + 
            "momentum_mavg t-1: " + pair.momentum_mavg[tick-1]);
        /* short entry */
        if(goShort(pair)){
            pair.entry_spread = pair.spread[tick];
            int qty = (int)(alpha*Math.pow((-pair.diff/pair.std[tick]),2));
            qty = Math.max(qty, -pair.position-pos_limit/2);
            adjustOrder(pair, "short", qty);
            
        }
        /* long entry */
        else if(goLong(pair)){
            pair.entry_spread = pair.spread[tick];
            int qty = (int)(alpha*Math.pow((pair.diff/pair.std[tick]),2));
            qty = Math.min(qty, pos_limit/2-pair.position);
            adjustOrder(pair, "long", qty);
        }
    }
    private void checkLongExit(StockPair pair){
        if(closeLong(pair)){
            int qty = -pair.position;
            adjustOrder(pair, "short", qty);
            if(goShort(pair)){
                qty = (int)(alpha*Math.pow((-pair.diff/pair.std[tick]), 2));
                qty = Math.max(qty, -pos_limit/2);
            }
        }
    }
    private void checkShortExit(StockPair pair){
        if(closeShort(pair)){
            int qty = -pair.position;
            adjustOrder(pair, "long", qty);
            if(goLong(pair)){ 
                qty = (int)(alpha*Math.pow((pair.diff/pair.std[tick]),2));
                qty = Math.min(qty, pos_limit/2);
                adjustOrder(pair, "long", qty);
            }
        }
    }

    private void adjustOrder(StockPair pair, String position, int qty){
        if(position == "short"){
            orders[pair.index1].quantity -= qty;
            orders[pair.index2].quantity += qty;
            pair.stock1holdings -= qty;
            pair.stock2holdings += qty;
            pair.position -= qty;
        }
        else if (position == "long"){
            orders[pair.index1].quantity += qty;
            orders[pair.index2].quantity -= qty;
            pair.stock1holdings += qty;
            pair.stock2holdings -= qty;
            pair.position += qty;
        }
    }

    private boolean goLong(StockPair pair){
        return (-pair.diff >= entry_threshold*pair.std[tick]
            && -pair.diff >= 2*min_spread
            && Math.signum(pair.momentum_mavg[tick]) != Math.signum(pair.momentum_mavg[tick-1])
            && pair.momentum_mavg[tick] > pair.momentum_mavg[tick-1]);
    }

    private boolean goShort(StockPair pair){
        return (pair.diff >= entry_threshold*pair.std[tick] 
            && pair.diff >= 2*min_spread
            && Math.signum(pair.momentum_mavg[tick]) != Math.signum(pair.momentum_mavg[tick-1]) 
            && pair.momentum_mavg[tick] < pair.momentum_mavg[tick-1]);
    }

    private boolean closeLong(StockPair pair){
        return ((pair.spread[tick]-pair.entry_spread) >= 2*min_spread
            && -pair.diff <= exit_threshold*pair.std[tick]
            && Math.signum(pair.momentum_mavg[tick]) != Math.signum(pair.momentum_mavg[tick-1])
            && pair.momentum_mavg[tick] < pair.momentum_mavg[tick-1]);
    }

    private boolean closeShort(StockPair pair){
        return ((pair.entry_spread-pair.spread[tick]) >= 2
            && pair.diff <= exit_threshold*pair.std[tick]
            && Math.signum(pair.momentum_mavg[tick]) != Math.signum(pair.momentum_mavg[tick-1])
            && pair.momentum_mavg[tick] > pair.momentum_mavg[tick-1]);
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
        //log("tick " + tick + "price1 " + pair.price1 + "price2 " + pair.price2);
        pair.spread[tick] = pair.price1 - pair.price2;
        pair.slow_mavg[tick] = movingAverage(pair, slow_mavg_window);
        pair.fast_mavg[tick] = movingAverage(pair, fast_mavg_window);
        pair.momentum_mavg[tick] = momentumMovingAverage(pair);
        pair.diff = pair.spread[tick] - pair.slow_mavg[tick];
        pair.std[tick] = standardDev(pair); // check the std function

    }

    private double expMovingAverage(StockPair pair){  
        pair.ema.average(pair.spread[tick]);
        return pair.ema.get();
    }

    private double movingAverage(StockPair pair, int window){
        if(tick < window){
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
        ArrayList<Double> deltas = new ArrayList<Double>();
        int offset = 0;
        if(tick >= momentum_mavg_window){
            offset = tick - momentum_mavg_window;
        }
        for(int i = offset; i < tick ; i++){
            //log("spread t " + pair.spread[i+1]);
            //log("spread t-1" + pair.spread[i]);
            double delta = pair.spread[i+1]-pair.spread[i];
            //log("delta " + delta);
            deltas.add(delta);
        }
        double cum_sum = 0;
        for(int i = 0; i < deltas.size(); i++){
            cum_sum += deltas.get(i);
        }
        //log("momentum_mavg: " + cum_sum/deltas.size());
        //log("cum_sum " + cum_sum + "size " + deltas.size());
        return cum_sum / deltas.size();
    }

    private double standardDev(StockPair pair){
        double sum1 = 0;
        double sum2 = 0;
        double stdev = 0;
        if(tick < std_window){
            for(int i = 0; i < tick; i++){
                sum1 += pair.spread[i];
                sum2 += Math.pow(pair.spread[i], 2);
                stdev = Math.sqrt(i*sum2 - Math.pow(sum1, 2))/i;
            }
        }
        else{
            for(int i = tick-std_window; i < tick; i++){
                sum1 += pair.spread[i];
                sum2 += Math.pow(pair.spread[i], 2);
                stdev = Math.sqrt(i*sum2 - Math.pow(sum1, 2))/i;
            }
        }
        return stdev;
    }

    public class EMA {

        private double alpha;
        private Double oldValue;;

        public EMA(double alpha) {
            this.alpha = alpha;
        }

        public double average(double value) {
            if (oldValue == null) {
                oldValue = value;
                return value;
            }
            double newValue = oldValue + alpha * (value - oldValue);
            oldValue = newValue;
            return newValue;
        }

        public double get() {
            if(oldValue == null){
                return 0;
            } else {
                return oldValue;
            }
        }

    }

    public class StockPair{
        int position;
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
        double[] slow_mavg;
        double[] fast_mavg;
        EMA ema;
        double[] exp_mavg;
        double[] momentum_mavg;
        double[] std;
        public StockPair(int index1, int index2){
            this.spread = new double[1000];
            this.slow_mavg = new double[1000];
            this.fast_mavg = new double[1000];
            ema = new EMA(ema_alpha);
            this.exp_mavg = new double[1000];
            this.momentum_mavg = new double[1000];
            this.std = new double[1000];
            this.position = 0; // starting position is cash
            this.index1 = index1;
            this.index2 = index2;
            stock1holdings = 0;
            stock2holdings = 0;
        }

    }

}
