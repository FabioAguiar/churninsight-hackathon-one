package com.churninsight.model.enums;
import com.fasterxml.jackson.annotation.JsonCreator;
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

    @JsonCreator
    public static PaymentMethodType fromValue(String text) {
        for (PaymentMethodType b : PaymentMethodType.values()) {
            if (String.valueOf(b.value).equals(text)) {
                return b;
            }
        }
        throw new IllegalArgumentException("Unexpected value '" + text + "'");
    }
}