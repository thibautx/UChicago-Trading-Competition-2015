import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;

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

    final double beta = 50000;

    final int strikes[] = {80, 90, 100, 110, 120};

    double spread = 0;

    double cash = 0;

    HashMap<Integer, Integer> positions = new HashMap<Integer, Integer>();

    EMA impliedVolEMA;

    /* parameters */
    double alpha, xi;

    public void initializeAlgo() {

        /* retrieve parameters */
        alpha = 1.0;
        xi = 1.0;
        impliedVolEMA = new EMA(0.5);

        /* add initial vol to EMA */
        impliedVolEMA.average(initialVol);

        /* initialize position map */
        for(int strike : strikes){
            positions.put(strike, 0);
        }
    }

    public void newFill(int strike, int side, double price) {
        System.out.println("Quote Fill, price=" + price + ", strike=" + strike + ", direction=" + side);
        spread = 0;
        /* update position */
        positions.put(strike, positions.get(strike) + side);

        /* estimate the true price by discounting the average edge our fills receive */
        double truePrice = (side == 1) ? (price/0.95) : (price/1.05);

        /* compute IV via Dekker-Brent method */
        double lastVol = impliedVolatility(truePrice, strike);

        //System.out.println("Compute lastVol = " + lastVol);

        /* add lastVol to IV EMA */
        impliedVolEMA.average(lastVol);

        cash -= side*price;

        impliedVolEMA.average(impliedVolEMA.get()+getTotalVegaRisk()/beta);

        //System.out.println("Got filled, immediate gain is " + side*(truePrice - price));
        //System.out.println("Got filled, immediate (avg) loss is " + side*(price-OptionsMathUtils.theoValue(strike, impliedVolEMA.get())));
    }

    public QuoteList getCurrentQuotes(){
        //System.out.println("Received a request for current quotes");

        double totalVegaRisk = getTotalVegaRisk();

        //System.out.println("Using IV = " + impliedVolEMA.get());

        double assets = 0;

        //System.out.println("--------------");
        //System.out.println("Cash = " + cash);
        for(int strike : strikes){
            //System.out.println(Integer.toString(strike) + " qty = " + positions.get(strike));
            assets += positions.get(strike) * OptionsMathUtils.theoValue(strike, impliedVolEMA.get());
        }
        //System.out.println("Assets = " + assets);
        //System.out.println("IV = " + impliedVolEMA.get());
        //System.out.println("Vega = " + getTotalVegaRisk() + " out of " + vegaLimit);
        System.out.println("PnL = " + (cash + assets) + " ---- Vega = " + getTotalVegaRisk());
        //System.out.println("--------------");

        Quote quoteEighty = getQuote(80, totalVegaRisk);
        Quote quoteNinety = getQuote(90, totalVegaRisk);
        Quote quoteHundred = getQuote(100, totalVegaRisk);
        Quote quoteHundredTen = getQuote(110, totalVegaRisk);
        Quote quoteHundredTwenty = getQuote(120, totalVegaRisk);

        return new QuoteList(quoteEighty,quoteNinety,quoteHundred,quoteHundredTen,quoteHundredTwenty);
    }

    //TODO - update vol based on the fact that we know their order was higher/lower than our quote
    public void noBrokerFills() {
        //System.out.println("No match against broker the broker orders...time to adjust some levers?");
        impliedVolEMA.average(impliedVolEMA.get()-getTotalVegaRisk()/beta);
        spread -= 0.1;
    }

    public void penaltyNotice(double amount) {
        //System.out.println("Penalty received in the amount of " + amount);
    }

    /* helper functions */
    /* price option by price = theoPrice * (1 +/- delta + omega) */
    private Quote getQuote(int strike, double totalVegaRisk){
        double vol = impliedVolEMA.get();
        double theoPrice = OptionsMathUtils.theoValue(strike, vol);
        double vega = OptionsMathUtils.calculateVega(strike, vol);
        //double delta = vega * volSD * alpha;
        double delta = volSD * alpha;
        double omega = totalVegaRisk * xi;
        double bidPrice = theoPrice * (1 - delta - Math.max(0, omega)) - spread;
        double askPrice = theoPrice * (1 + delta - Math.min(0, omega)) + spread;
        //System.out.println("Bid omega is " + -1*Math.max(omega/5, omega));
        //System.out.println("Ask omega is " + -1*Math.min(omega/5, omega));
        //System.out.println(Integer.toString(strike) + " quote is " + bidPrice + " - " + askPrice);
        return new Quote(strike, bidPrice, askPrice);
    }

    private double getTotalVegaRisk() {
        double totalVega = 0;
        double vol = impliedVolEMA.get();

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
        UnivariateDifferentiableFunction f = new ImpliedVolFunction(price, strike);
        double start = impliedVolEMA.get();
        return solver.solve(100000, f, 0.0, 5.0, start);
    }

    class ImpliedVolFunction implements UnivariateDifferentiableFunction {

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

        @Override
        public DerivativeStructure value(DerivativeStructure d) throws DimensionMismatchException {
            return new DerivativeStructure(1, 1, OptionsMathUtils.calculateVega(strike, price));
        }

    }

    public class EMA {

        private double alpha;
        private Double oldValue;

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
            return oldValue;
        }

    }



}

