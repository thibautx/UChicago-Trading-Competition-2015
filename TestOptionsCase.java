import java.util.*;

import org.apache.commons.math3.analysis.UnivariateFunction;
import org.apache.commons.math3.analysis.differentiation.DerivativeStructure;
import org.apache.commons.math3.analysis.differentiation.UnivariateDifferentiableFunction;
import org.apache.commons.math3.analysis.solvers.BisectionSolver;
import org.apache.commons.math3.analysis.solvers.NewtonRaphsonSolver;
import org.apache.commons.math3.exception.DimensionMismatchException;
import org.uchicago.options.OptionsHelpers.Quote;
import org.uchicago.options.OptionsHelpers.QuoteList;
import org.uchicago.options.OptionsMathUtils;
import org.uchicago.options.core.AbstractOptionsCase;
import org.uchicago.options.core.OptionsInterface;

import com.optionscity.freeway.api.IDB;
import com.optionscity.freeway.api.IJobSetup;


public class TestOptionsCase {

    private IDB myDatabase;

    // Note that this implementation uses price of 100 call for ALL options
    final double vegaLimit = 5 * OptionsMathUtils.theoValue(100, 0.3);
    final double volSD = 0.05;
    final double initialVol = 0.3;

    final double r = 0.01;
    final double t = 1.0;
    final double s = 100.0;

    final int strikes[] = {80, 90, 100, 110, 120};

    double cur_iota = 0;
    double iota;

    double cash = 0;

    HashMap<Integer, Integer> positions = new HashMap<Integer, Integer>();

    public EMA impliedVolEMA;

    /* parameters */
    double alpha, xi, beta, hit_weight, edge_estimate;

    double beta_decay_rate;
    double min_beta = 0.01;
    double cur_beta;
    int beta_trigger = 8;

    double last_vega_sign = 0;

    int miss_streak_weight;
    int miss_count_trigger;
    int cur_miss_count = 0;

    int we_fucked_up_trigger = 100;
    double fucked_beta = 0.2;

    double d_vol_cap = 0.25;
    double max_beta_d_vol = 0.025;

    EMA ticksPosVega = new EMA(0.5);
    EMA ticksNegVega = new EMA(0.5);
    int pos_vega_ticks = 0;
    int neg_vega_ticks = 0;

    public void initializeAlgo(double alpha_, double xi_, double ema_decay_, double edge_estimate_, double iota_,
                               double beta_, double beta_decay_, int hit_weight_, int miss_streak_weight_, int miss_count_trigger_, int fucked_up_trigger_) {

        /* retrieve parameters */
        alpha = alpha_;
        xi = xi_;
        edge_estimate = edge_estimate_;
        iota = iota_;
        beta = beta_;
        beta_decay_rate = beta_decay_;
        cur_beta = beta;
        miss_streak_weight = miss_streak_weight_;
        miss_count_trigger = miss_count_trigger_;
        hit_weight = hit_weight_;
        we_fucked_up_trigger = fucked_up_trigger_;
        impliedVolEMA = new EMA(ema_decay_);

        /* add initial vol to EMA */
        impliedVolEMA.average(initialVol);

        /* initialize position map */
        for(int strike : strikes){
            positions.put(strike, 0);
        }
    }

    /* side =  1 => we sold   */
    /* side = -1 => we bought */
    public void newFill(int strike, int side, double price) {
        System.out.println("Quote Fill, price=" + price + ", strike=" + strike + ", direction=" + side);

        /* estimate the true price by discounting the average edge our fills receive */
        double truePrice = (side == -1) ? (price/(1 - edge_estimate)) : (price/(1 + edge_estimate));

        /* add lastVol to IV EMA */
        for(int x = 0; x < hit_weight; x++) {
            impliedVolEMA.average(lastVol);
        }

        /* update position */
        positions.put(strike, positions.get(strike) - side);

        cash += side*price;

        if(side == 1){
            neg_vega_ticks++;
        } else {
            pos_vega_ticks++;
        }

        double vega = getTotalVegaRisk();

    }

