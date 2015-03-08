package ill1;

import java.util.List;

import org.apache.commons.math3.analysis.UnivariateFunction;
import org.apache.commons.math3.analysis.solvers.BrentSolver;
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
    double currentBid = OptionsMathUtils.theoValue(100, 0.3)-1;
    double currentAsk = OptionsMathUtils.theoValue(100, 0.3)+1;

    final double r = 0.01;
    final double t = 1.0;
    final double s = 100.0;

    double lastVol = 0.3;

    final double strikes[] = {80, 90, 100, 110, 120};
    final int C80 = 0, C90 = 1, C100 = 2, C110 = 3, C120 = 4;  //TODO - use map to index instead

    double[] lastPrices = new double[10];


    @Override
    public void addVariables(IJobSetup setup) {
        setup.addVariable("Strategy", "Strategy to use", "string", "one");
    }

    @Override
    public void initializeAlgo(IDB dataBase, List<String> instruments) {
        // TODO Auto-generated method stub
        // blah
        String strategy = getStringVar("Strategy");
        if (strategy.contains("one")) {
            // do strategy one
        }
    }

    @Override
    public void newFill(int strike, int side, double price) {
        // TODO Auto-generated method stub
        log("My logic received a quote Fill, price=" + price + ", strike=" + strike + ", direction=" + side);
        int index = (int)((strike / 10.0) - 8);
        double factor = (side == 1) ? (1/0.95) : (1/1.05);  //TODO - factor should be our pricing factor, not always 5%
        lastPrices[index] = price * factor;
    }

    @Override
    public QuoteList getCurrentQuotes(){
        // TODO Auto-generated method stub
        log("My Case1 implementation received a request for current quotes");
        Quote quoteEighty = new Quote(80, currentBid,currentAsk);
        Quote quoteNinety = new Quote(90, currentBid,currentAsk);
        Quote quoteHundred = new Quote(100, currentBid,currentAsk);
        Quote quoteHundredTen = new Quote(110, currentBid,currentAsk);
        Quote quoteHundredTwenty = new Quote(120, currentBid,currentAsk);

        return new QuoteList(quoteEighty,quoteNinety,quoteHundred,quoteHundredTen,quoteHundredTwenty);
    }

    @Override
    //TODO - update vol based on the fact that we know their order was higher/lower than our quote
    public void noBrokerFills() {
        // TODO Auto-generated method stub
        log("No match against broker the broker orders...time to adjust some levers?");
    }

    @Override
    public void penaltyNotice(double amount) {
        // TODO Auto-generated method stub
        log("Penalty received in the amount of " + amount);
    }

    @Override
    public OptionsInterface getImplementation() {
        // TODO Auto-generated method stub
        return null;
    }

    /* helper functions */
    //TODO - maybe we should compute impliedVol as a weighted moving average, since we only get one hit per tick
    private double getAverageVolatility(){
        double sum = 0;
        sum += impliedVolatility(lastPrices[C80], 80);
        sum += impliedVolatility(lastPrices[C90], 90);
        sum += impliedVolatility(lastPrices[C100], 100);
        sum += impliedVolatility(lastPrices[C110], 110);
        sum += impliedVolatility(lastPrices[C120], 120);
        return sum / 5;
    }

    private void updateLastPrices() {

    }


    public double impliedVolatility(double price, double strike) {

        BrentSolver solver = new BrentSolver();
        UnivariateFunction f = new ImpliedVolFunction(price, strike);
        return solver.solve(10000, f, 0.0, 5.0, lastVol);
    }

    private static class ImpliedVolFunction implements UnivariateFunction {

        double price, strike;

        public ImpliedVolFunction(double price, double strike) {
            this.price = price;
            this.strike = strike;
        }

        public double value(double vol) {
            return price - OptionsMathUtils.theoValue(strike, vol);
        }

    }

}
