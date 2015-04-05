import java.util.HashMap;
import java.util.List;

import org.apache.commons.math3.analysis.UnivariateFunction;
import org.apache.commons.math3.analysis.solvers.BisectionSolver;
import org.uchicago.options.OptionsHelpers.Quote;
import org.uchicago.options.OptionsHelpers.QuoteList;
import org.uchicago.options.OptionsMathUtils;
import org.uchicago.options.core.AbstractOptionsCase;
import org.uchicago.options.core.OptionsInterface;

import com.optionscity.freeway.api.IDB;
import com.optionscity.freeway.api.IJobSetup;


public class OptionsCaseILL1 extends AbstractOptionsCase implements OptionsInterface {

    private IDB myDatabase;

    final double vegaLimit = 5 * OptionsMathUtils.theoValue(100, 0.3);
    final double volSD = 0.05;
    final double initialVol = 0.3;

    final double r = 0.01;
    final double t = 1.0;
    final double s = 100.0;

    final int strikes[] = {80, 90, 100, 110, 120};

    double spread = 0;

    double cash = 0;

    HashMap<Integer, Integer> positions = new HashMap<Integer, Integer>();

    EMA impliedVolEMA;

    /* parameters */
    double alpha, xi, beta, beta_decay_rate;

    int we_fucked_up_trigger;

    /* permanent parameters */
    double min_beta = 0.00;
    double cur_beta;
    double last_vega_sign = 0.0;
    int cur_miss_count = 0;
    double d_vol_cap = 0.25;
    double max_beta_d_vol = 0.015;
    double edge_estimate = 0.04;

    @Override
    public void addVariables(IJobSetup setup) {
        setup.addVariable("Alpha", "Passiveness: Number of standard deviations in vega to buffer quote against", "double", "1.0");
        setup.addVariable("Xi", "Sensitivity to vega risk", "double", "1");
        setup.addVariable("Beta", "How much to add to IV when we fucked up", "double", "0.01");
        setup.addVariable("Beta Decay", "How much to decay/multiply consecutive beta additions", "double", "1.2");
        setup.addVariable("\"I'm Fucked\" Trigger", "How long to wait to accept the fact that we fucked up.", "int", "7");
    }


    @Override
    public void initializeAlgo(IDB dataBase, List<String> instruments) {

        /* retrieve parameters */
        alpha = getDoubleVar("Alpha");
        xi = getDoubleVar("Xi");
        impliedVolEMA = new EMA(0.99);
        beta = getDoubleVar("Beta");
        beta_decay_rate = getDoubleVar("Beta Decay");
        we_fucked_up_trigger = getIntVar("\"I'm Fucked\" Trigger");

        /* add initial vol to EMA */
        impliedVolEMA.average(initialVol);

        /* initialize position map */
        for(int strike : strikes){
            positions.put(strike, 0);
        }
    }

    /* side =  1 => we sold   */
    /* side = -1 => we bought */
    @Override
    public void newFill(int strike, int side, double price) {
        log("Quote Fill, price=" + price + ", strike=" + strike + ", direction=" + side);

        /* estimate the true price by discounting the average edge our fills receive */
        double truePrice = (side == -1) ? (price/(1 - edge_estimate)) : (price/(1 + edge_estimate));

        /* compute IV via bisection method */
        double lastVol = impliedVolatility(truePrice, strike);

        double d_vol = lastVol - impliedVolEMA.get();

        if(Math.abs(d_vol) > d_vol_cap){
            lastVol = impliedVolEMA.get() + d_vol_cap*Math.signum(d_vol);
        }


        impliedVolEMA.average(lastVol);


        /* update position */
        positions.put(strike, positions.get(strike) - side);

        cash += side*price;

        double vega = getTotalVegaRisk();

        cur_miss_count = 0;
        cur_beta = beta;
    }

    @Override
    public QuoteList getCurrentQuotes(){

        double totalVegaRisk = getTotalVegaRisk();

        log("PnL = " + getPnL());
        log("Vega = " + +getTotalVegaRisk());
        log("Vol = " + impliedVolEMA.get());

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

    @Override
    //TODO - update vol based on the fact that we know their order was higher/lower than our quote
    public void noBrokerFills() {

        double vega = getTotalVegaRisk();

        if(cur_miss_count >= we_fucked_up_trigger && cur_miss_count % 2 == 0) {
            double b = cur_miss_count * cur_beta / 10;
            cur_beta = Math.max(min_beta, cur_beta * beta_decay_rate);
            impliedVolEMA.average(impliedVolEMA.get() - 2*minAbs(vega * cur_beta, Math.signum(vega) * max_beta_d_vol));
        }

        if(-1 == last_vega_sign*vega){
            cur_beta = beta;
        }

        cur_miss_count++;
        last_vega_sign = Math.signum(vega);

    }

    @Override
    public void penaltyNotice(double amount) {
        log("Penalty received in the amount of " + amount + ".  Good one fucker.");
    }

    @Override
    public OptionsInterface getImplementation() {
        return this;
    }

    /* helper functions */
    /* price option by price = theoPrice * (1 +/- delta + omega) */
    private Quote getQuote(int strike, double vega){
        double vol = impliedVolEMA.get();
        double theoPrice = OptionsMathUtils.theoValue(strike, vol);
        double delta = volSD * alpha;
        double omega = vega * xi;
        double bidPrice = theoPrice * (1 - delta - Math.max(omega/500, omega));
        double askPrice = theoPrice * (1 + delta - Math.min(omega/500, omega));
        return new Quote(strike, bidPrice, askPrice);
    }

    public double getPnL(){
        return getPnL(impliedVolEMA.get());
    }

    public double getPnL(double vol){
        double assets = 0;

        for(int strike : strikes){
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
