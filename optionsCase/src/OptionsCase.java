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


public class OptionsCase extends AbstractOptionsCase implements OptionsInterface {

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

    @Override
    public void addVariables(IJobSetup setup) {
        setup.addVariable("Alpha", "Passiveness: Number of standard deviations in vega to buffer quote against", "double", "1.0");
        setup.addVariable("Xi", "Sensitivity to vega risk", "double", "1");
        setup.addVariable("EMA Decay", "Decay factor of the IV series EMA", "double", "0.5");
    }

    @Override
    public void initializeAlgo(IDB dataBase, List<String> instruments) {

        /* retrieve parameters */
        alpha = getDoubleVar("Alpha");
        xi = getDoubleVar("Xi");
        impliedVolEMA = new EMA(getDoubleVar("EMA Decay"));

        /* add initial vol to EMA */
        impliedVolEMA.average(initialVol);

        /* initialize position map */
        for(int strike : strikes){
            positions.put(strike, 0);
        }
    }

    @Override
    public void newFill(int strike, int side, double price) {
        log("Quote Fill, price=" + price + ", strike=" + strike + ", direction=" + side);
        spread = 0;
        /* update position */
        positions.put(strike, positions.get(strike) + side);

        /* estimate the true price by discounting the average edge our fills receive */
        double truePrice = (side == 1) ? (price/0.95) : (price/1.05);

        /* compute IV via Dekker-Brent method */
        double lastVol = impliedVolatility(truePrice, strike);

        //log("Compute lastVol = " + lastVol);

        /* add lastVol to IV EMA */
        impliedVolEMA.average(lastVol);

        cash -= side*price;

        impliedVolEMA.average(impliedVolEMA.get()+getTotalVegaRisk()/beta);

        //log("Got filled, immediate gain is " + side*(truePrice - price));
        //log("Got filled, immediate (avg) loss is " + side*(price-OptionsMathUtils.theoValue(strike, impliedVolEMA.get())));
    }

    @Override
    public QuoteList getCurrentQuotes(){
        //log("Received a request for current quotes");

        double totalVegaRisk = getTotalVegaRisk();

        //log("Using IV = " + impliedVolEMA.get());

        double assets = 0;

        //log("--------------");
        //log("Cash = " + cash);
        for(int strike : strikes){
              //log(Integer.toString(strike) + " qty = " + positions.get(strike));
              assets += positions.get(strike) * OptionsMathUtils.theoValue(strike, impliedVolEMA.get());
        }
        //log("Assets = " + assets);
        //log("IV = " + impliedVolEMA.get());
        //log("Vega = " + getTotalVegaRisk() + " out of " + vegaLimit);
        log("PnL = " + (cash + assets) + " ---- Vega = " + getTotalVegaRisk());
        //log("--------------");

        Quote quoteEighty = getQuote(80, totalVegaRisk);
        Quote quoteNinety = getQuote(90, totalVegaRisk);
        Quote quoteHundred = getQuote(100, totalVegaRisk);
        Quote quoteHundredTen = getQuote(110, totalVegaRisk);
        Quote quoteHundredTwenty = getQuote(120, totalVegaRisk);

        return new QuoteList(quoteEighty,quoteNinety,quoteHundred,quoteHundredTen,quoteHundredTwenty);
    }

    @Override
    //TODO - update vol based on the fact that we know their order was higher/lower than our quote
    public void noBrokerFills() {
        //log("No match against broker the broker orders...time to adjust some levers?");
        impliedVolEMA.average(impliedVolEMA.get()-getTotalVegaRisk()/beta);
        spread -= 0.1;
    }

    @Override
    public void penaltyNotice(double amount) {
        //log("Penalty received in the amount of " + amount);
    }

    @Override
    public OptionsInterface getImplementation() {
        return this;
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
        //log("Bid omega is " + -1*Math.max(omega/5, omega));
        //log("Ask omega is " + -1*Math.min(omega/5, omega));
        //log(Integer.toString(strike) + " quote is " + bidPrice + " - " + askPrice);
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
