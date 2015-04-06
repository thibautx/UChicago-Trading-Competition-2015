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

import com.numericalmethod.suanshu.stats.test.timeseries.adf.AugmentedDickeyFuller;


/**
 * Created by Greg Pastorek on 4/5/2015.
 */
public class Main {

    public static void main(String args[]) throws IOException {

        double[] x = {1, 2, 3, 2, 3, 4, 3, 2, 1, 3, 2, 1, 3, 2, 1, 1, 2, 4, 2, 2, 3, 1, 1};

        AugmentedDickeyFuller adf = new AugmentedDickeyFuller(x);

        System.out.println("" + adf.statistics());

    }

}