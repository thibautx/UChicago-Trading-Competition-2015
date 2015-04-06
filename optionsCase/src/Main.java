
import org.uchicago.options.OptionsHelpers.*;

import java.io.*;
import java.util.LinkedList;
import java.util.Queue;

import org.apache.commons.math3.stat.regression.SimpleRegression;

/**
 * Created by Greg Pastorek on 3/11/2015.
 */
public class Main {

    final static boolean USE_REAL_VOL = false;
    static double alpha = 1.0;
    static double xi = 2.0;
    static double ema_decay = 0.99;
    static double edge_estimate = 0.04;
    static double iota = 0.000;
    static double beta = 0.01;
    static double beta_decay = 1.2; //1.2
    static int hit_weight = 5;
    static int miss_streak_weight = 3;
    static int miss_count_trigger = 3;
    static int fucked_up_trigger = 7; //7

    static LinkedList<Double> vegaQueue = new LinkedList<Double>();

    public static void main(String args[]) throws IOException {

        double[] xxx = {1, 2, 3, 2, 3, 4, 3, 2, 1, 3, 2, 1, 3, 2, 1, 1, 2, 4, 2, 2, 3, 1, 1};

        AugmentedDickeyFuller adf = new AugmentedDickeyFuller(xxx);

        System.out.println("" + adf.statistics());

    }

    public double[] difference(double[] x) {

        double[] y = new double[x.length-1];

        for(int i=0; i < x.length-1; i++) {
            y[i] = x[i+1] - x[i];
        }

    }


    public double getAverage(double[] x) {
        double s = 0;
        for(double _x : x) {
            s += _x;
        }
        return s / (double)x.length;
    }


    public double myADF(double[] x) {

        double[] y = difference(x);
        double u = getAverage(x);

        double[] A = new double[y.length];
        double[] b = new double[y.length];

        for(int i = 0; i < y.length; i++) {
            A[i] = y[i] - u;
            b[i] = x[i];
        }

        SimpleRegression sr = new SimpleRegression();
        sr

    }

}
