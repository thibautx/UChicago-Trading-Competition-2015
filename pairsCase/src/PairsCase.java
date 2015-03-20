import com.optionscity.freeway.api.IDB;
import com.optionscity.freeway.api.IJobSetup;
import org.uchicago.pairs.core.AbstractPairsCase;
import org.uchicago.pairs.PairsHelper.OrderState;
import org.uchicago.pairs.PairsHelper.Order;
import org.uchicago.pairs.PairsHelper.Quote;
import org.uchicago.pairs.PairsHelper.Ticker;
import org.uchicago.pairs.core.PairsInterface;
import org.uchicago.pairs.PairsUtils;


public class PairsCaseSample extends AbstractPairsCase implements PairsInterface {

    private IDB myDatabase;

    private String curr_position;
    private String new_position;

    /* Algorithm Parameters */
    static float slow_mavg_window = 500.0;
    static float fast_mavg_window = 50.0;
    static float momentum_mavg_window = 20.0;
    static float entry_threshold = 2.0;
    static float exit_threshold = 0.0;
    static float risk_threshold = 5.0;
    static float momentum_threshold = 0.0;
    static double std_window = 20.0;

    /* Data */
    // @TODO: spread data structure for when we need to find the pairs?
    int tick = 0; // current tick
    int numSymbols;
    int numPairs;
    Order[] orders;
    double priceHuron, priceSuperior, priceMichigan, priceOntario, priceErie; //variables to store current price information
    float[] spread; // the spreads of the pairs we are trading
    double std; // standard deviation
    

    /* Flags */
    boolean foundPairs = false;

    /* Indicators */
    // @TODO: data structure for when we need to find the pairs?
    float slow_mavg;
    float fast_mavg;
    float momentum_mavg;

    /* Indicators */

    private void updateIndicators(){
    // This method is called every time we increment a tick
        for(int i = 0; i < numPairs; i++){
            // For each pair, update its current moving averages
            slow_mavg = movingAverage(slow_mavg_window);
            fast_mavg = movingAverage(fast_mavg_window);
            momentum_mavg = momentumMovingAverage(momentum_mavg_window);
        }
    }

    private float movingAverage(int window){
        if(tick <= window){
            float cum_sum = 0;
            for(int i = 0; i < tick; i++){
                cum_sum += spread[i];
            }
            return cum_sum/tick;
        }
        else{
            float cum_sum = 0;
            for(int i = tick-window; i < tick; i++){
                cum_sum += spread[i];
            }
            return cum_sum/window;
        }
    }   

    private float momentumMovingAverage(int window){
        ArrayList<float> derivs = new ArrayList<float>();
        for(int i = 0; i < window-1; i++){
            derivs.append(spread[i+1]-spread[i]);
        }
        if(tick <= window){
            float cum_sum = 0;
            for(int i = 0; i < tick; i++){
                cum_sum += derivs.get(i);
            }
            return cum_sum / tick;
        }
        else{
            float cum_sum = 0;
            for(int i = 0; i < window; i++){
                cum_sum += derivs.get(i);
            }
            return cum_sum / window;
        }
    }

    /* Signals */

    // @TODO: update the std
    private String checkCashEntry(){
        // we want to go short
        if(diff >= entry_threshold*std >= 2.0*stock_spread && momentum_mavg <= momentum_threshold){
            // @TODO
        }
        // we want to go long
        else if(-diff >= entry_threshold*std >= 2.0*stock_spread && momentum_mavg >= momentum_threshold){
            // @TODO
        }
    }
    private String checkLongExit(){
        // we close the position for a profit
        if( diff >= exit_threshold*std && momentum_mavg <= -momentum_threshold){
            // @TODO
        }
        // we close the trade for a loss
        else if(-diff >= risk_threshold*std){
            // @TODO
        }
    }
    private String checkShortExit(){
        // we close the position for a gain
        if(diff <= exit_threshold*std && momentum_mavg >= momentum_threshold){
            // @TODO
        }
        // we close the position for a loss
        else if (-diff >= risk_threshold*std){
            // @TODO
        }
    }


    @Override
    public void addVariables(IJobSetup setup) {
        setup.addVariable("Strategy", "Strategy to use", "string", "one");
    }

    @Override
    public void initializeAlgo(IDB dataBase) {
        numPairs = (numSymbols == 5) ? 2 : 0; // initialize numPairs
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
        //initiate Order[]
        orders = PairsUtils.initiateOrders(symbols);
    }

    @Override
    public Order[] getNewQuotes(Quote[] quotes) {
        tick ++; // update the tick
        if (numSymbols == 2) {
            priceHuron = quotes[0].bid;
            priceSuperior = quotes[1].bid;
            spread[tick] = priceHuron - priceSuperior; // update the spread
            return roundOneStrategy(priceHuron, priceSuperior);

        } else if (numSymbols == 3){
            priceHuron = quotes[0].bid;
            priceSuperior = quotes[1].bid;
            priceMichigan = quotes[2].bid;
            return roundTwoStrategy(priceHuron, priceSuperior, priceMichigan);
        } else{
            priceHuron = quotes[0].bid;
            priceSuperior = quotes[1].bid;
            priceMichigan = quotes[2].bid;
            priceOntario = quotes[3].bid;
            priceErie = quotes[4].bid;
            return roundThreeStrategy(priceHuron, priceSuperior, priceMichigan, priceOntario, priceErie);
        }
    }

    //helper function that implements a dummy strategy for round 1
    public Order[] roundOneStrategy (double priceHuron, double priceSuperior){
        return orders;
    }
    //helper function that implements a dummy strategy for round 2
    public Order[] roundTwoStrategy(double priceHuron, double priceSuperior, double priceMichigan) {  
        return orders;
    }
    //helper function that implements a dummy strategy for round 2
    public Order[] roundThreeStrategy(double priceHuron, double priceSuperior, double priceMichigan, double priceOntario, double priceErie){
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
        return null;
    }

    //@TODO: this is called when we need to make changes to position, executes trades
    public Order[] adjustPosition(curr_spread, entry_spread, weights){

    }

    //@TODO: find the correlated pairs...return type?
    public void findCorrelatedPairs(){

    }
}
