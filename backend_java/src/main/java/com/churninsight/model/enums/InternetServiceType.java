
import com.fasterxml.jackson.annotation.JsonValue;

public enum InternetServiceType {
    DSL("DSL"),
    FIBER_OPTIC("Fiber optic"),
    NO("No");

    private final String value;

    InternetServiceType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }
}