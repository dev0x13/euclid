import com.mongodb.BasicDBObject;
import com.mongodb.DBObject;

import java.util.Arrays;
import java.util.List;

class Point {
    double x = 0;
    double y = 0;
    double z = 0;

    private int coordTurn = 0;
    public void inc() {
        switch (coordTurn % 3) {
            case 0: this.x += 0.01; break;
            case 1: this.y += 0.01; break;
            case 2: this.z += 0.01; break;
        }
        coordTurn++;
    }
}

public class ExpGenerator {
    private double startTime = 0.0;
    private Point point;
    private int id;
    ExpGenerator(){
        startTime = 0.0;
        point = new Point();
    }

    public DBObject generateSample() {

        long expDeltaTime = (long)(Math.random() * 200);
        try {
            Thread.sleep(expDeltaTime);
        } catch (InterruptedException e){
            e.printStackTrace();
        }

        startTime += 0.001 * expDeltaTime;
        point.inc();

        List<Double> coords = Arrays.asList(point.x, point.y, point.z);

        DBObject expObj = new BasicDBObject("id", this.id++)
                .append("time", startTime)
                .append("coordinates", coords)
                .append("density", Math.random());

        return expObj;
    }
}
