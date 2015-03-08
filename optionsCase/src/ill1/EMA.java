package ill1;


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
