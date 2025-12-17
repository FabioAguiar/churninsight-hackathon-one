
import com.fasterxml.jackson.annotation.JsonValue;

public enum PaymentMethodType {
    ELECTRONIC_CHECK("Electronic check"),
    BANK_TRANSFER("Bank transfer"),
    CREDIT_CARD("Credit card");

    private final String value;

    PaymentMethodType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }
}