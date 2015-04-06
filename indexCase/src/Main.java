

import java.io.*;
import java.util.LinkedList;
import java.util.Queue;

import com.numericalmethod.suanshu.stats.test.timeseries.adf.AugmentedDickeyFuller;

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