    public QuoteList getCurrentQuotes(){
        //System.out.println("Received a request for current quotes");

        double totalVegaRisk = getTotalVegaRisk();

        if(totalVegaRisk > 0){
            ticksNegVega.average(neg_vega_ticks);
            pos_vega_ticks++;
            neg_vega_ticks = 0;
        }
        else if (totalVegaRisk < 0) {
            ticksPosVega.average(pos_vega_ticks);
            neg_vega_ticks++;
            pos_vega_ticks = 0;
        }

        System.out.println("PnL = " + getPnL());
        System.out.println("Vega = " +  + getTotalVegaRisk());
        System.out.println("Vol = " + impliedVolEMA.get());

        Quote quoteEighty = getQuote(80, totalVegaRisk);
        Quote quoteNinety = getQuote(90, totalVegaRisk);
        Quote quoteHundred = getQuote(100, totalVegaRisk);
        Quote quoteHundredTen = getQuote(110, totalVegaRisk);
        Quote quoteHundredTwenty = getQuote(120, totalVegaRisk);

        return new QuoteList(quoteEighty,quoteNinety,quoteHundred,quoteHundredTen,quoteHundredTwenty);
    }

    private double minAbs(double A, double B){
        return Math.abs(A) < Math.abs(B) ? A : B;
    }


    public void noBrokerFills() {
        //System.out.println("No match against broker the broker orders...time to adjust some levers?");
        //TODO - no fill, what to do now?

    }

    public void penaltyNotice(double amount) {
        System.out.println("Penalty received in the amount of " + amount);
    }

    /* helper functions */
    private Quote getQuote(int strike, double totalVegaRisk){
        double vol = impliedVolEMA.get();
        double theoPrice = OptionsMathUtils.theoValue(strike, vol);
        double vega = OptionsMathUtils.calculateVega(strike, vol);
		
		//TODO - use trading logic to adjust your spread
		
        double bidPrice = theoPrice * /* insert spread ratio here */;
        double askPrice = theoPrice * /* insert spread ratio here */;
        System.out.println("Quote: " + Integer.toString(strike) + "|" + bidPrice + "|" + askPrice);
        return new Quote(strike, bidPrice, askPrice);
    }

    public double getPnL(){
        return getPnL(impliedVolEMA.get());
    }

    public double getPnL(double vol){
        double assets = 0;

        for(int strike : strikes){
            //System.out.println(Integer.toString(strike) + " qty = " + positions.get(strike));
            assets += positions.get(strike) * OptionsMathUtils.theoValue(strike, vol);
        }

        return 100*(cash + assets);

    }

    private double getTotalVegaRisk() {
        double vol = impliedVolEMA.get();
        return getTotalVegaRisk(vol);
    }

    public double getTotalVegaRisk(double vol) {
        double totalVega = 0;

        for(int strike : strikes){
            double vega = OptionsMathUtils.calculateVega(strike, vol);
            totalVega += vega*positions.get(strike);
        }

        return totalVega;
    }

    private double getVegaRisk(int strike){
        double vol = impliedVolEMA.get();
        double vega = OptionsMathUtils.calculateVega(strike, vol);
        return vega*positions.get(strike);
    }

    public double impliedVolatility(double price, double strike) {
        BisectionSolver solver = new BisectionSolver();
        UnivariateFunction f = new ImpliedVolFunction(price, strike);
        double start = impliedVolEMA.get();
        return solver.solve(100000, f, 0.0, 5.0, start);
    }

    class ImpliedVolFunction implements UnivariateFunction {

        double strike;
        double price;

        public ImpliedVolFunction(double price, double strike){
            this.strike = strike;
            this.price = price;
        }


        @Override
        public double value(double v) {
            return OptionsMathUtils.theoValue(strike, v) - price;
        }
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



}

