
import org.uchicago.index.core.AbstractIndexCase;
import org.uchicago.index.core.IndexCase;

import com.optionscity.freeway.api.IDB;
import com.optionscity.freeway.api.IJobSetup;

import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;


public class IndexCaseILL1 extends AbstractIndexCase implements IndexCase {

    int round;

    double score = 0;

    double[] my_portfolioWeights;
    double[] trueWeights;

    int substitution_window = 10;

    double[][] correlation_matrix;
    double[]   lastUnderlyingPrices = new double[30];
    double[][] returns_history = new double[30][10000];

    LinkedList<Transfer> pendingTransfers = new LinkedList<Transfer>();
    HashMap<Integer, Substitution> currentSubstitutions = new HashMap<Integer, Substitution>();

    @Override
    public double[] updatePosition(int currentTime, double[] underlyingPrices, double indexValue) {


        for (Iterator<Transfer> it = pendingTransfers.iterator(); it.hasNext();) {
            Transfer t = it.next();
			
            if (--t.remaining < t.transactions) {
                my_portfolioWeights[t.substitute] += t.weight;
                my_portfolioWeights[t.security] -= t.weight;
                score -= (Math.exp(Math.abs(t.weight))-1) / 200;
            }

            if(my_portfolioWeights[t.security] < 10e-8){
                my_portfolioWeights[t.security] = 0;
            }
            if(my_portfolioWeights[t.substitute] < 10e-8){
                my_portfolioWeights[t.substitute] = 0;
            }

            if(t.remaining == 0){
                it.remove();
            }

        }

        return my_portfolioWeights;
    }



    @Override
    public void regulationAnnouncement(int currentTime, int timeTakeEffect, boolean[] tradables) {


		double[][] _correlation_matrix = correlation_matrix.clone()
	
        /* for each security */
        for(int sec = 0; sec < 30; sec++) {

            int substitute = sec;
            while(!tradables[substitute]) {
                _correlation_matrix[sec][substitute] = -100;
                substitute = /* TODO - findBestSubstitute(_correlation_matrix, sec); */
            }

            Substitution cur_sub = currentSubstitutions.get(sec);

            if(substitute != cur_sub.substitute) {
                int remaining = timeTakeEffect - currentTime;
                if(/* stock went from untradable to tradable in this announcement */) {
                    remaining++;
                }
                int transactions = (sec == substitute) ? 1 : remaining;
                double weight = trueWeights[sec] / transactions;
                Transfer t = new Transfer(cur_sub.substitute, substitute, remaining, transactions, weight);
                Substitution s = new Substitution(sec, substitute, t);
                pendingTransfers.add(t);
                currentSubstitutions.put(sec, s);
            }

        }


    }

    @Override
    public void initializeAlgo(IDB database) {

        /* initialize substitutions */
        for(int sec = 0; sec < 30; sec++) {
            currentSubstitutions.put(sec, new Substitution(sec, sec, null));
        }
    }


    public class Transfer {

        public int security;
        public int substitute;
        public int remaining;
        public int transactions;
        public double weight; //weight to transfer per tick

        public Transfer(int security_, int substitute_, int remaining_, int transactions_, double weight_) {
            security = security_;
            substitute = substitute_;
            remaining = remaining_;
            transactions = transactions_;
            weight = weight_;
        }
    }

    public class Substitution {

        public int security;
        public int substitute;
        private Transfer transfer;

        public Substitution(int security_, int substitute_, Transfer t) {
            security = security_;
            substitute = substitute_;
            transfer = t;
        }

        public Transfer getTransfer() {
            return transfer;
        }

    }


}
