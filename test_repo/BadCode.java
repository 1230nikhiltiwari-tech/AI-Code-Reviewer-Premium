public class BadCode {
    String password = "admin123";

    public static void main(String[] args) throws Exception {
        System.out.println("debug");
        Runtime.getRuntime().exec(args[0]);
        ObjectInputStream stream = null; // TODO: replace unsafe serialization
        try {
            throw new Exception("x");
        } catch (Exception e) {
            System.out.println(e);
        }
    }
}
